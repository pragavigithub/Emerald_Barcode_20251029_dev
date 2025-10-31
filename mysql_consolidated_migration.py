#!/usr/bin/env python3
"""
Consolidated MySQL Migration Script - All WMS Tables
Combines all migration scripts into a single comprehensive file.
This is the ONLY migration file you need to run.

INCLUDES:
✅ Core WMS tables (users, branches, sessions)
✅ GRPO module with serial/batch number support
✅ Inventory transfers and serial transfers
✅ Pick lists and QC workflows
✅ Serial item transfers
✅ Multi-GRN support
✅ Document number series
✅ Performance optimizations and indexing

Run with: python mysql_consolidated_migration.py
"""

import os
import sys
import logging
import pymysql
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MySQLConsolidatedMigration:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def get_database_config(self):
        """Get database configuration from environment or user input"""
        config = {
            'host': os.getenv('MYSQL_HOST') or input('MySQL Host (localhost): ') or 'localhost',
            'port': int(os.getenv('MYSQL_PORT') or input('MySQL Port (3306): ') or '3306'),
            'user': os.getenv('MYSQL_USER') or input('MySQL User (root): ') or 'root',
            'password': os.getenv('MYSQL_PASSWORD') or input('MySQL Password: '),
            'database': os.getenv('MYSQL_DATABASE') or input('Database Name (wms_db): ') or 'wms_db',
            'charset': 'utf8mb4',
            'autocommit': False
        }
        return config
    
    def connect(self, config):
        """Connect to MySQL database"""
        try:
            self.connection = pymysql.connect(**config)
            self.cursor = self.connection.cursor()
            logger.info(f"✅ Connected to MySQL: {config['database']}")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def create_all_tables(self):
        """Create all WMS tables with latest schema"""
        
        tables = {
            # 1. Document Number Series
            'document_number_series': '''
                CREATE TABLE IF NOT EXISTS document_number_series (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_type VARCHAR(20) NOT NULL UNIQUE,
                    prefix VARCHAR(10) NOT NULL,
                    current_number INT DEFAULT 1,
                    year_suffix BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_document_type (document_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 2. Branches/Locations
            'branches': '''
                CREATE TABLE IF NOT EXISTS branches (
                    id VARCHAR(10) PRIMARY KEY,
                    name VARCHAR(100),
                    description VARCHAR(255),
                    branch_code VARCHAR(10) UNIQUE NOT NULL,
                    branch_name VARCHAR(100) NOT NULL,
                    address VARCHAR(255),
                    city VARCHAR(50),
                    state VARCHAR(50),
                    postal_code VARCHAR(20),
                    country VARCHAR(50),
                    phone VARCHAR(20),
                    email VARCHAR(120),
                    manager_name VARCHAR(100),
                    warehouse_codes TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_branch_code (branch_code),
                    INDEX idx_active (active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 3. Users
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(80),
                    last_name VARCHAR(80),
                    role VARCHAR(20) NOT NULL DEFAULT 'user',
                    branch_id VARCHAR(10),
                    branch_name VARCHAR(100),
                    default_branch_id VARCHAR(10),
                    active BOOLEAN DEFAULT TRUE,
                    must_change_password BOOLEAN DEFAULT FALSE,
                    last_login TIMESTAMP NULL,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_username (username),
                    INDEX idx_email (email),
                    INDEX idx_role (role),
                    INDEX idx_active (active),
                    INDEX idx_branch_id (branch_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 4. GRPO Documents
            'grpo_documents': '''
                CREATE TABLE IF NOT EXISTS grpo_documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    po_number VARCHAR(50) NOT NULL,
                    supplier_code VARCHAR(20),
                    supplier_name VARCHAR(100),
                    warehouse_code VARCHAR(10),
                    user_id INT NOT NULL,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    status VARCHAR(20) DEFAULT 'draft',
                    po_total DECIMAL(15,2),
                    sap_document_number VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id),
                    INDEX idx_po_number (po_number),
                    INDEX idx_status (status),
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 5. GRPO Items
            'grpo_items': '''
                CREATE TABLE IF NOT EXISTS grpo_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_id INT NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200),
                    quantity DECIMAL(15,3) NOT NULL,
                    received_quantity DECIMAL(15,3) DEFAULT 0,
                    unit_price DECIMAL(15,4),
                    line_total DECIMAL(15,2),
                    unit_of_measure VARCHAR(10),
                    warehouse_code VARCHAR(10),
                    bin_location VARCHAR(200),
                    batch_number VARCHAR(50),
                    serial_number VARCHAR(50),
                    expiry_date DATE,
                    barcode TEXT,
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    po_line_number INT,
                    base_entry INT,
                    base_line INT,
                    batch_required VARCHAR(1) DEFAULT 'N',
                    serial_required VARCHAR(1) DEFAULT 'N',
                    manage_method VARCHAR(1) DEFAULT 'N',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
                    INDEX idx_grpo_id (grpo_id),
                    INDEX idx_item_code (item_code),
                    INDEX idx_qc_status (qc_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 6. GRPO Serial Numbers (Enhanced)
            'grpo_serial_numbers': '''
                CREATE TABLE IF NOT EXISTS grpo_serial_numbers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_item_id INT NOT NULL,
                    manufacturer_serial_number VARCHAR(100),
                    internal_serial_number VARCHAR(100) NOT NULL UNIQUE,
                    expiry_date DATE,
                    manufacture_date DATE,
                    notes TEXT,
                    barcode TEXT,
                    quantity DECIMAL(15,3) DEFAULT 1.0,
                    base_line_number INT DEFAULT 0,
                    grn_number VARCHAR(50),
                    qty_per_pack DECIMAL(15,3) DEFAULT 1.0,
                    no_of_packs INT DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grpo_item_id) REFERENCES grpo_items(id) ON DELETE CASCADE,
                    INDEX idx_grpo_item_id (grpo_item_id),
                    INDEX idx_internal_serial (internal_serial_number),
                    INDEX idx_grpo_serial_grn (grn_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 7. GRPO Batch Numbers (Enhanced)
            'grpo_batch_numbers': '''
                CREATE TABLE IF NOT EXISTS grpo_batch_numbers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    grpo_item_id INT NOT NULL,
                    batch_number VARCHAR(100) NOT NULL,
                    quantity DECIMAL(15,3) NOT NULL,
                    base_line_number INT DEFAULT 0,
                    manufacturer_serial_number VARCHAR(100),
                    internal_serial_number VARCHAR(100),
                    expiry_date DATE,
                    barcode TEXT,
                    grn_number VARCHAR(50),
                    qty_per_pack DECIMAL(15,3),
                    no_of_packs INT DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (grpo_item_id) REFERENCES grpo_items(id) ON DELETE CASCADE,
                    INDEX idx_grpo_item_id (grpo_item_id),
                    INDEX idx_batch_number (batch_number),
                    INDEX idx_grpo_batch_grn (grn_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 8. Inventory Transfers
            'inventory_transfers': '''
                CREATE TABLE IF NOT EXISTS inventory_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_request_number VARCHAR(20) NOT NULL,
                    sap_document_number VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INT NOT NULL,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(20),
                    to_warehouse VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id),
                    INDEX idx_transfer_request_number (transfer_request_number),
                    INDEX idx_status (status),
                    INDEX idx_user_id (user_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 9. Inventory Transfer Items
            'inventory_transfer_items': '''
                CREATE TABLE IF NOT EXISTS inventory_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    inventory_transfer_id INT NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200) NOT NULL,
                    quantity DECIMAL(15,4) NOT NULL,
                    requested_quantity DECIMAL(15,4) NOT NULL,
                    transferred_quantity DECIMAL(15,4) DEFAULT 0,
                    remaining_quantity DECIMAL(15,4) NOT NULL,
                    unit_of_measure VARCHAR(10) NOT NULL,
                    from_bin VARCHAR(20),
                    to_bin VARCHAR(20),
                    from_bin_location VARCHAR(50),
                    to_bin_location VARCHAR(50),
                    batch_number VARCHAR(50),
                    available_batches TEXT,
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    qc_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inventory_transfer_id) REFERENCES inventory_transfers(id) ON DELETE CASCADE,
                    INDEX idx_inventory_transfer_id (inventory_transfer_id),
                    INDEX idx_item_code (item_code),
                    INDEX idx_qc_status (qc_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 10. Serial Number Transfers
            'serial_number_transfers': '''
                CREATE TABLE IF NOT EXISTS serial_number_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_number VARCHAR(50) NOT NULL UNIQUE,
                    sap_document_number VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INT NOT NULL,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(10) NOT NULL,
                    to_warehouse VARCHAR(10) NOT NULL,
                    priority VARCHAR(10) DEFAULT 'normal',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id),
                    INDEX idx_transfer_number (transfer_number),
                    INDEX idx_status (status),
                    INDEX idx_user_id (user_id),
                    INDEX idx_from_warehouse (from_warehouse),
                    INDEX idx_to_warehouse (to_warehouse),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 11. Serial Number Transfer Items
            'serial_number_transfer_items': '''
                CREATE TABLE IF NOT EXISTS serial_number_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial_transfer_id INT NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_name VARCHAR(200),
                    unit_of_measure VARCHAR(10) DEFAULT 'EA',
                    from_warehouse_code VARCHAR(10) NOT NULL,
                    to_warehouse_code VARCHAR(10) NOT NULL,
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (serial_transfer_id) REFERENCES serial_number_transfers(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_item_per_transfer (serial_transfer_id, item_code),
                    INDEX idx_serial_transfer_id (serial_transfer_id),
                    INDEX idx_item_code (item_code),
                    INDEX idx_qc_status (qc_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 12. Serial Number Transfer Serials
            'serial_number_transfer_serials': '''
                CREATE TABLE IF NOT EXISTS serial_number_transfer_serials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_item_id INT NOT NULL,
                    serial_number VARCHAR(100) NOT NULL,
                    internal_serial_number VARCHAR(100) NOT NULL,
                    system_serial_number INT,
                    is_validated BOOLEAN DEFAULT FALSE,
                    validation_error TEXT,
                    manufacturing_date DATE,
                    expiry_date DATE,
                    admission_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (transfer_item_id) REFERENCES serial_number_transfer_items(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_serial_per_item (transfer_item_id, serial_number),
                    INDEX idx_transfer_item_id (transfer_item_id),
                    INDEX idx_serial_number (serial_number),
                    INDEX idx_is_validated (is_validated),
                    INDEX idx_internal_serial_number (internal_serial_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 13. Pick Lists
            'pick_lists': '''
                CREATE TABLE IF NOT EXISTS pick_lists (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    absolute_entry INT,
                    name VARCHAR(50) NOT NULL,
                    owner_code INT,
                    owner_name VARCHAR(100),
                    pick_date TIMESTAMP NULL,
                    remarks TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    object_type VARCHAR(10) DEFAULT '156',
                    use_base_units VARCHAR(5) DEFAULT 'tNO',
                    sales_order_number VARCHAR(20),
                    pick_list_number VARCHAR(20),
                    user_id INT NOT NULL,
                    approver_id INT,
                    priority VARCHAR(10) DEFAULT 'normal',
                    warehouse_code VARCHAR(10),
                    customer_code VARCHAR(20),
                    customer_name VARCHAR(100),
                    total_items INT DEFAULT 0,
                    picked_items INT DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (approver_id) REFERENCES users(id),
                    INDEX idx_name (name),
                    INDEX idx_status (status),
                    INDEX idx_user_id (user_id),
                    INDEX idx_absolute_entry (absolute_entry)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 14. Serial Item Transfers
            'serial_item_transfers': '''
                CREATE TABLE IF NOT EXISTS serial_item_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_number VARCHAR(50) NOT NULL UNIQUE,
                    sap_document_number VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INT NOT NULL,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(10) NOT NULL,
                    to_warehouse VARCHAR(10) NOT NULL,
                    priority VARCHAR(10) DEFAULT 'normal',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_transfer_number (transfer_number),
                    INDEX idx_status (status),
                    INDEX idx_user_id (user_id),
                    INDEX idx_qc_approver_id (qc_approver_id),
                    INDEX idx_from_warehouse (from_warehouse),
                    INDEX idx_to_warehouse (to_warehouse),
                    INDEX idx_priority (priority),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 15. Serial Item Transfer Items
            'serial_item_transfer_items': '''
                CREATE TABLE IF NOT EXISTS serial_item_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    serial_item_transfer_id INT NOT NULL,
                    serial_number VARCHAR(100) NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_description VARCHAR(200) NOT NULL,
                    warehouse_code VARCHAR(10) NOT NULL,
                    quantity INT DEFAULT 1,
                    unit_of_measure VARCHAR(10) DEFAULT 'EA',
                    from_warehouse_code VARCHAR(10) NOT NULL,
                    to_warehouse_code VARCHAR(10) NOT NULL,
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    qc_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (serial_item_transfer_id) REFERENCES serial_item_transfers(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_serial_per_transfer (serial_item_transfer_id, serial_number),
                    INDEX idx_serial_item_transfer_id (serial_item_transfer_id),
                    INDEX idx_serial_number (serial_number),
                    INDEX idx_item_code (item_code),
                    INDEX idx_qc_status (qc_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 16. Direct Inventory Transfers
            'direct_inventory_transfers': '''
                CREATE TABLE IF NOT EXISTS direct_inventory_transfers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transfer_number VARCHAR(50) NOT NULL UNIQUE,
                    sap_document_number VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'draft',
                    user_id INT NOT NULL,
                    qc_approver_id INT,
                    qc_approved_at TIMESTAMP NULL,
                    qc_notes TEXT,
                    from_warehouse VARCHAR(50),
                    to_warehouse VARCHAR(50),
                    from_bin VARCHAR(50),
                    to_bin VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
                    FOREIGN KEY (qc_approver_id) REFERENCES users(id) ON DELETE SET NULL,
                    INDEX idx_transfer_number (transfer_number),
                    INDEX idx_status (status),
                    INDEX idx_user_id (user_id),
                    INDEX idx_qc_approver_id (qc_approver_id),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''',
            
            # 17. Direct Inventory Transfer Items
            'direct_inventory_transfer_items': '''
                CREATE TABLE IF NOT EXISTS direct_inventory_transfer_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    direct_inventory_transfer_id INT NOT NULL,
                    item_code VARCHAR(50) NOT NULL,
                    item_description VARCHAR(200),
                    barcode VARCHAR(100),
                    item_type VARCHAR(20),
                    quantity DECIMAL(15,4) DEFAULT 1,
                    unit_of_measure VARCHAR(10) DEFAULT 'EA',
                    from_warehouse_code VARCHAR(50),
                    to_warehouse_code VARCHAR(50),
                    from_bin_code VARCHAR(50),
                    to_bin_code VARCHAR(50),
                    batch_number VARCHAR(100),
                    serial_numbers TEXT,
                    qc_status VARCHAR(20) DEFAULT 'pending',
                    validation_status VARCHAR(20) DEFAULT 'pending',
                    validation_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (direct_inventory_transfer_id) REFERENCES direct_inventory_transfers(id) ON DELETE CASCADE,
                    INDEX idx_direct_inventory_transfer_id (direct_inventory_transfer_id),
                    INDEX idx_item_code (item_code),
                    INDEX idx_barcode (barcode),
                    INDEX idx_qc_status (qc_status),
                    INDEX idx_validation_status (validation_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            '''
        }
        
        logger.info("=" * 80)
        logger.info("Creating WMS Database Tables")
        logger.info("=" * 80)
        
        for table_name, create_sql in tables.items():
            try:
                logger.info(f"📝 Creating table: {table_name}...")
                self.cursor.execute(create_sql)
                self.connection.commit()
                logger.info(f"✅ Table '{table_name}' created successfully")
            except Exception as e:
                logger.error(f"❌ Error creating table '{table_name}': {e}")
                return False
        
        logger.info("=" * 80)
        logger.info("✅ All tables created successfully!")
        logger.info("=" * 80)
        return True
    
    def create_default_admin(self):
        """Create default admin user if not exists"""
        try:
            # Check if admin exists
            self.cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if self.cursor.fetchone():
                logger.info("ℹ️  Admin user already exists")
                return True
            
            # Create admin user
            admin_password = generate_password_hash('admin123')
            self.cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, first_name, last_name, active)
                VALUES ('admin', 'admin@wms.local', %s, 'admin', 'System', 'Administrator', TRUE)
            """, (admin_password,))
            
            self.connection.commit()
            logger.info("✅ Default admin user created (username: admin, password: admin123)")
            logger.warning("⚠️  Please change the admin password after first login!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating admin user: {e}")
            return False
    
    def run(self):
        """Run the complete migration"""
        logger.info("\n" + "=" * 80)
        logger.info("MySQL WMS Consolidated Migration")
        logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80 + "\n")
        
        # Get database config
        config = self.get_database_config()
        
        # Connect to database
        if not self.connect(config):
            logger.error("Migration failed - cannot connect to database")
            return False
        
        # Create all tables
        if not self.create_all_tables():
            logger.error("Migration failed - error creating tables")
            return False
        
        # Create default admin
        if not self.create_default_admin():
            logger.warning("Warning - default admin user not created")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 Migration Completed Successfully!")
        logger.info("=" * 80)
        logger.info("\nTables created:")
        logger.info("  ✓ Core: users, branches, document_number_series")
        logger.info("  ✓ GRPO: grpo_documents, grpo_items, grpo_serial_numbers, grpo_batch_numbers")
        logger.info("  ✓ Transfers: inventory_transfers, serial_number_transfers, serial_item_transfers")
        logger.info("  ✓ Pick Lists: pick_lists")
        logger.info("=" * 80 + "\n")
        
        return True
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("📤 Database connection closed")

if __name__ == "__main__":
    migration = MySQLConsolidatedMigration()
    
    try:
        success = migration.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        migration.close()
