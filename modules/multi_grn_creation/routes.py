"""
Multiple GRN Creation Routes
Multi-step workflow for creating GRNs from multiple Purchase Orders
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from modules.multi_grn_creation.models import MultiGRNBatch, MultiGRNPOLink, MultiGRNLineSelection
from modules.multi_grn_creation.services import SAPMultiGRNService
import logging
from datetime import datetime, date
import json
from decimal import Decimal, InvalidOperation

multi_grn_bp = Blueprint('multi_grn', __name__, url_prefix='/multi-grn')

@multi_grn_bp.route('/')
@login_required
def index():
    """Main page - list all GRN batches for current user"""
    if not current_user.has_permission('multiple_grn'):
        flash('Access denied - Multiple GRN permissions required', 'error')
        return redirect(url_for('dashboard'))
    
    batches = MultiGRNBatch.query.filter_by(user_id=current_user.id).order_by(MultiGRNBatch.created_at.desc()).all()
    return render_template('multi_grn/index.html', batches=batches)

@multi_grn_bp.route('/create/step1', methods=['GET', 'POST'])
@login_required
def create_step1_customer():
    """Step 1: Select Customer"""
    if not current_user.has_permission('multiple_grn'):
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        customer_code = request.form.get('customer_code')
        customer_name = request.form.get('customer_name')
        
        if not customer_code or not customer_name:
            flash('Please select a customer', 'error')
            return redirect(url_for('multi_grn.create_step1_customer'))
        
        from datetime import datetime
        batch_number = f"MGRN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        batch = MultiGRNBatch(
            user_id=current_user.id,
            batch_number=batch_number,
            customer_code=customer_code,
            customer_name=customer_name,
            status='draft'
        )
        db.session.add(batch)
        db.session.commit()
        
        logging.info(f"✅ Created GRN batch {batch.batch_number} for customer {customer_name}")
        return redirect(url_for('multi_grn.create_step2_select_pos', batch_id=batch.id))
    
    return render_template('multi_grn/step1_customer.html')

@multi_grn_bp.route('/create/step2/<int:batch_id>', methods=['GET', 'POST'])
@login_required
def create_step2_select_pos(batch_id):
    """Step 2: Select Purchase Orders"""
    batch = MultiGRNBatch.query.get_or_404(batch_id)
    
    if batch.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('multi_grn.index'))
    
    if request.method == 'POST':
        selected_pos = request.form.getlist('selected_pos[]')
        
        if not selected_pos:
            flash('Please select at least one Purchase Order', 'error')
            return redirect(url_for('multi_grn.create_step2_select_pos', batch_id=batch_id))
        
        for po_data_json in selected_pos:
            po_data = json.loads(po_data_json)
            
            po_link = MultiGRNPOLink(
                batch_id=batch.id,
                po_doc_entry=po_data['DocEntry'],
                po_doc_num=po_data['DocNum'],
                po_card_code=po_data['CardCode'],
                po_card_name=po_data['CardName'],
                po_doc_date=datetime.strptime(po_data['DocDate'][:10], '%Y-%m-%d').date() if po_data.get('DocDate') else None,
                po_doc_total=Decimal(str(po_data.get('DocTotal', 0))),
                status='selected'
            )
            db.session.add(po_link)
        
        batch.total_pos = len(selected_pos)
        db.session.commit()
        
        logging.info(f"✅ Added {len(selected_pos)} POs to batch {batch_id}")
        flash(f'Selected {len(selected_pos)} Purchase Orders', 'success')
        return redirect(url_for('multi_grn.create_step3_select_lines', batch_id=batch_id))
    
    sap_service = SAPMultiGRNService()
    result = sap_service.fetch_open_purchase_orders_by_name(batch.customer_name)
    
    if not result['success']:
        flash(f"Error fetching Purchase Orders: {result.get('error')}", 'error')
        return redirect(url_for('multi_grn.index'))
    
    purchase_orders = result.get('purchase_orders', [])
    logging.info(f"📊 Found {len(purchase_orders)} open POs for customer {batch.customer_name} ({batch.customer_code})")
    return render_template('multi_grn/step2_select_pos.html', batch=batch, purchase_orders=purchase_orders)

@multi_grn_bp.route('/create/step3/<int:batch_id>', methods=['GET', 'POST'])
@login_required
def create_step3_select_lines(batch_id):
    """Step 3: Select line items from POs"""
    batch = MultiGRNBatch.query.get_or_404(batch_id)
    
    if batch.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('multi_grn.index'))
    
    if request.method == 'POST':
        for po_link in batch.po_links:
            selected_lines = request.form.getlist(f'lines_po_{po_link.id}[]')
            
            for line_data_json in selected_lines:
                line_data = json.loads(line_data_json)
                qty_key = f'qty_po_{po_link.id}_line_{line_data["LineNum"]}'
                open_qty = line_data.get('OpenQuantity', line_data.get('Quantity', 0))
                selected_qty = Decimal(request.form.get(qty_key, open_qty))
                
                if selected_qty > 0:
                    line_selection = MultiGRNLineSelection(
                        po_link_id=po_link.id,
                        po_line_num=line_data['LineNum'],
                        item_code=line_data['ItemCode'],
                        item_description=line_data.get('ItemDescription', ''),
                        ordered_quantity=Decimal(str(line_data.get('Quantity', 0))),
                        open_quantity=Decimal(str(line_data.get('OpenQuantity', line_data.get('Quantity', 0)))),
                        selected_quantity=selected_qty,
                        warehouse_code=line_data.get('WarehouseCode', ''),
                        unit_price=Decimal(str(line_data.get('UnitPrice', 0))),
                        line_status=line_data.get('LineStatus', ''),
                        inventory_type=line_data.get('ManageSerialNumbers') or line_data.get('ManageBatchNumbers') or 'standard'
                    )
                    db.session.add(line_selection)
        
        db.session.commit()
        logging.info(f"✅ Line items selected for batch {batch_id}")
        flash('Line items selected successfully', 'success')
        return redirect(url_for('multi_grn.create_step4_review', batch_id=batch_id))
    
    sap_service = SAPMultiGRNService()
    po_details = []
    
    for po_link in batch.po_links:
        result = sap_service.fetch_open_purchase_orders_by_name(batch.customer_name)
        logging.info(f"📊 Step 3 - Fetched PO details for {batch.customer_name}: {result.get('success')}")
        if result['success']:
            for po in result['purchase_orders']:
                if po['DocEntry'] == po_link.po_doc_entry:
                    po_details.append({
                        'po_link': po_link,
                        'lines': po.get('OpenLines', [])
                    })
                    break
    
    return render_template('multi_grn/step3_select_lines.html', batch=batch, po_details=po_details)

@multi_grn_bp.route('/create/step4/<int:batch_id>')
@login_required
def create_step4_review(batch_id):
    """Step 4: Review selections before posting"""
    batch = MultiGRNBatch.query.get_or_404(batch_id)
    
    if batch.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('multi_grn.index'))
    
    return render_template('multi_grn/step4_review.html', batch=batch)

@multi_grn_bp.route('/create/step5/<int:batch_id>', methods=['POST'])
@login_required
def create_step5_post(batch_id):
    """Step 5: Post GRNs to SAP B1"""
    batch = MultiGRNBatch.query.get_or_404(batch_id)
    
    if batch.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    try:
        sap_service = SAPMultiGRNService()
        results = []
        success_count = 0
        
        for po_link in batch.po_links:
            if not po_link.line_selections:
                continue
            
            document_lines = []
            for line in po_link.line_selections:
                # Check if this is a manual item (not from PO line)
                if line.line_status == 'manual' or line.po_line_num == -1:
                    # Manual item - no base reference to PO
                    doc_line = {
                        'ItemCode': line.item_code,
                        'Quantity': float(line.selected_quantity),
                        'WarehouseCode': line.warehouse_code or '7000-FG'
                    }
                else:
                    # PO-based item - include base reference
                    doc_line = {
                        'BaseType': 22,
                        'BaseEntry': po_link.po_doc_entry,
                        'BaseLine': line.po_line_num,
                        'ItemCode': line.item_code,
                        'Quantity': float(line.selected_quantity),
                        'WarehouseCode': line.warehouse_code or '7000-FG'
                    }
                
                # Add batch/serial numbers if present
                if line.serial_numbers:
                    serial_data = json.loads(line.serial_numbers) if isinstance(line.serial_numbers, str) else line.serial_numbers
                    doc_line['SerialNumbers'] = serial_data
                
                if line.batch_numbers:
                    batch_data = json.loads(line.batch_numbers) if isinstance(line.batch_numbers, str) else line.batch_numbers
                    doc_line['BatchNumbers'] = batch_data
                
                document_lines.append(doc_line)
            
            grn_data = {
                'CardCode': po_link.po_card_code,
                'DocDate': date.today().isoformat(),
                'DocDueDate': date.today().isoformat(),
                'Comments': f'Auto-created from batch {batch.id}',
                'NumAtCard': f'BATCH-{batch.id}-PO-{po_link.po_doc_num}',
                'BPL_IDAssignedToInvoice': 5,
                'DocumentLines': document_lines
            }
            
            result = sap_service.create_purchase_delivery_note(grn_data)
            
            if result['success']:
                po_link.status = 'posted'
                po_link.sap_grn_doc_num = result.get('doc_num')
                po_link.sap_grn_doc_entry = result.get('doc_entry')
                po_link.posted_at = datetime.utcnow()
                success_count += 1
                results.append({'po_num': po_link.po_doc_num, 'success': True, 'grn_num': result.get('doc_num')})
            else:
                po_link.status = 'failed'
                po_link.error_message = result.get('error')
                results.append({'po_num': po_link.po_doc_num, 'success': False, 'error': result.get('error')})
        
        batch.status = 'completed' if success_count > 0 else 'failed'
        batch.total_grns_created = success_count
        batch.completed_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"✅ Batch {batch_id} completed: {success_count} GRNs created")
        return jsonify({
            'success': True,
            'results': results,
            'total_success': success_count,
            'total_failed': len(results) - success_count
        })
        
    except Exception as e:
        logging.error(f"❌ Error posting GRNs for batch {batch_id}: {str(e)}")
        batch.status = 'failed'
        batch.error_log = str(e)
        db.session.commit()
        return jsonify({'success': False, 'error': str(e)}), 500

@multi_grn_bp.route('/batch/<int:batch_id>')
@login_required
def view_batch(batch_id):
    """View batch details"""
    batch = MultiGRNBatch.query.get_or_404(batch_id)
    
    if batch.user_id != current_user.id and current_user.role not in ['admin', 'manager']:
        flash('Access denied', 'error')
        return redirect(url_for('multi_grn.index'))
    
    return render_template('multi_grn/view_batch.html', batch=batch)

@multi_grn_bp.route('/api/search-customers')
@login_required
def api_search_customers():
    """API endpoint to search customers (legacy - kept for backward compatibility)"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify({'customers': []})
    
    sap_service = SAPMultiGRNService()
    result = sap_service.fetch_business_partners('S')
    
    if not result['success']:
        return jsonify({'error': result.get('error')}), 500
    
    partners = result.get('partners', [])
    filtered = [p for p in partners if query.lower() in p['CardName'].lower() or query.lower() in p['CardCode'].lower()]
    
    return jsonify({'customers': filtered[:20]})

