"""
Multiple GRN Creation Module Models
Database models for batch GRN creation from multiple POs
"""
from app import db
from datetime import datetime

class MultiGRNBatch(db.Model):
    """Main batch record for multiple GRN creation"""
    __tablename__ = 'multi_grn_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    customer_code = db.Column(db.String(50), nullable=False)
    customer_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='draft', nullable=False)
    total_pos = db.Column(db.Integer, default=0)
    total_grns_created = db.Column(db.Integer, default=0)
    sap_session_metadata = db.Column(db.Text)
    error_log = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    posted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref='multi_grn_batches')
    po_links = db.relationship('MultiGRNPOLink', backref='batch', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<MultiGRNBatch {self.id} - {self.customer_name}>'

class MultiGRNPOLink(db.Model):
    """Links between GRN batch and selected Purchase Orders"""
    __tablename__ = 'multi_grn_po_links'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('multi_grn_batches.id'), nullable=False)
    po_doc_entry = db.Column(db.Integer, nullable=False)
    po_doc_num = db.Column(db.String(50), nullable=False)
    po_card_code = db.Column(db.String(50))
    po_card_name = db.Column(db.String(200))
    po_doc_date = db.Column(db.Date)
    po_doc_total = db.Column(db.Numeric(15, 2))
    status = db.Column(db.String(20), default='selected', nullable=False)
    sap_grn_doc_num = db.Column(db.String(50))
    sap_grn_doc_entry = db.Column(db.Integer)
    posted_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    line_selections = db.relationship('MultiGRNLineSelection', backref='po_link', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('batch_id', 'po_doc_entry', name='uq_batch_po'),
    )
    
    def __repr__(self):
        return f'<MultiGRNPOLink PO:{self.po_doc_num}>'

class MultiGRNLineSelection(db.Model):
    """Selected line items from Purchase Orders"""
    __tablename__ = 'multi_grn_line_selections'
    
    id = db.Column(db.Integer, primary_key=True)
    po_link_id = db.Column(db.Integer, db.ForeignKey('multi_grn_po_links.id'), nullable=False)
    po_line_num = db.Column(db.Integer, nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_description = db.Column(db.String(200))
    ordered_quantity = db.Column(db.Numeric(15, 3), nullable=False)
    open_quantity = db.Column(db.Numeric(15, 3), nullable=False)
    selected_quantity = db.Column(db.Numeric(15, 3), nullable=False)
    warehouse_code = db.Column(db.String(50))
    bin_location = db.Column(db.String(200))
    unit_price = db.Column(db.Numeric(15, 4))
    line_status = db.Column(db.String(20))
    inventory_type = db.Column(db.String(20))
    serial_numbers = db.Column(db.Text)
    batch_numbers = db.Column(db.Text)
    posting_payload = db.Column(db.Text)
    barcode_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<MultiGRNLineSelection {self.item_code} - Qty:{self.selected_quantity}>'
