from app import db
from datetime import datetime
from sqlalchemy.orm import relationship


class DeliveryDocument(db.Model):
    """Delivery Note Documents - Local storage for tracking delivery notes against sales orders"""
    __tablename__ = 'delivery_documents'

    id = db.Column(db.Integer, primary_key=True)
    so_doc_entry = db.Column(db.Integer, nullable=False, index=True)
    so_doc_num = db.Column(db.Integer, nullable=True)
    so_series = db.Column(db.Integer, nullable=True)
    card_code = db.Column(db.String(50), nullable=True)
    card_name = db.Column(db.String(200), nullable=True)
    doc_currency = db.Column(db.String(10), nullable=True)
    doc_date = db.Column(db.DateTime, nullable=True)
    delivery_series = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='draft')  # draft, submitted, qc_approved, posted, rejected
    sap_doc_entry = db.Column(db.Integer, nullable=True, index=True)
    sap_doc_num = db.Column(db.Integer, nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    qc_approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    qc_approved_at = db.Column(db.DateTime, nullable=True)
    qc_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)
    last_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    qc_approver = relationship('User', foreign_keys=[qc_approver_id])
    items = relationship('DeliveryItem', back_populates='delivery', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DeliveryDocument SO={self.so_doc_num} Status={self.status}>'


class DeliveryItem(db.Model):
    """Delivery Note Line Items - Local storage for tracking individual items"""
    __tablename__ = 'delivery_items'

    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, db.ForeignKey('delivery_documents.id'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    base_line = db.Column(db.Integer, nullable=False)
    item_code = db.Column(db.String(50), nullable=False, index=True)
    item_description = db.Column(db.String(200), nullable=True)
    warehouse_code = db.Column(db.String(10), nullable=True)
    quantity = db.Column(db.Float, nullable=False, default=0)
    open_quantity = db.Column(db.Float, nullable=True, default=0)
    unit_price = db.Column(db.Float, nullable=True, default=0)
    uom_code = db.Column(db.String(10), nullable=True)
    batch_required = db.Column(db.Boolean, default=False)
    serial_required = db.Column(db.Boolean, default=False)
    batch_number = db.Column(db.String(100), nullable=True)
    serial_number = db.Column(db.String(100), nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    manufacture_date = db.Column(db.DateTime, nullable=True)
    bin_location = db.Column(db.String(50), nullable=True)
    project_code = db.Column(db.String(50), nullable=True)
    cost_code = db.Column(db.String(50), nullable=True)
    qr_code_generated = db.Column(db.Boolean, default=False)
    warehouse_routing = db.Column(db.String(200), nullable=True)
    qc_status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    delivery = relationship('DeliveryDocument', back_populates='items')

    def __repr__(self):
        return f'<DeliveryItem Line={self.line_number} Item={self.item_code} Qty={self.quantity}>'
