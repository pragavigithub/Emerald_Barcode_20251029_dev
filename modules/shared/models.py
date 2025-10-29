"""
Shared Models for WMS Application
Contains common models used across modules
"""
from app import db
from datetime import datetime

# Note: User model is defined in models.py
# GRPO and other modules use string references like db.relationship('User', ...)

class Warehouse(db.Model):
    """Warehouse master data"""
    id = db.Column(db.Integer, primary_key=True)
    warehouse_code = db.Column(db.String(10), unique=True, nullable=False)
    warehouse_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BinLocation(db.Model):
    """Bin location master data"""
    id = db.Column(db.Integer, primary_key=True)
    warehouse_code = db.Column(db.String(10), nullable=False)
    bin_code = db.Column(db.String(20), nullable=False)
    bin_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BusinessPartner(db.Model):
    """Business partner (supplier/customer) master data"""
    id = db.Column(db.Integer, primary_key=True)
    card_code = db.Column(db.String(20), unique=True, nullable=False)
    card_name = db.Column(db.String(100), nullable=False)
    card_type = db.Column(db.String(10))  # Supplier, Customer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)