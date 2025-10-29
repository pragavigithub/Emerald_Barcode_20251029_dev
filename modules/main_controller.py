"""
Main Controller to integrate all modules
Provides a unified interface to register all module blueprints
"""
from flask import Flask
from modules.grpo.routes import grpo_bp
from modules.inventory_transfer.routes import transfer_bp
from modules.multi_grn_creation.routes import multi_grn_bp

def register_modules(app: Flask):
    """Register all module blueprints with the Flask app"""
    
    # Register GRPO module
    app.register_blueprint(grpo_bp)
    
    # Register Inventory Transfer module
    app.register_blueprint(transfer_bp)
    
    # Register Multiple GRN Creation module
    app.register_blueprint(multi_grn_bp)
    
    # Add module-specific template folders
    app.jinja_loader.searchpath.extend([
        'modules/grpo/templates',
        'modules/inventory_transfer/templates',
        'modules/multi_grn_creation/templates'
    ])
    
    print("✅ All modules registered successfully")
    print("📁 Module structure:")
    print("   - GRPO Module: /grpo/*")
    print("   - Inventory Transfer Module: /inventory_transfer/*")
    print("   - Multiple GRN Creation Module: /multi-grn/*")
    print("   - Shared Models: modules/shared/models.py")

def get_module_info():
    """Get information about available modules"""
    return {
        'grpo': {
            'name': 'Goods Receipt PO',
            'prefix': '/grpo',
            'description': 'Manage goods receipt against purchase orders',
            'models': ['GRPODocument', 'GRPOItem', 'PurchaseDeliveryNote'],
            'routes': ['index', 'detail', 'create', 'submit', 'approve', 'reject']
        },
        'inventory_transfer': {
            'name': 'Inventory Transfer',
            'prefix': '/inventory_transfer',
            'description': 'Manage inventory transfers between warehouses/bins',
            'models': ['InventoryTransfer', 'InventoryTransferItem', 'TransferStatusHistory', 'TransferRequest'],
            'routes': ['index', 'detail', 'create', 'submit', 'qc_approve', 'qc_reject', 'reopen']
        },
        'shared': {
            'name': 'Shared Components',
            'prefix': None,
            'description': 'Common models and utilities used across modules',
            'models': ['User', 'Warehouse', 'BinLocation', 'BusinessPartner'],
            'routes': []
        }
    }