@multi_grn_bp.route('/api/customers-dropdown')
@login_required
def api_customers_dropdown():
    """API endpoint to fetch all valid customers for dropdown"""
    sap_service = SAPMultiGRNService()
    result = sap_service.fetch_all_valid_customers()
    
    if not result['success']:
        return jsonify({'success': False, 'error': result.get('error')}), 500
    
    customers = result.get('customers', [])
    return jsonify({'success': True, 'customers': customers})

@multi_grn_bp.route('/api/generate-barcode', methods=['POST'])
@login_required
def generate_barcode():
    """Generate barcode/QR code for MultiGRN item"""
    try:
        data = request.get_json()
        item_code = data.get('item_code')
        item_name = data.get('item_name', '')
        batch_number = data.get('batch_number', '')
        serial_number = data.get('serial_number', '')
        grn_doc_num = data.get('grn_doc_num', '')
        batch_id = data.get('batch_id')
        
        if not item_code:
            return jsonify({'success': False, 'error': 'Item code is required'}), 400
        
        qr_string = f"{item_code}|{grn_doc_num}|{item_name}|{batch_number or serial_number or 'N/A'}"
        
        return jsonify({
            'success': True,
            'qr_data': qr_string,
            'label_info': {
                'item_code': item_code,
                'grn_doc_num': grn_doc_num,
                'item_name': item_name,
                'batch_number': batch_number,
                'serial_number': serial_number,
                'batch_id': batch_id
            }
        })
        
    except Exception as e:
        logging.error(f"Error generating barcode: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@multi_grn_bp.route('/api/validate-item', methods=['POST'])
@login_required
def validate_item():
    """Validate item code and return batch/serial management info"""
    try:
        data = request.get_json()
        item_code = data.get('item_code')
        
        if not item_code:
            return jsonify({'success': False, 'error': 'Item code is required'}), 400
        
        sap_service = SAPMultiGRNService()
        
        # Validate item and get batch/serial info
        validation_result = sap_service.validate_item_code(item_code)
        
        if not validation_result['success']:
            return jsonify(validation_result), 404
        
        # Get item details (name, UoM, etc.)
        details_result = sap_service.get_item_details(item_code)
        
        if details_result['success']:
            validation_result['item_name'] = details_result['item'].get('ItemName', '')
            validation_result['uom'] = details_result['item'].get('InventoryUOM', '')
        
        return jsonify(validation_result)
        
    except Exception as e:
        logging.error(f"Error validating item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@multi_grn_bp.route('/api/add-manual-item', methods=['POST'])
@login_required
def add_manual_item():
    """Add a manual item to a PO link"""
    try:
        # Parse and validate JSON request body
        data = request.get_json()
        if data is None:
            return jsonify({'success': False, 'error': 'Invalid or missing JSON request body'}), 400
        
        po_link_id = data.get('po_link_id')
        item_code = data.get('item_code')
        item_description = data.get('item_description')
        quantity = data.get('quantity')
        uom = data.get('uom')
        warehouse_code = data.get('warehouse_code')
        bin_location = data.get('bin_location')
        batch_number = data.get('batch_number')
        expiry_date = data.get('expiry_date')
        serial_number = data.get('serial_number')
        supplier_barcode = data.get('supplier_barcode')
        
        if not all([po_link_id, item_code, quantity]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    except Exception as parse_error:
        # Catch JSON parsing errors (BadRequest, etc.)
        return jsonify({'success': False, 'error': f'Invalid JSON format: {str(parse_error)}'}), 400
    
    try:
        
        # Validate quantity format early
        try:
            quantity_decimal = Decimal(str(quantity))
            if quantity_decimal <= 0:
                return jsonify({'success': False, 'error': 'Quantity must be positive'}), 400
        except (ValueError, TypeError, InvalidOperation):
            return jsonify({'success': False, 'error': 'Invalid quantity format (must be numeric)'}), 400
        
        po_link = MultiGRNPOLink.query.get(po_link_id)
        if not po_link:
            return jsonify({'success': False, 'error': 'PO link not found'}), 404
        
        # Check if item already exists in line selections
        existing_line = MultiGRNLineSelection.query.filter_by(
            po_link_id=po_link_id,
            item_code=item_code
        ).first()
        
        if existing_line:
            return jsonify({'success': False, 'error': 'Item already exists in this PO'}), 400
        
        # SERVER-SIDE VALIDATION: Validate item code with SAP to get canonical inventory type
        sap_service = SAPMultiGRNService()
        validation_result = sap_service.validate_item_code(item_code)
        
        if not validation_result['success']:
            return jsonify({'success': False, 'error': f'Item validation failed: {validation_result.get("error")}'}), 400
        
        # Use server-validated inventory type, not client-provided value
        inventory_type = validation_result['inventory_type']
        batch_managed = validation_result['batch_managed']
        serial_managed = validation_result['serial_managed']
        
        # Create new line selection
        line_selection = MultiGRNLineSelection(
            po_link_id=po_link_id,
            po_line_num=-1,  # Manual item, not from PO line
            item_code=item_code,
            item_description=item_description or '',
            ordered_quantity=Decimal(str(quantity)),
            open_quantity=Decimal(str(quantity)),
            selected_quantity=Decimal(str(quantity)),
            warehouse_code=warehouse_code or '7000-FG',
            bin_location=bin_location,
            unit_price=Decimal('0'),
            line_status='manual',
            inventory_type=inventory_type
        )
        
        # SERVER-SIDE VALIDATION: Handle batch/serial numbers based on server-validated type
        if batch_managed:
            batch_numbers_data = data.get('batch_numbers')
            if not batch_numbers_data:
                return jsonify({'success': False, 'error': 'Batch numbers are required for batch-managed items'}), 400
            
            # Parse JSON if string
            if isinstance(batch_numbers_data, str):
                try:
                    batch_array = json.loads(batch_numbers_data)
                except json.JSONDecodeError:
                    return jsonify({'success': False, 'error': 'Invalid batch numbers JSON format'}), 400
            else:
                batch_array = batch_numbers_data
            
            # Validate batch array
            if not isinstance(batch_array, list) or len(batch_array) == 0:
                return jsonify({'success': False, 'error': 'At least one batch entry is required'}), 400
            
            total_batch_qty = Decimal('0')
            for idx, batch in enumerate(batch_array):
                # Validate entry is a dict
                if not isinstance(batch, dict):
                    return jsonify({'success': False, 'error': f'Batch #{idx+1}: Invalid batch entry format (must be an object)'}), 400
                
                # Validate required fields
                if not batch.get('BatchNumber'):
                    return jsonify({'success': False, 'error': f'Batch #{idx+1}: BatchNumber is required'}), 400
                if not batch.get('Quantity'):
                    return jsonify({'success': False, 'error': f'Batch #{idx+1}: Quantity is required'}), 400
                
                try:
                    batch_qty = Decimal(str(batch['Quantity']))
                    if batch_qty <= 0:
                        return jsonify({'success': False, 'error': f'Batch #{idx+1}: Quantity must be positive'}), 400
                    total_batch_qty += batch_qty
                except (ValueError, TypeError, InvalidOperation):
                    return jsonify({'success': False, 'error': f'Batch #{idx+1}: Invalid quantity format (must be numeric)'}), 400
            
            # Validate total batch quantity matches item quantity
            item_qty = Decimal(str(quantity))
            if abs(total_batch_qty - item_qty) > Decimal('0.001'):
                return jsonify({'success': False, 'error': f'Total batch quantity ({total_batch_qty}) must equal item quantity ({item_qty})'}), 400
            
            # Store normalized JSON
            line_selection.batch_numbers = json.dumps(batch_array)
        
        elif serial_managed:
            serial_numbers_data = data.get('serial_numbers')
            if not serial_numbers_data:
                return jsonify({'success': False, 'error': 'Serial numbers are required for serial-managed items'}), 400
            
            # Validate quantity is a positive integer for serial-managed items
            try:
                item_qty_decimal = Decimal(str(quantity))
                if item_qty_decimal <= 0:
                    return jsonify({'success': False, 'error': 'Quantity must be positive for serial-managed items'}), 400
                
                # Check if quantity is an integer
                if item_qty_decimal % 1 != 0:
                    return jsonify({'success': False, 'error': 'Quantity must be a whole number for serial-managed items (one serial per unit)'}), 400
                
                item_qty = int(item_qty_decimal)
            except (ValueError, TypeError, InvalidOperation):
                return jsonify({'success': False, 'error': 'Invalid quantity format (must be numeric)'}), 400
            
            # Parse JSON if string
            if isinstance(serial_numbers_data, str):
                try:
                    serial_array = json.loads(serial_numbers_data)
                except json.JSONDecodeError:
                    return jsonify({'success': False, 'error': 'Invalid serial numbers JSON format'}), 400
            else:
                serial_array = serial_numbers_data
            
            # Validate serial array
            if not isinstance(serial_array, list) or len(serial_array) == 0:
                return jsonify({'success': False, 'error': 'At least one serial number is required'}), 400
            
            # Validate exact 1:1 ratio between serial entries and quantity
            if len(serial_array) != item_qty:
                return jsonify({'success': False, 'error': f'Number of serial entries ({len(serial_array)}) must exactly equal quantity ({item_qty})'}), 400
            
            # Validate each serial entry
            for idx, serial in enumerate(serial_array):
                # Validate entry is a dict
                if not isinstance(serial, dict):
                    return jsonify({'success': False, 'error': f'Serial #{idx+1}: Invalid serial entry format (must be an object)'}), 400
                
                # Validate required fields
                if not serial.get('ManufacturerSerialNumber'):
                    return jsonify({'success': False, 'error': f'Serial #{idx+1}: ManufacturerSerialNumber is required'}), 400
                if not serial.get('InternalSerialNumber'):
                    return jsonify({'success': False, 'error': f'Serial #{idx+1}: InternalSerialNumber is required'}), 400
            
            # Store normalized JSON
            line_selection.serial_numbers = json.dumps(serial_array)
        
        db.session.add(line_selection)
        db.session.commit()
        
        logging.info(f"✅ Manual item {item_code} added to PO link {po_link_id} (type: {inventory_type})")
        return jsonify({
            'success': True,
            'message': 'Item added successfully',
            'line_id': line_selection.id
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding manual item: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
