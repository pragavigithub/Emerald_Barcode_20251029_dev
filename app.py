import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Load credentials from JSON file instead of .env
try:
    from credentials_loader import load_credentials
    credentials = load_credentials()
    logging.info("✅ Credentials loaded from JSON file or environment variables")
except Exception as e:
    logging.warning(f"⚠️ Could not load credentials: {e}")
    logging.info("Using system environment variables as fallback")

# Configure logging
logging.basicConfig(level=logging.DEBUG)


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask app
app = Flask(__name__)

# Validate SESSION_SECRET is set - required for security
session_secret = os.environ.get("SESSION_SECRET")
if not session_secret:
    raise RuntimeError("SESSION_SECRET environment variable must be set for secure session management")
app.secret_key = session_secret

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration - PostgreSQL required for Replit environment
database_url_env = os.environ.get("DATABASE_URL", "")

# Validate DATABASE_URL is set and is PostgreSQL
if not database_url_env:
    raise RuntimeError("DATABASE_URL environment variable must be set")

# if not ("postgres" in database_url_env or "postgresql" in database_url_env):
#     raise RuntimeError("DATABASE_URL must be a PostgreSQL connection string for Replit environment")

logging.info(f"✅ Using PostgreSQL database (Replit environment): {database_url_env[:50]}...")

# Convert postgres:// to postgresql:// if needed for SQLAlchemy compatibility
if database_url_env.startswith("postgres://"):
    database_url_env = database_url_env.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url_env
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10
}
db_type = "postgresql"

# Test PostgreSQL connection - fail fast if connection fails
from sqlalchemy import create_engine, text
try:
    test_engine = create_engine(database_url_env, pool_pre_ping=True)
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logging.info("✅ PostgreSQL database connection successful")
    database_url = database_url_env
except Exception as e:
    raise RuntimeError(f"PostgreSQL connection failed: {e}")

# Store database type for use in other modules
app.config["DB_TYPE"] = db_type

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access this page.'

# SAP B1 Configuration - Updated with user's real SAP server
app.config['SAP_B1_SERVER'] = os.environ.get('SAP_B1_SERVER',
                                             'https://10.112.253.173:50000')
app.config['SAP_B1_USERNAME'] = os.environ.get('SAP_B1_USERNAME', 'manager')
app.config['SAP_B1_PASSWORD'] = os.environ.get('SAP_B1_PASSWORD', '1422')
app.config['SAP_B1_COMPANY_DB'] = os.environ.get('SAP_B1_COMPANY_DB',
                                                 'SBODemoUS')

# Import models after app is configured to avoid circular imports
import models
import models_extensions
from modules.grpo import models as grpo_models
from modules.multi_grn_creation import models as multi_grn_models

with app.app_context():
    # Create all database tables first
    db.create_all()
    logging.info("Database tables created")
    
    # Fix duplicate serial number constraint issue - drop unique constraint to allow duplicates
    if db_type == "mysql":
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                # Check if the constraint exists and drop it
                result = conn.execute(text("""
                    SELECT CONSTRAINT_NAME 
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'serial_number_transfer_serials' 
                    AND CONSTRAINT_NAME = 'unique_serial_per_item'
                """))
                
                if result.fetchone():
                    conn.execute(text("ALTER TABLE serial_number_transfer_serials DROP INDEX unique_serial_per_item"))
                    conn.commit()
                    logging.info("✅ Dropped unique_serial_per_item constraint to allow duplicate serial numbers")
                else:
                    logging.info("ℹ️ unique_serial_per_item constraint not found, skipping")
        except Exception as e:
            logging.warning(f"⚠️ Could not drop unique constraint: {e}")
    
    # Create default data for PostgreSQL database
    try:
        from models_extensions import Branch
        from werkzeug.security import generate_password_hash
        from models import User
        
        # Create default branch
        default_branch = Branch.query.filter_by(id='BR001').first()
        if not default_branch:
            default_branch = Branch()
            default_branch.id = 'BR001'
            default_branch.name = 'Main Branch'
            default_branch.branch_code = 'BR001'  # Required field
            default_branch.branch_name = 'Main Branch'  # Required field
            default_branch.description = 'Main Office Branch'
            default_branch.address = 'Main Office'
            default_branch.phone = '123-456-7890'
            default_branch.email = 'main@company.com'
            default_branch.manager_name = 'Branch Manager'
            default_branch.is_active = True
            default_branch.is_default = True
            db.session.add(default_branch)
            logging.info("Default branch created")
        
        # Create default admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User()
            admin.username = 'admin'
            admin.email = 'admin@company.com'
            admin.password_hash = generate_password_hash('admin123')
            admin.first_name = 'System'
            admin.last_name = 'Administrator'
            admin.role = 'admin'
            admin.branch_id = 'BR001'
            admin.branch_name = 'Main Branch'
            admin.default_branch_id = 'BR001'
            admin.is_active = True
            admin.must_change_password = False
            db.session.add(admin)
            logging.info("Default admin user created")
            
        db.session.commit()
        logging.info("✅ Default data initialization completed")
        
    except Exception as e:
        logging.error(f"Error initializing default data: {e}")
        db.session.rollback()
        # Continue with application startup

# Initialize dual database support for MySQL sync 
# Enable by default but fail gracefully if MySQL not available
try:
    from db_dual_support import init_dual_database
    dual_db = init_dual_database(app)
    app.config['DUAL_DB'] = dual_db
    logging.info("✅ Dual database support initialized for MySQL sync")
except Exception as e:
    logging.warning(f"⚠️ Dual database support not available: {e}")
    app.config['DUAL_DB'] = None
    logging.info("💡 MySQL sync disabled, using single database mode")

# Validate and create SAP B1 SQL Queries on startup
try:
    from sap_query_manager import validate_sap_queries
    validate_sap_queries(app)
except Exception as e:
    logging.warning(f"⚠️ SAP query validation skipped: {e}")
    logging.info("💡 Application will continue without SAP query validation")

# Import and register blueprints
from modules.inventory_transfer.routes import transfer_bp
from modules.serial_item_transfer.routes import serial_item_bp
from modules.multi_grn_creation.routes import multi_grn_bp
from modules.grpo.routes import grpo_bp
from modules.sales_delivery.routes import sales_delivery_bp
from modules.direct_inventory_transfer.routes import direct_inventory_transfer_bp

app.register_blueprint(transfer_bp)
app.register_blueprint(serial_item_bp)
app.register_blueprint(multi_grn_bp)
app.register_blueprint(grpo_bp)
app.register_blueprint(sales_delivery_bp)
app.register_blueprint(direct_inventory_transfer_bp)

# Add module-specific template folders to Jinja loader search path
app.jinja_loader.searchpath.extend([
    'modules/grpo/templates',
    'modules/inventory_transfer/templates',
    'modules/multi_grn_creation/templates',
    'modules/serial_item_transfer/templates',
    'modules/direct_inventory_transfer/templates'
])

logging.info("✅ All module blueprints registered and template paths configured")

# Register custom Jinja2 filters
import json

@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string to Python object for use in templates"""
    if value is None or value == '':
        return []
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []

logging.info("✅ Custom Jinja2 filters registered")

# Import routes to register them
import routes
