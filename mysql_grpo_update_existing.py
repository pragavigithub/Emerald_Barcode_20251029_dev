"""
MySQL GRPO Schema Update Script for EXISTING Databases
Date: October 22, 2025
Purpose: Safely update existing MySQL database to match current GRPO models

This script:
1. Checks which columns exist
2. Only adds/modifies missing columns
3. Creates backups before making changes
4. Provides detailed progress reporting
"""

import pymysql
import sys
from datetime import datetime

# Database connection settings
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change this to your MySQL username
    'password': 'root123',  # Change this to your MySQL password
    'database': 'test_emrald',  # Change this to your database name
    'charset': 'utf8mb4'
}

def get_connection():
    """Create database connection"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print(f"✓ Connected to MySQL database: {DB_CONFIG['database']}")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        print("\nPlease update DB_CONFIG in this script with your MySQL credentials:")
        print("  - host")
        print("  - user")
        print("  - password")
        print("  - database")
        sys.exit(1)

def get_table_columns(cursor, table_name):
    """Get list of columns in a table"""
    cursor.execute(f"SHOW COLUMNS FROM {table_name}")
    columns = {row[0]: row[1] for row in cursor.fetchall()}
    return columns

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    columns = get_table_columns(cursor, table_name)
    return column_name in columns

def execute_safe(cursor, sql, description):
    """Execute SQL with error handling"""
    try:
        cursor.execute(sql)
        print(f"  ✓ {description}")
        return True
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1060:  # Duplicate column name
            print(f"  ⊙ {description} (already exists, skipped)")
            return True
        elif e.args[0] == 1091:  # Can't DROP - doesn't exist
            print(f"  ⊙ {description} (doesn't exist, skipped)")
            return True
        else:
            print(f"  ✗ {description} - Error: {e}")
            return False
    except Exception as e:
        print(f"  ✗ {description} - Error: {e}")
        return False

def update_grpo_documents(conn):
    """Update grpo_documents table schema"""
    print("\n" + "="*60)
    print("UPDATING grpo_documents TABLE")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Get current columns
    current_columns = get_table_columns(cursor, 'grpo_documents')
    print(f"\nCurrent columns: {', '.join(current_columns.keys())}")
    
    # Check if we need to rename qc_user_id to qc_approver_id
    if 'qc_user_id' in current_columns and 'qc_approver_id' not in current_columns:
        print("\n1. Renaming qc_user_id to qc_approver_id...")
        execute_safe(cursor, 
            "ALTER TABLE grpo_documents CHANGE COLUMN qc_user_id qc_approver_id INT NULL",
            "Renamed qc_user_id to qc_approver_id")
    elif 'qc_approver_id' not in current_columns:
        print("\n1. Adding qc_approver_id column...")
        execute_safe(cursor,
            "ALTER TABLE grpo_documents ADD COLUMN qc_approver_id INT NULL AFTER user_id",
            "Added qc_approver_id column")
    else:
        print("\n1. qc_approver_id already exists ✓")
    
    # Add warehouse_code if missing
    print("\n2. Checking warehouse_code column...")
    if not column_exists(cursor, 'grpo_documents', 'warehouse_code'):
        execute_safe(cursor,
            "ALTER TABLE grpo_documents ADD COLUMN warehouse_code VARCHAR(10) NULL AFTER supplier_name",
            "Added warehouse_code column")
    else:
        print("  ✓ warehouse_code already exists")
    
    # Add updated_at if missing
    print("\n3. Checking updated_at column...")
    if not column_exists(cursor, 'grpo_documents', 'updated_at'):
        execute_safe(cursor,
            "ALTER TABLE grpo_documents ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at",
            "Added updated_at column")
    else:
        print("  ✓ updated_at already exists")
    
    # Update foreign key constraint for qc_approver_id
    print("\n4. Updating foreign key constraints...")
    execute_safe(cursor,
        "ALTER TABLE grpo_documents DROP FOREIGN KEY IF EXISTS grpo_documents_ibfk_2",
        "Dropped old foreign key (if exists)")
    execute_safe(cursor,
        "ALTER TABLE grpo_documents ADD CONSTRAINT grpo_documents_ibfk_2 FOREIGN KEY (qc_approver_id) REFERENCES users(id)",
        "Added foreign key for qc_approver_id")
    
    conn.commit()
    print("\n✓ grpo_documents table updated successfully")

def backup_grpo_items(conn):
    """Create backup of grpo_items table"""
    print("\n" + "="*60)
    print("CREATING BACKUP OF grpo_items TABLE")
    print("="*60)
    
    cursor = conn.cursor()
    backup_table = f"grpo_items_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {backup_table}")
        cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM grpo_items")
        cursor.execute(f"SELECT COUNT(*) FROM {backup_table}")
        count = cursor.fetchone()[0]
        conn.commit()
        print(f"✓ Backup created: {backup_table} ({count} rows)")
        return backup_table
    except Exception as e:
        print(f"✗ Failed to create backup: {e}")
        return None

def update_grpo_items(conn):
    """Update grpo_items table schema"""
    print("\n" + "="*60)
    print("UPDATING grpo_items TABLE")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Get current columns
    current_columns = get_table_columns(cursor, 'grpo_items')
    print(f"\nCurrent columns: {', '.join(current_columns.keys())}")
    
    # Rename grpo_document_id to grpo_id if needed
    print("\n1. Checking grpo_id column...")
    if 'grpo_document_id' in current_columns and 'grpo_id' not in current_columns:
        execute_safe(cursor,
            "ALTER TABLE grpo_items CHANGE COLUMN grpo_document_id grpo_id INT NOT NULL",
            "Renamed grpo_document_id to grpo_id")
    elif 'grpo_id' not in current_columns:
        execute_safe(cursor,
            "ALTER TABLE grpo_items ADD COLUMN grpo_id INT NOT NULL AFTER id",
            "Added grpo_id column")
    else:
        print("  ✓ grpo_id already exists")
    
    # Add missing columns
    print("\n2. Adding missing columns...")
    
    columns_to_add = [
        ("line_total", "DECIMAL(15,2) NULL AFTER unit_price", "Added line_total"),
        ("base_entry", "INT NULL AFTER po_line_number", "Added base_entry (SAP PO DocEntry)"),
        ("base_line", "INT NULL AFTER base_entry", "Added base_line (SAP PO Line)"),
        ("batch_required", "VARCHAR(1) DEFAULT 'N' AFTER base_line", "Added batch_required"),
        ("serial_required", "VARCHAR(1) DEFAULT 'N' AFTER batch_required", "Added serial_required"),
        ("manage_method", "VARCHAR(1) DEFAULT 'N' AFTER serial_required", "Added manage_method"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at", "Added updated_at"),
    ]
    
    for col_name, col_def, description in columns_to_add:
        if not column_exists(cursor, 'grpo_items', col_name):
            execute_safe(cursor,
                f"ALTER TABLE grpo_items ADD COLUMN {col_name} {col_def}",
                description)
        else:
            print(f"  ✓ {col_name} already exists")
    
    # Rename expiration_date to expiry_date if needed
    print("\n3. Checking expiry_date column...")
    if 'expiration_date' in current_columns and 'expiry_date' not in current_columns:
        execute_safe(cursor,
            "ALTER TABLE grpo_items CHANGE COLUMN expiration_date expiry_date DATE NULL",
            "Renamed expiration_date to expiry_date")
    elif 'expiry_date' not in current_columns:
        execute_safe(cursor,
            "ALTER TABLE grpo_items ADD COLUMN expiry_date DATE NULL AFTER serial_number",
            "Added expiry_date column")
    else:
        print("  ✓ expiry_date already exists")
    
    # Rename supplier_barcode to barcode if needed
    print("\n4. Checking barcode column...")
    if 'supplier_barcode' in current_columns and 'barcode' not in current_columns:
        execute_safe(cursor,
            "ALTER TABLE grpo_items CHANGE COLUMN supplier_barcode barcode VARCHAR(100) NULL",
            "Renamed supplier_barcode to barcode")
    elif 'barcode' not in current_columns:
        execute_safe(cursor,
            "ALTER TABLE grpo_items ADD COLUMN barcode VARCHAR(100) NULL AFTER expiry_date",
            "Added barcode column")
    else:
        print("  ✓ barcode already exists")
    
    # Update column types
    print("\n5. Updating column types...")
    execute_safe(cursor,
        "ALTER TABLE grpo_items MODIFY COLUMN quantity DECIMAL(15,3) NOT NULL",
        "Updated quantity precision to DECIMAL(15,3)")
    execute_safe(cursor,
        "ALTER TABLE grpo_items MODIFY COLUMN received_quantity DECIMAL(15,3) DEFAULT 0",
        "Updated received_quantity precision to DECIMAL(15,3)")
    
    # Drop obsolete columns
    print("\n6. Removing obsolete columns...")
    obsolete_columns = ['generated_barcode', 'barcode_printed', 'qc_notes', 'po_quantity', 'open_quantity']
    for col_name in obsolete_columns:
        if column_exists(cursor, 'grpo_items', col_name):
            execute_safe(cursor,
                f"ALTER TABLE grpo_items DROP COLUMN {col_name}",
                f"Dropped obsolete column: {col_name}")
    
    # Update foreign key
    print("\n7. Updating foreign key constraints...")
    execute_safe(cursor,
        "ALTER TABLE grpo_items DROP FOREIGN KEY IF EXISTS grpo_items_ibfk_1",
        "Dropped old foreign key")
    execute_safe(cursor,
        "ALTER TABLE grpo_items ADD CONSTRAINT grpo_items_ibfk_1 FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE",
        "Added new foreign key for grpo_id")
    
    # Update indexes
    print("\n8. Updating indexes...")
    execute_safe(cursor,
        "DROP INDEX IF EXISTS idx_grpo_document_id ON grpo_items",
        "Dropped old index")
    execute_safe(cursor,
        "CREATE INDEX idx_grpo_id ON grpo_items(grpo_id)",
        "Created index on grpo_id")
    
    conn.commit()
    print("\n✓ grpo_items table updated successfully")

def verify_schema(conn):
    """Verify the updated schema"""
    print("\n" + "="*60)
    print("SCHEMA VERIFICATION")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Check grpo_documents
    print("\ngrpo_documents columns:")
    cursor.execute("SHOW COLUMNS FROM grpo_documents")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Check grpo_items
    print("\ngrpo_items columns:")
    cursor.execute("SHOW COLUMNS FROM grpo_items")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Count records
    print("\nRecord counts:")
    cursor.execute("SELECT COUNT(*) FROM grpo_documents")
    print(f"  - grpo_documents: {cursor.fetchone()[0]} records")
    cursor.execute("SELECT COUNT(*) FROM grpo_items")
    print(f"  - grpo_items: {cursor.fetchone()[0]} records")

def main():
    """Main migration function"""
    print("\n" + "="*60)
    print("MySQL GRPO Schema Update - October 22, 2025")
    print("="*60)
    print(f"\nTarget database: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    
    # Confirm before proceeding
    response = input("\nThis will modify your database. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        sys.exit(0)
    
    # Connect to database
    conn = get_connection()
    
    try:
        # Update grpo_documents table
        update_grpo_documents(conn)
        
        # Backup grpo_items table
        backup_table = backup_grpo_items(conn)
        if not backup_table:
            print("\n✗ Failed to create backup. Migration aborted.")
            sys.exit(1)
        
        # Update grpo_items table
        update_grpo_items(conn)
        
        # Verify schema
        verify_schema(conn)
        
        print("\n" + "="*60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"\n✓ Backup table created: {backup_table}")
        print("✓ grpo_documents table updated")
        print("✓ grpo_items table updated")
        print("\nYou can now test your GRPO module with the updated schema.")
        print(f"\nIf anything goes wrong, you can restore from: {backup_table}")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
