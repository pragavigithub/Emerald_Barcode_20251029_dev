"""
GRPO (Goods Receipt PO) Models
Contains all models related to goods receipt against purchase orders
"""
from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class GRPODocument(db.Model):
    """Main GRPO document header"""
    __tablename__ = 'grpo_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), nullable=False)
    doc_number = db.Column(db.String(50), unique=True)  # GRN/YYYYMMDD/NNNNNNNNNN format - unique constraint enforced
    supplier_code = db.Column(db.String(20))
    supplier_name = db.Column(db.String(100))
    warehouse_code = db.Column(db.String(10))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qc_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    qc_approved_at = db.Column(db.DateTime)
    qc_notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='draft')  # draft, submitted, qc_approved, posted, rejected
    po_total = db.Column(db.Numeric(15, 2))
    sap_document_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='grpo_documents')
    qc_approver = db.relationship('User', foreign_keys=[qc_approver_id])
    items = db.relationship('GRPOItem', backref='grpo_document', lazy=True, cascade='all, delete-orphan')

class GRPOItem(db.Model):
    """GRPO line items"""
    __tablename__ = 'grpo_items'
    
    id = db.Column(db.Integer, primary_key=True)
    grpo_id = db.Column(db.Integer, db.ForeignKey('grpo_documents.id'), nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200))
    quantity = db.Column(db.Numeric(15, 3), nullable=False)
    received_quantity = db.Column(db.Numeric(15, 3), default=0)
    unit_price = db.Column(db.Numeric(15, 4))
    line_total = db.Column(db.Numeric(15, 2))
    unit_of_measure = db.Column(db.String(10))
    warehouse_code = db.Column(db.String(10))
    bin_location = db.Column(db.String(200))
    batch_number = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    barcode = db.Column(db.String(100))
    qc_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    po_line_number = db.Column(db.Integer)
    base_entry = db.Column(db.Integer)  # SAP PO DocEntry
    base_line = db.Column(db.Integer)   # SAP PO Line Number
    
    # Item validation metadata from SAP
    batch_required = db.Column(db.String(1), default='N')  # Y or N
    serial_required = db.Column(db.String(1), default='N')  # Y or N
    manage_method = db.Column(db.String(1), default='N')  # A (Average), R (FIFO/Release), N (None)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PurchaseDeliveryNote(db.Model):
    """Purchase Delivery Note for SAP B1 posting"""
    __tablename__ = 'purchase_delivery_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    grpo_id = db.Column(db.Integer, db.ForeignKey('grpo_documents.id'), nullable=False)
    external_reference = db.Column(db.String(50), unique=True)
    sap_document_number = db.Column(db.String(50))
    supplier_code = db.Column(db.String(20))
    warehouse_code = db.Column(db.String(10))
    document_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(15, 2))
    status = db.Column(db.String(20), default='draft')  # draft, posted, cancelled
    json_payload = db.Column(db.Text)  # Store the JSON sent to SAP
    sap_response = db.Column(db.Text)  # Store SAP response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posted_at = db.Column(db.DateTime)

    # Relationships
    grpo_document = db.relationship('GRPODocument', backref='delivery_notes')

class GRPOSerialNumber(db.Model):
    """Serial numbers for GRPO items"""
    __tablename__ = 'grpo_serial_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    grpo_item_id = db.Column(db.Integer, db.ForeignKey('grpo_items.id'), nullable=False)
    manufacturer_serial_number = db.Column(db.String(100))
    internal_serial_number = db.Column(db.String(100), unique=True, nullable=False)
    expiry_date = db.Column(db.Date)
    manufacture_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1.0)
    base_line_number = db.Column(db.Integer, default=0)
    grn_number = db.Column(db.String(50))
    qty_per_pack = db.Column(db.Numeric(15, 3), default=1.0)
    no_of_packs = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grpo_item = db.relationship('GRPOItem', backref=db.backref('serial_numbers', lazy=True, cascade='all, delete-orphan'))

class GRPOBatchNumber(db.Model):
    """Batch numbers for GRPO items"""
    __tablename__ = 'grpo_batch_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    grpo_item_id = db.Column(db.Integer, db.ForeignKey('grpo_items.id'), nullable=False)
    batch_number = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Numeric(15, 3), nullable=False)
    base_line_number = db.Column(db.Integer, default=0)
    manufacturer_serial_number = db.Column(db.String(100))
    internal_serial_number = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    barcode = db.Column(db.String(200))
    grn_number = db.Column(db.String(50))
    qty_per_pack = db.Column(db.Numeric(15, 3))
    no_of_packs = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grpo_item = db.relationship('GRPOItem', backref=db.backref('batch_numbers', lazy=True, cascade='all, delete-orphan'))

class GRPONonManagedItem(db.Model):
    """Non-batch, Non-serial managed items for GRPO (when both BatchNum='N' and SerialNum='N')"""
    __tablename__ = 'grpo_non_managed_items'
    
    id = db.Column(db.Integer, primary_key=True)
    grpo_item_id = db.Column(db.Integer, db.ForeignKey('grpo_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    base_line_number = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.String(50))
    admin_date = db.Column(db.String(50))
    grn_number = db.Column(db.String(50))
    qty_per_pack = db.Column(db.Integer)
    no_of_packs = db.Column(db.Integer)
    pack_number = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    grpo_item = db.relationship('GRPOItem', backref=db.backref('non_managed_items', lazy=True, cascade='all, delete-orphan'))