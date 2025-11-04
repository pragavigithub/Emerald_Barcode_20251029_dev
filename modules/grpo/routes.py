"""
GRPO (Goods Receipt PO) Routes
All routes related to goods receipt against purchase orders
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from modules.grpo.models import GRPODocument, GRPOItem, GRPOSerialNumber, GRPOBatchNumber, GRPONonManagedItem
from models import User
from sap_integration import SAPIntegration
import logging
from datetime import datetime
import qrcode
import io
import base64
import json

grpo_bp = Blueprint('grpo', __name__, url_prefix='/grpo', template_folder='templates')

@grpo_bp.route('/')
@login_required
def index():
    """GRPO main page - list all GRPOs for current user"""
    if not current_user.has_permission('grpo'):
        flash('Access denied - GRPO permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    documents = GRPODocument.query.filter_by(user_id=current_user.id).order_by(GRPODocument.created_at.desc()).all()
    return render_template('grpo/grpo.html', documents=documents, per_page=10, search_term='', pagination=None)

@grpo_bp.route('/detail/<int:grpo_id>')
@login_required
def detail(grpo_id):
    """GRPO detail page"""
    grpo_doc = GRPODocument.query.get_or_404(grpo_id)
    
    # Check permissions
    if grpo_doc.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
        flash('Access denied - You can only view your own GRPOs', 'error')
        return redirect(url_for('grpo.index'))
    
    # Fetch PO items from SAP to display available items for receiving
    po_items = []
    sap = SAPIntegration()
    po_data = sap.get_purchase_order(grpo_doc.po_number)
    
    if po_data and 'DocumentLines' in po_data:
        all_po_items = po_data.get('DocumentLines', [])
        # Filter out closed line items - only show open items
        po_items = [
            item for item in all_po_items 
            if item.get('LineStatus') not in ['bost_Close', 'bost_Closed']
        ]
        logging.info(f"📦 Fetched {len(all_po_items)} total items for PO {grpo_doc.po_number}, {len(po_items)} open items (filtered out {len(all_po_items) - len(po_items)} closed items)")
    else:
        logging.warning(f"⚠️ Could not fetch PO items for {grpo_doc.po_number}")
    
    return render_template('grpo/grpo_detail.html', grpo_doc=grpo_doc, po_items=po_items)

@grpo_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new GRPO"""
    if not current_user.has_permission('grpo'):
        flash('Access denied - GRPO permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        po_number = request.form.get('po_number')
        
        if not po_number:
            flash('PO number is required', 'error')
            return redirect(url_for('grpo.create'))
        
        # Check if GRPO already exists for this PO (only prevent if not posted to SAP)
        existing_grpo = GRPODocument.query.filter_by(po_number=po_number, user_id=current_user.id).first()
        if existing_grpo and existing_grpo.status != 'posted' and not existing_grpo.sap_document_number:
            flash(f'GRPO already exists for PO {po_number} and is not yet posted. Please complete the existing GRPO first.', 'warning')
            return redirect(url_for('grpo.detail', grpo_id=existing_grpo.id))
        elif existing_grpo and existing_grpo.status == 'posted':
            logging.info(f"📝 Creating new GRPO for PO {po_number} - Previous GRPO already posted to SAP (DocNum: {existing_grpo.sap_document_number})")
        
        # Fetch PO details from SAP to get supplier information
        sap = SAPIntegration()
        po_data = sap.get_purchase_order(po_number)
        
        supplier_code = None
        supplier_name = None
        
        if po_data:
            supplier_code = po_data.get('CardCode')
            supplier_name = po_data.get('CardName')
            logging.info(f"📋 PO {po_number} - Supplier: {supplier_name} ({supplier_code})")
        else:
            logging.warning(f"⚠️ Could not fetch PO details from SAP for PO {po_number}")
        
        # Create new GRPO without doc_number first (will be generated after commit)
        grpo = GRPODocument(
            po_number=po_number,
            supplier_code=supplier_code,
            supplier_name=supplier_name,
            user_id=current_user.id,
            status='draft'
        )
        
        db.session.add(grpo)
        db.session.flush()  # Flush to get the ID without committing
        
        # Generate document number using the auto-incremented ID for guaranteed uniqueness
        # Format: GRN/YYYYMMDD/NNNNNNNNNN
        today_str = grpo.created_at.strftime('%Y%m%d')
        grpo.doc_number = f"GRN/{today_str}/{str(grpo.id).zfill(10)}"
        
        db.session.commit()
        
        logging.info(f"✅ GRPO created for PO {po_number} by user {current_user.username}")
        flash(f'GRPO created for PO {po_number}', 'success')
        return redirect(url_for('grpo.detail', grpo_id=grpo.id))
    
    return render_template('grpo/create_grpo.html')

@grpo_bp.route('/<int:grpo_id>/submit', methods=['POST'])
@login_required
def submit(grpo_id):
    """Submit GRPO for QC approval"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check permissions
        if grpo.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if grpo.status != 'draft':
            return jsonify({'success': False, 'error': 'Only draft GRPOs can be submitted'}), 400
        
        if not grpo.items:
            return jsonify({'success': False, 'error': 'Cannot submit GRPO without items'}), 400
        
        # Update status
        grpo.status = 'submitted'
        grpo.updated_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"📤 GRPO {grpo_id} submitted for QC approval")
        return jsonify({
            'success': True,
            'message': 'GRPO submitted for QC approval',
            'status': 'submitted'
        })
        
    except Exception as e:
        logging.error(f"Error submitting GRPO: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/<int:grpo_id>/approve', methods=['POST'])
@login_required
def approve(grpo_id):
    """QC approve GRPO and post to SAP B1"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'QC permissions required'}), 403
        
        if grpo.status != 'submitted':
            return jsonify({'success': False, 'error': 'Only submitted GRPOs can be approved'}), 400
        
        # Get QC notes
        qc_notes = ''
        if request.form:
            qc_notes = request.form.get('qc_notes', '')
        elif request.json:
            qc_notes = request.json.get('qc_notes', '')
        
        # Mark items as approved
        for item in grpo.items:
            item.qc_status = 'approved'
        
        # Update GRPO status
        grpo.status = 'qc_approved'
        grpo.qc_approver_id = current_user.id
        grpo.qc_approved_at = datetime.utcnow()
        grpo.qc_notes = qc_notes
        
        # Initialize SAP integration and post to SAP B1
        from sap_integration import SAPIntegration
        sap = SAPIntegration()
        
        # Log the posting attempt
        logging.info(f"🚀 Attempting to post GRPO {grpo_id} to SAP B1...")
        logging.info(f"GRPO Items: {len(grpo.items)} items, QC Approved: {len([i for i in grpo.items if i.qc_status == 'approved'])}")
        
        # Post GRPO to SAP B1 as Purchase Delivery Note
        sap_result = sap.post_grpo_to_sap(grpo)
        
        # Log the result
        logging.info(f"📡 SAP B1 posting result: {sap_result}")
        
        if sap_result.get('success'):
            grpo.sap_document_number = sap_result.get('sap_document_number')
            grpo.status = 'posted'
            db.session.commit()
            
            logging.info(f"✅ GRPO {grpo_id} QC approved and posted to SAP B1 as {grpo.sap_document_number}")
            return jsonify({
                'success': True,
                'message': f'GRPO approved and posted to SAP B1 as {grpo.sap_document_number}',
                'sap_document_number': grpo.sap_document_number
            })
        else:
            # If SAP posting fails, still mark as QC approved but not posted
            db.session.commit()
            error_msg = sap_result.get('error', 'Unknown SAP error')
            
            logging.warning(f"⚠️ GRPO {grpo_id} QC approved but SAP posting failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': f'GRPO approved but SAP posting failed: {error_msg}',
                'status': 'qc_approved'
            })
        
    except Exception as e:
        logging.error(f"Error approving GRPO: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/<int:grpo_id>/reject', methods=['POST'])
@login_required
def reject(grpo_id):
    """QC reject GRPO"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check QC permissions
        if not current_user.has_permission('qc_dashboard') and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'QC permissions required'}), 403
        
        if grpo.status != 'submitted':
            return jsonify({'success': False, 'error': 'Only submitted GRPOs can be rejected'}), 400
        
        # Get rejection reason
        qc_notes = ''
        if request.form:
            qc_notes = request.form.get('qc_notes', '')
        elif request.json:
            qc_notes = request.json.get('qc_notes', '')
        
        if not qc_notes:
            return jsonify({'success': False, 'error': 'Rejection reason is required'}), 400
        
        # Mark items as rejected
        for item in grpo.items:
            item.qc_status = 'rejected'
        
        # Update GRPO status
        grpo.status = 'rejected'
        grpo.qc_approver_id = current_user.id
        grpo.qc_approved_at = datetime.utcnow()
        grpo.qc_notes = qc_notes
        
        db.session.commit()
        
        logging.info(f"❌ GRPO {grpo_id} rejected by QC")
        return jsonify({
            'success': True,
            'message': 'GRPO rejected by QC',
            'status': 'rejected'
        })
        
    except Exception as e:
        logging.error(f"Error rejecting GRPO: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/<int:grpo_id>/add_item', methods=['POST'])
@login_required
def add_grpo_item(grpo_id):
    """Add item to GRPO with SAP validation and batch/serial number support"""
    try:
        grpo = GRPODocument.query.get_or_404(grpo_id)
        
        # Check permissions
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            flash('Access denied - You can only modify your own GRPOs', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        if grpo.status != 'draft':
            flash('Cannot add items to non-draft GRPO', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # Get form data
        item_code = request.form.get('item_code')
        item_name = request.form.get('item_name')
        quantity = float(request.form.get('quantity', 0))
        unit_of_measure = request.form.get('unit_of_measure')
        warehouse_code = request.form.get('warehouse_code')
        bin_location = request.form.get('bin_location')
        batch_number = request.form.get('batch_number')
        expiry_date = request.form.get('expiry_date')
        serial_numbers_json = request.form.get('serial_numbers_json', '')
        batch_numbers_json = request.form.get('batch_numbers_json', '')
        
        # Safely parse number_of_bags with validation
        try:
            number_of_bags_str = (request.form.get('number_of_bags') or '1').strip()
            number_of_bags = int(number_of_bags_str) if number_of_bags_str else 1
            if number_of_bags < 1:
                number_of_bags = 1
        except (ValueError, TypeError, AttributeError):
            number_of_bags = 1
        
        if not all([item_code, item_name, quantity > 0]):
            flash('Item Code, Item Name, and Quantity are required', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **DUPLICATE PREVENTION LOGIC**
        existing_item = GRPOItem.query.filter_by(
            grpo_id=grpo_id,
            item_code=item_code
        ).first()
        
        if existing_item:
            flash(f'Item {item_code} has already been added to this GRPO. Each item can only be received once per GRPO to avoid duplication.', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **SAP VALIDATION - Determine item management type**
        from sap_integration import SAPIntegration
        sap = SAPIntegration()
        validation_result = sap.validate_item_code(item_code)
        
        is_batch_managed = validation_result.get('batch_required', False)
        is_serial_managed = validation_result.get('serial_required', False)
        
        logging.info(f"🔍 Item {item_code} validation: Batch={is_batch_managed}, Serial={is_serial_managed}")
        
        # **VALIDATION: Enforce serial/batch data for managed items**
        if is_serial_managed and not serial_numbers_json:
            flash(f'Item {item_code} is serial managed - serial numbers are required', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        if is_batch_managed and not batch_numbers_json:
            flash(f'Item {item_code} is batch managed - batch numbers are required', 'error')
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # Parse expiry date if provided
        expiry_date_obj = None
        if expiry_date:
            try:
                expiry_date_obj = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid expiry date format. Use YYYY-MM-DD', 'error')
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # Create new GRPO item
        grpo_item = GRPOItem(
            grpo_id=grpo_id,
            item_code=item_code,
            item_name=item_name,
            quantity=quantity,
            received_quantity=quantity,
            unit_of_measure=unit_of_measure,
            warehouse_code=warehouse_code,
            bin_location=bin_location,
            batch_number=batch_number,
            expiry_date=expiry_date_obj,
            qc_status='pending'
        )
        
        db.session.add(grpo_item)
        db.session.flush()
        
        # **SERIAL NUMBER HANDLING**
        if is_serial_managed and serial_numbers_json:
            try:
                serial_numbers = json.loads(serial_numbers_json)
                
                # Validate quantity matches serial entries
                if len(serial_numbers) != int(quantity):
                    flash(f'Serial managed item requires {int(quantity)} serial numbers, but {len(serial_numbers)} provided', 'error')
                    db.session.rollback()
                    return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                
                # Calculate qty per pack based on number of serials per bag
                # For serials, we distribute the serials across bags, so qty_per_pack is serials per bag
                total_serials = len(serial_numbers)
                
                # Validate that number_of_bags doesn't exceed total serials
                if number_of_bags > total_serials:
                    flash(f'Number of bags ({number_of_bags}) cannot exceed number of serial items ({total_serials})', 'error')
                    db.session.rollback()
                    return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                
                # Validate that serials can be evenly divided into bags (integer pack sizes only)
                if total_serials % number_of_bags != 0:
                    flash(f'Number of serials ({total_serials}) must be evenly divisible by number of bags ({number_of_bags}). Each bag must contain the same integer number of serials.', 'error')
                    db.session.rollback()
                    return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                
                qty_per_pack = total_serials / number_of_bags
                no_of_packs = number_of_bags
                
                # Create serial number records with automatic barcode generation
                for idx, serial_data in enumerate(serial_numbers):
                    # Generate unique GRN number for this serial
                    grn_number = generate_unique_grn_number(grpo, idx + 1)
                    
                    serial = GRPOSerialNumber(
                        grpo_item_id=grpo_item.id,
                        manufacturer_serial_number=serial_data.get('manufacturer_serial_number', ''),
                        internal_serial_number=serial_data.get('internal_serial_number'),
                        expiry_date=datetime.strptime(serial_data['expiry_date'], '%Y-%m-%d').date() if serial_data.get('expiry_date') else None,
                        manufacture_date=datetime.strptime(serial_data['manufacture_date'], '%Y-%m-%d').date() if serial_data.get('manufacture_date') else None,
                        notes=serial_data.get('notes', ''),
                        quantity=1.0,
                        base_line_number=idx,
                        grn_number=grn_number,
                        qty_per_pack=qty_per_pack,
                        no_of_packs=no_of_packs
                    )
                    db.session.add(serial)
                    logging.info(f"✅ Created serial {serial_data.get('internal_serial_number')} with GRN {grn_number}")
                
                logging.info(f"✅ Added {len(serial_numbers)} serial numbers for item {item_code} (Qty per pack: {qty_per_pack}, No of packs: {no_of_packs})")
                
            except json.JSONDecodeError:
                flash('Invalid serial numbers data format', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
            except Exception as e:
                flash(f'Error processing serial numbers: {str(e)}', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **BATCH NUMBER HANDLING**
        if is_batch_managed and batch_numbers_json:
            try:
                batch_numbers = json.loads(batch_numbers_json)
                
                # Validate total batch quantity matches item quantity
                total_batch_qty = sum(float(b.get('quantity', 0)) for b in batch_numbers)
                if abs(total_batch_qty - quantity) > 0.001:
                    flash(f'Total batch quantity ({total_batch_qty}) must equal item quantity ({quantity})', 'error')
                    db.session.rollback()
                    return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                
                # Create batch number records with automatic barcode generation
                for idx, batch_data in enumerate(batch_numbers):
                    batch_qty = float(batch_data.get('quantity', 0))
                    
                    # Validate that batch quantity can be evenly divided into bags
                    if batch_qty % number_of_bags != 0:
                        flash(f'Batch quantity ({batch_qty}) for batch {batch_data.get("batch_number")} must be evenly divisible by number of bags ({number_of_bags}). Each bag must contain the same integer quantity.', 'error')
                        db.session.rollback()
                        return redirect(url_for('grpo.detail', grpo_id=grpo_id))
                    
                    # Calculate qty per pack for this batch
                    qty_per_pack = batch_qty / number_of_bags if number_of_bags > 0 else batch_qty
                    no_of_packs = number_of_bags
                    
                    # Generate unique GRN number for this batch
                    grn_number = generate_unique_grn_number(grpo, idx + 1)
                    
                    batch = GRPOBatchNumber(
                        grpo_item_id=grpo_item.id,
                        batch_number=batch_data.get('batch_number'),
                        quantity=batch_qty,
                        manufacturer_serial_number=batch_data.get('manufacturer_serial_number', ''),
                        internal_serial_number=batch_data.get('internal_serial_number', ''),
                        expiry_date=datetime.strptime(batch_data['expiry_date'], '%Y-%m-%d').date() if batch_data.get('expiry_date') else None,
                        base_line_number=idx,
                        grn_number=grn_number,
                        qty_per_pack=qty_per_pack,
                        no_of_packs=no_of_packs
                    )
                    db.session.add(batch)
                    logging.info(f"✅ Created batch {batch_data.get('batch_number')} with GRN {grn_number} (Qty per pack: {qty_per_pack}, No of packs: {no_of_packs})")
                
                logging.info(f"✅ Added {len(batch_numbers)} batch numbers for item {item_code}")
                
            except json.JSONDecodeError:
                flash('Invalid batch numbers data format', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
            except Exception as e:
                flash(f'Error processing batch numbers: {str(e)}', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        # **NON-MANAGED ITEM HANDLING** (when both BatchNum='N' and SerialNum='N')
        if not is_batch_managed and not is_serial_managed:
            has_serial_data = False
            has_batch_data = False
            
            if serial_numbers_json:
                try:
                    parsed_serials = json.loads(serial_numbers_json)
                    has_serial_data = isinstance(parsed_serials, list) and len(parsed_serials) > 0
                except (json.JSONDecodeError, TypeError):
                    pass
            
            if batch_numbers_json:
                try:
                    parsed_batches = json.loads(batch_numbers_json)
                    has_batch_data = isinstance(parsed_batches, list) and len(parsed_batches) > 0
                except (json.JSONDecodeError, TypeError):
                    pass
            
            if has_serial_data or has_batch_data:
                logging.error(f"❌ CRITICAL: Attempted to create non-managed items for {item_code} but serial/batch data was provided! is_batch_managed={is_batch_managed}, is_serial_managed={is_serial_managed}, has_serial_data={has_serial_data}, has_batch_data={has_batch_data}")
                flash(f'Data inconsistency: Item {item_code} has batch/serial data but SAP validation indicates it is not managed. Please check SAP item master data.', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
            
            try:
                qty_per_pack = quantity / number_of_bags if number_of_bags > 0 else quantity
                no_of_packs = number_of_bags
                
                for idx in range(number_of_bags):
                    grn_number = generate_unique_grn_number(grpo, idx + 1)
                    
                    non_managed_item = GRPONonManagedItem(
                        grpo_item_id=grpo_item.id,
                        quantity=qty_per_pack,
                        base_line_number=idx,
                        expiry_date=expiry_date_obj,
                        admin_date=datetime.now().date(),
                        grn_number=grn_number,
                        qty_per_pack=qty_per_pack,
                        no_of_packs=no_of_packs,
                        pack_number=idx + 1
                    )
                    db.session.add(non_managed_item)
                    logging.info(f"✅ Created non-managed item pack {idx + 1} of {no_of_packs} with GRN {grn_number} (Qty per pack: {qty_per_pack})")
                
                logging.info(f"✅ Added non-managed item {item_code} with {no_of_packs} packs (Qty per pack: {qty_per_pack})")
                
            except Exception as e:
                flash(f'Error processing non-managed item: {str(e)}', 'error')
                db.session.rollback()
                return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        elif is_batch_managed and not batch_numbers_json:
            logging.error(f"❌ Batch-managed item {item_code} added without batch data")
            flash(f'Item {item_code} is batch managed but no batch numbers were provided', 'error')
            db.session.rollback()
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        elif is_serial_managed and not serial_numbers_json:
            logging.error(f"❌ Serial-managed item {item_code} added without serial data")
            flash(f'Item {item_code} is serial managed but no serial numbers were provided', 'error')
            db.session.rollback()
            return redirect(url_for('grpo.detail', grpo_id=grpo_id))
        
        db.session.commit()
        
        logging.info(f"✅ Item {item_code} added to GRPO {grpo_id} (Batch: {is_batch_managed}, Serial: {is_serial_managed})")
        flash(f'Item {item_code} successfully added to GRPO', 'success')
        
    except Exception as e:
        logging.error(f"Error adding item to GRPO: {str(e)}")
        flash(f'Error adding item: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('grpo.detail', grpo_id=grpo_id))

@grpo_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_grpo_item(item_id):
    """Delete GRPO item"""
    try:
        item = GRPOItem.query.get_or_404(item_id)
        grpo = item.grpo_document
        
        # Check permissions
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        if grpo.status != 'draft':
            return jsonify({'success': False, 'error': 'Cannot delete items from non-draft GRPO'}), 400
        
        grpo_id = grpo.id
        item_code = item.item_code
        
        db.session.delete(item)
        db.session.commit()
        
        logging.info(f"🗑️ Item {item_code} deleted from GRPO {grpo_id}")
        return jsonify({'success': True, 'message': f'Item {item_code} deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting GRPO item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/validate-item/<string:item_code>', methods=['GET'])
@login_required
def validate_item_code(item_code):
    """Validate ItemCode and return batch/serial requirements"""
    try:
        from sap_integration import SAPIntegration
        
        sap = SAPIntegration()
        validation_result = sap.validate_item_code(item_code)
        
        logging.info(f"🔍 ItemCode validation for {item_code}: {validation_result}")
        
        return jsonify(validation_result)
        
    except Exception as e:
        logging.error(f"Error validating ItemCode {item_code}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'item_code': item_code,
            'batch_required': False,
            'serial_required': False,
            'manage_method': 'N'
        }), 500

@grpo_bp.route('/items/<int:item_id>/serial-numbers', methods=['GET'])
@login_required
def get_serial_numbers(item_id):
    """Get all serial numbers for a GRPO item"""
    try:
        item = GRPOItem.query.get_or_404(item_id)
        grpo = item.grpo_document
        
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        serial_numbers = []
        for serial in item.serial_numbers:
            serial_numbers.append({
                'id': serial.id,
                'internal_serial_number': serial.internal_serial_number,
                'manufacturer_serial_number': serial.manufacturer_serial_number,
                'expiry_date': serial.expiry_date.strftime('%Y-%m-%d') if serial.expiry_date else None,
                'manufacture_date': serial.manufacture_date.strftime('%Y-%m-%d') if serial.manufacture_date else None,
                'notes': serial.notes,
                'qty_per_pack': float(serial.qty_per_pack) if serial.qty_per_pack else 1.0,
                'no_of_packs': serial.no_of_packs if serial.no_of_packs else 1
            })
        
        return jsonify({
            'success': True,
            'serial_numbers': serial_numbers,
            'count': len(serial_numbers),
            'grpo_details': {
                'po_number': grpo.po_number,
                'grn_date': grpo.created_at.strftime('%Y-%m-%d'),
                'doc_number': grpo.doc_number or f'GRN/{grpo.id}',
                'item_code': item.item_code,
                'item_name': item.item_name,
                'received_quantity': float(item.quantity)
            }
        })
        
    except Exception as e:
        logging.error(f"Error fetching serial numbers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/items/<int:item_id>/batch-numbers', methods=['GET'])
@login_required
def get_batch_numbers(item_id):
    """Get all batch numbers for a GRPO item with GRPO document details"""
    try:
        item = GRPOItem.query.get_or_404(item_id)
        grpo = item.grpo_document
        
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        batch_numbers = []
        for batch in item.batch_numbers:
            batch_numbers.append({
                'id': batch.id,
                'batch_number': batch.batch_number,
                'quantity': float(batch.quantity),
                'expiry_date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else None,
                'manufacturer_serial_number': batch.manufacturer_serial_number,
                'internal_serial_number': batch.internal_serial_number,
                'qty_per_pack': float(batch.qty_per_pack) if batch.qty_per_pack else float(batch.quantity),
                'no_of_packs': batch.no_of_packs if batch.no_of_packs else 1
            })
        
        return jsonify({
            'success': True,
            'batch_numbers': batch_numbers,
            'count': len(batch_numbers),
            'grpo_details': {
                'po_number': grpo.po_number,
                'grn_date': grpo.created_at.strftime('%Y-%m-%d'),
                'doc_number': grpo.doc_number or f'GRN/{grpo.id}',
                'item_code': item.item_code,
                'item_name': item.item_name,
                'received_quantity': float(item.quantity)
            }
        })
        
    except Exception as e:
        logging.error(f"Error fetching batch numbers: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/items/<int:item_id>/non-managed-items', methods=['GET'])
@login_required
def get_non_managed_items(item_id):
    """Get all non-managed item records for a GRPO item with GRPO document details"""
    try:
        logging.info(f"📦 Fetching non-managed items for item_id={item_id}")
        item = GRPOItem.query.get_or_404(item_id)
        grpo = item.grpo_document
        
        logging.info(f"📦 Item found: {item.item_code}, GRPO ID: {grpo.id}, User ID: {grpo.user_id}")
        
        if grpo.user_id != current_user.id and current_user.role not in ['admin', 'manager', 'qc']:
            logging.warning(f"⚠️ Access denied for user {current_user.id} to GRPO {grpo.id}")
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        non_managed_items_query = item.non_managed_items
        logging.info(f"📦 Found {len(non_managed_items_query) if non_managed_items_query else 0} non-managed item records")
        
        if not non_managed_items_query or len(non_managed_items_query) == 0:
            logging.warning(f"⚠️ No non-managed item records found for item_id={item_id}. Item might be serial/batch managed or records not created during item addition.")
            return jsonify({
                'success': False,
                'error': 'No non-managed item records found. This item may be serial or batch managed, or the item was not properly saved. Please check the item type and try adding it again.',
                'hint': 'Check that this is a non-serial, non-batch managed item'
            }), 404
        
        non_managed_items = []
        for nm_item in non_managed_items_query:
            non_managed_items.append({
                'id': nm_item.id,
                'grn_number': nm_item.grn_number,
                'quantity': nm_item.quantity,
                'expiry_date': nm_item.expiry_date ,
                'qty_per_pack': float(nm_item.qty_per_pack) if nm_item.qty_per_pack else float(nm_item.quantity),
                'no_of_packs': nm_item.no_of_packs if nm_item.no_of_packs else 1,
                'pack_number': nm_item.pack_number,
                'admin_date': nm_item.admin_date
            })
        #nm_item.admin_date.strftime('%Y-%m-%d') if
        logging.info(f"✅ Successfully returning {len(non_managed_items)} non-managed items")
        return jsonify({
            'success': True,
            'non_managed_items': non_managed_items,
            'count': len(non_managed_items),
            'grpo_details': {
                'po_number': grpo.po_number,
                'grn_date': grpo.created_at.strftime('%Y-%m-%d'),
                'doc_number': grpo.doc_number or f'GRN/{grpo.id}',
                'item_code': item.item_code,
                'item_name': item.item_name,
                'received_quantity': float(item.quantity)
            }
        })
        
    except Exception as e:
        import traceback
        logging.error(f"❌ Error fetching non-managed items for item_id={item_id}: {str(e)}")
        logging.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_barcode(data):
    """Generate QR code barcode and return base64 encoded image"""
    try:
        if not data or len(str(data).strip()) == 0:
            logging.warning("⚠️ Empty data provided for barcode generation")
            return None
        
        # Limit data length to prevent overly complex QR codes
        data_str = str(data).strip()
        if len(data_str) > 500:
            logging.warning(f"⚠️ Barcode data too long ({len(data_str)} chars), truncating to 500")
            data_str = data_str[:500]
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data_str)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Limit base64 size (typical QR code should be < 10KB)
        if len(img_base64) > 100000:  # ~75KB limit
            logging.warning(f"⚠️ Generated barcode too large ({len(img_base64)} bytes), skipping")
            return None
        
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logging.error(f"❌ Error generating barcode for data '{str(data)[:50]}...': {str(e)}")
        return None

def generate_unique_grn_number(grpo_document, sequence_number):
    """Generate unique GRN number for each serial/batch label
    Format: GRN/YY/NNNNNNNNNN where YY is 2-digit year and N is sequence
    """
    year_suffix = grpo_document.created_at.strftime('%y')
    base_id = str(grpo_document.id).zfill(8)
    seq = str(sequence_number).zfill(4)
    return f"GRN/{year_suffix}/{base_id}{seq}"

@grpo_bp.route('/items/<int:item_id>/serial-numbers', methods=['GET', 'POST'])
@login_required
def manage_serial_numbers(item_id):
    """Get or add serial numbers for a GRPO item"""
    item = GRPOItem.query.get_or_404(item_id)
    
    # Check permissions
    if item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        # Return existing serial numbers
        serials = [{
            'id': sn.id,
            'manufacturer_serial_number': sn.manufacturer_serial_number,
            'internal_serial_number': sn.internal_serial_number,
            'expiry_date': sn.expiry_date.isoformat() if sn.expiry_date else None,
            'manufacture_date': sn.manufacture_date.isoformat() if sn.manufacture_date else None,
            'notes': sn.notes,
            'barcode': sn.barcode,
            'quantity': float(sn.quantity),
            'base_line_number': sn.base_line_number
        } for sn in item.serial_numbers]
        
        # Include GRPO document details for QR labels
        grpo = item.grpo_document
        grpo_details = {
            'po_number': grpo.po_number or 'N/A',
            'grn_date': grpo.created_at.strftime('%Y-%m-%d') if grpo.created_at else 'N/A',
            'doc_number': grpo.doc_number or 'N/A'
        }
        
        return jsonify({
            'success': True, 
            'serial_numbers': serials,
            'grpo_details': grpo_details
        })
    
    elif request.method == 'POST':
        # Add new serial number
        try:
            data = request.json
            
            # Check if internal serial number already exists
            existing = GRPOSerialNumber.query.filter_by(
                internal_serial_number=data['internal_serial_number']
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': f"Serial number '{data['internal_serial_number']}' already exists"
                }), 400
            
            # Generate barcode
            internal_sn = data.get('internal_serial_number', '').strip()
            if not internal_sn:
                return jsonify({
                    'success': False,
                    'error': 'Internal serial number is required'
                }), 400
            
            barcode_data = f"SN:{internal_sn}"
            try:
                barcode = generate_barcode(barcode_data)
                if not barcode:
                    logging.warning(f"⚠️ Barcode generation failed for serial: {internal_sn}, continuing without barcode")
                    barcode = None
            except Exception as barcode_error:
                logging.error(f"❌ Barcode generation error for {internal_sn}: {str(barcode_error)}")
                barcode = None
            
            # Create serial number entry
            serial = GRPOSerialNumber(
                grpo_item_id=item_id,
                manufacturer_serial_number=data.get('manufacturer_serial_number', '').strip() or None,
                internal_serial_number=internal_sn,
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
                manufacture_date=datetime.strptime(data['manufacture_date'], '%Y-%m-%d').date() if data.get('manufacture_date') else None,
                notes=data.get('notes', '').strip() or None,
                barcode=barcode,
                quantity=float(data.get('quantity', 1.0)),
                base_line_number=int(data.get('base_line_number', 0))
            )
            
            db.session.add(serial)
            db.session.commit()
            
            logging.info(f"✅ Serial number {internal_sn} added to item {item_id}{' (no barcode)' if not barcode else ''}")
            
            return jsonify({
                'success': True,
                'serial_number': {
                    'id': serial.id,
                    'manufacturer_serial_number': serial.manufacturer_serial_number,
                    'internal_serial_number': serial.internal_serial_number,
                    'expiry_date': serial.expiry_date.isoformat() if serial.expiry_date else None,
                    'manufacture_date': serial.manufacture_date.isoformat() if serial.manufacture_date else None,
                    'notes': serial.notes,
                    'barcode': serial.barcode,
                    'quantity': float(serial.quantity),
                    'base_line_number': serial.base_line_number
                }
            })
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding serial number: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/serial-numbers/<int:serial_id>', methods=['DELETE'])
@login_required
def delete_serial_number(serial_id):
    """Delete a serial number"""
    try:
        serial = GRPOSerialNumber.query.get_or_404(serial_id)
        
        # Check permissions
        if serial.grpo_item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        db.session.delete(serial)
        db.session.commit()
        
        logging.info(f"🗑️ Serial number {serial.internal_serial_number} deleted")
        return jsonify({'success': True, 'message': 'Serial number deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting serial number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/items/<int:item_id>/batch-numbers', methods=['GET', 'POST'])
@login_required
def manage_batch_numbers(item_id):
    """Get or add batch numbers for a GRPO item"""
    item = GRPOItem.query.get_or_404(item_id)
    
    # Check permissions
    if item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    if request.method == 'GET':
        # Return existing batch numbers
        batches = [{
            'id': bn.id,
            'batch_number': bn.batch_number,
            'quantity': float(bn.quantity),
            'base_line_number': bn.base_line_number,
            'manufacturer_serial_number': bn.manufacturer_serial_number,
            'internal_serial_number': bn.internal_serial_number,
            'expiry_date': bn.expiry_date.isoformat() if bn.expiry_date else None,
            'barcode': bn.barcode
        } for bn in item.batch_numbers]
        
        return jsonify({'success': True, 'batch_numbers': batches})
    
    elif request.method == 'POST':
        # Add new batch number
        try:
            data = request.json
            
            # Validate batch number
            batch_num = data.get('batch_number', '').strip()
            if not batch_num:
                return jsonify({
                    'success': False,
                    'error': 'Batch number is required'
                }), 400
            
            quantity = float(data.get('quantity', 0))
            if quantity <= 0:
                return jsonify({
                    'success': False,
                    'error': 'Quantity must be greater than 0'
                }), 400
            
            # Generate barcode
            barcode_data = f"BATCH:{batch_num}"
            try:
                barcode = generate_barcode(barcode_data)
                if not barcode:
                    logging.warning(f"⚠️ Barcode generation failed for batch: {batch_num}, continuing without barcode")
                    barcode = None
            except Exception as barcode_error:
                logging.error(f"❌ Barcode generation error for batch {batch_num}: {str(barcode_error)}")
                barcode = None
            
            # Create batch number entry
            batch = GRPOBatchNumber(
                grpo_item_id=item_id,
                batch_number=batch_num,
                quantity=quantity,
                base_line_number=int(data.get('base_line_number', 0)),
                manufacturer_serial_number=data.get('manufacturer_serial_number', '').strip() or None,
                internal_serial_number=data.get('internal_serial_number', '').strip() or None,
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
                barcode=barcode
            )
            
            db.session.add(batch)
            db.session.commit()
            
            logging.info(f"✅ Batch number {batch_num} (qty: {quantity}) added to item {item_id}{' (no barcode)' if not barcode else ''}")
            
            return jsonify({
                'success': True,
                'batch_number': {
                    'id': batch.id,
                    'batch_number': batch.batch_number,
                    'quantity': float(batch.quantity),
                    'base_line_number': batch.base_line_number,
                    'manufacturer_serial_number': batch.manufacturer_serial_number,
                    'internal_serial_number': batch.internal_serial_number,
                    'expiry_date': batch.expiry_date.isoformat() if batch.expiry_date else None,
                    'barcode': batch.barcode
                }
            })
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding batch number: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/batch-numbers/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch_number(batch_id):
    """Delete a batch number"""
    try:
        batch = GRPOBatchNumber.query.get_or_404(batch_id)
        
        # Check permissions
        if batch.grpo_item.grpo_document.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        db.session.delete(batch)
        db.session.commit()
        
        logging.info(f"🗑️ Batch number {batch.batch_number} deleted")
        return jsonify({'success': True, 'message': 'Batch number deleted'})
        
    except Exception as e:
        logging.error(f"Error deleting batch number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/validate-serial/<string:serial_number>', methods=['GET'])
@login_required
def validate_serial_unique(serial_number):
    """Check if serial number is unique"""
    try:
        existing = GRPOSerialNumber.query.filter_by(
            internal_serial_number=serial_number
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'unique': False,
                'message': f"Serial number '{serial_number}' already exists"
            })
        else:
            return jsonify({
                'success': True,
                'unique': True,
                'message': f"Serial number '{serial_number}' is available"
            })
            
    except Exception as e:
        logging.error(f"Error validating serial number: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grpo_bp.route('/api/generate-barcode-labels', methods=['POST'])
@login_required
def generate_barcode_labels_api():
    """
    API endpoint to generate QR code labels for GRPO items (Serial, Batch, and Non-managed)
    Accepts: grpo_id, item_id, label_type ('serial', 'batch', or 'regular')
    Returns: JSON with label data including all requested fields
    """
    try:
        data = request.get_json()
        
        grpo_id = data.get('grpo_id')
        item_id = data.get('item_id')
        label_type = data.get('label_type', 'batch')  # 'serial', 'batch', or 'regular'
        
        if not all([grpo_id, item_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: grpo_id, item_id'
            }), 400
        
        grpo_doc = GRPODocument.query.get_or_404(grpo_id)
        item = GRPOItem.query.get_or_404(item_id)
        
        if grpo_doc.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        if item.grpo_id != grpo_id:
            return jsonify({
                'success': False,
                'error': 'Item does not belong to this GRPO'
            }), 400
        
        grn_date = grpo_doc.created_at.strftime('%Y-%m-%d')
        doc_number = grpo_doc.doc_number or f"GRN/{grpo_doc.id}"
        po_number = grpo_doc.po_number
        
        labels = []
        
        if label_type == 'serial':
            # Generate labels for serial-managed items
            serial_numbers = item.serial_numbers
            total_serials = len(serial_numbers)
            
            for idx, serial in enumerate(serial_numbers, start=1):
                # Use the unique GRN number for this serial
                serial_grn = serial.grn_number or doc_number
                
                qr_data = {
                    'PO': po_number,
                    'SerialNumber': serial.internal_serial_number,
                    'Qty': float(serial.qty_per_pack) if serial.qty_per_pack else 1,
                    'Pack': f"{idx} of {serial.no_of_packs or total_serials}",
                    'GRN Date': grn_date,
                    'Exp Date': serial.expiry_date.strftime('%Y-%m-%d') if serial.expiry_date else 'N/A',
                    'ItemCode': item.item_code,
                    'ItemDesc': item.item_name or '',
                    'id': serial_grn
                }
                
                # Convert to QR code friendly format
                qr_text = '\n'.join([f"{k}: {v}" for k, v in qr_data.items()])
                qr_code_image = generate_barcode(qr_text)
                
                label = {
                    'sequence': idx,
                    'total': serial.no_of_packs or total_serials,
                    'pack_text': f"{idx} of {serial.no_of_packs or total_serials}",
                    'po_number': po_number,
                    'serial_number': serial.internal_serial_number,
                    'quantity': float(serial.qty_per_pack) if serial.qty_per_pack else 1,
                    'qty_per_pack': float(serial.qty_per_pack) if serial.qty_per_pack else 1,
                    'no_of_packs': serial.no_of_packs or total_serials,
                    'grn_date': grn_date,
                    'grn_number': serial_grn,
                    'expiration_date': serial.expiry_date.strftime('%Y-%m-%d') if serial.expiry_date else 'N/A',
                    'item_code': item.item_code,
                    'item_name': item.item_name or '',
                    'doc_number': serial_grn,
                    'qr_code_image': qr_code_image,
                    'qr_data': qr_data
                }
                labels.append(label)
        
        elif label_type == 'batch':
            # Generate labels for batch-managed items
            batch_numbers = item.batch_numbers
            label_counter = 1
            
            for batch in batch_numbers:
                num_packs = batch.no_of_packs or 1
                
                for pack_idx in range(1, num_packs + 1):
                    batch_grn = batch.grn_number or doc_number
                    
                    qr_data = {
                        'PO': po_number,
                        'BatchNumber': batch.batch_number,
                        'Qty': float(batch.qty_per_pack) if batch.qty_per_pack else float(batch.quantity),
                        'Pack': f"{pack_idx} of {num_packs}",
                        'GRN Date': grn_date,
                        'Exp Date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else 'N/A',
                        'ItemCode': item.item_code,
                        'ItemDesc': item.item_name or '',
                        'id': f"{batch_grn}-{pack_idx}"
                    }
                    
                    # Convert to QR code friendly format
                    qr_text = '\n'.join([f"{k}: {v}" for k, v in qr_data.items()])
                    qr_code_image = generate_barcode(qr_text)
                    
                    label = {
                        'sequence': label_counter,
                        'total': num_packs,
                        'pack_text': f"{pack_idx} of {num_packs}",
                        'po_number': po_number,
                        'batch_number': batch.batch_number,
                        'quantity': float(batch.quantity),
                        'qty_per_pack': float(batch.qty_per_pack) if batch.qty_per_pack else float(batch.quantity),
                        'no_of_packs': num_packs,
                        'grn_date': grn_date,
                        'grn_number': f"{batch_grn}-{pack_idx}",
                        'expiration_date': batch.expiry_date.strftime('%Y-%m-%d') if batch.expiry_date else 'N/A',
                        'item_code': item.item_code,
                        'item_name': item.item_name or '',
                        'doc_number': f"{batch_grn}-{pack_idx}",
                        'qr_code_image': qr_code_image,
                        'qr_data': qr_data
                    }
                    labels.append(label)
                    label_counter += 1
        
        else:  # Regular non-serial/non-batch items (non-managed items)
            # Check if there are non_managed_items records (number of bags > 1)
            non_managed_items = item.non_managed_items
            
            if non_managed_items and len(non_managed_items) > 0:
                # Generate labels for each bag/pack
                total_packs = len(non_managed_items)
                
                for idx, non_managed in enumerate(non_managed_items, start=1):
                    # Use the unique GRN number for this pack
                    pack_grn = non_managed.grn_number or doc_number
                    
                    qr_data = {
                        'PO': po_number,
                        'ItemCode': item.item_code,
                        'Qty': float(non_managed.qty_per_pack) if non_managed.qty_per_pack else float(non_managed.quantity),
                        'Pack': f"{idx} of {non_managed.no_of_packs or total_packs}",
                        'GRN': pack_grn,
                        'GRN Date': grn_date,
                        'Exp Date': non_managed.expiry_date.strftime('%Y-%m-%d') if non_managed.expiry_date else 'N/A',
                        'ItemDesc': item.item_name or ''
                    }
                    
                    # Convert to JSON format for QR code as requested by user
                    import json
                    qr_text = json.dumps(qr_data, indent=2)
                    qr_code_image = generate_barcode(qr_text)
                    
                    label = {
                        'sequence': idx,
                        'total': non_managed.no_of_packs or total_packs,
                        'pack_text': f"{idx} of {non_managed.no_of_packs or total_packs}",
                        'po_number': po_number,
                        'quantity': float(non_managed.quantity),
                        'qty_per_pack': float(non_managed.qty_per_pack) if non_managed.qty_per_pack else float(non_managed.quantity),
                        'no_of_packs': non_managed.no_of_packs or total_packs,
                        'grn_date': grn_date,
                        'grn_number': pack_grn,
                        'expiration_date': non_managed.expiry_date.strftime('%Y-%m-%d') if non_managed.expiry_date else 'N/A',
                        'item_code': item.item_code,
                        'item_name': item.item_name or '',
                        'doc_number': pack_grn,
                        'qr_code_image': qr_code_image,
                        'qr_data': qr_data
                    }
                    labels.append(label)
            else:
                # Fallback: Generate a single label for items without bag records
                qr_data = {
                    'PO': po_number,
                    'ItemCode': item.item_code,
                    'Qty': float(item.quantity),
                    'Pack': '1 of 1',
                    'GRN': doc_number,
                    'GRN Date': grn_date,
                    'Exp Date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else 'N/A',
                    'ItemDesc': item.item_name or ''
                }
                
                # Convert to JSON format for QR code
                import json
                qr_text = json.dumps(qr_data, indent=2)
                qr_code_image = generate_barcode(qr_text)
                
                label = {
                    'sequence': 1,
                    'total': 1,
                    'pack_text': '1 of 1',
                    'po_number': po_number,
                    'quantity': float(item.quantity),
                    'grn_date': grn_date,
                    'grn_number': doc_number,
                    'expiration_date': item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else 'N/A',
                    'item_code': item.item_code,
                    'item_name': item.item_name or '',
                    'doc_number': doc_number,
                    'qr_code_image': qr_code_image,
                    'qr_data': qr_data
                }
                labels.append(label)
        
        return jsonify({
            'success': True,
            'labels': labels,
            'grpo_id': grpo_id,
            'item_id': item_id,
            'label_type': label_type,
            'total_labels': len(labels)
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid value: {str(e)}'
        }), 400
    except Exception as e:
        logging.error(f"Error generating barcode labels: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500