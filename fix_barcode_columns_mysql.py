#!/usr/bin/env python3
"""
MySQL Migration Script - Fix Barcode Column Size
=================================================
Issue: Barcode columns are VARCHAR(100-200) but need to be TEXT
       to store base64-encoded PNG images (~5000 characters)

Error: (1406, "Data too long for column 'barcode' at row 1")

This script will:
1. Connect to your MySQL database
2. Change barcode columns from VARCHAR to TEXT
3. Verify the changes were successful
"""

import pymysql
import sys
from datetime import datetime

# ========================================
# DATABASE CONFIGURATION
# ========================================
# UPDATE THESE WITH YOUR MySQL CREDENTIALS
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Add your MySQL password here
    'database': 'wms_db',
    'charset': 'utf8mb4'
}

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def check_column_type(cursor, table_name, column_name):
    """Check current data type of a column"""
    cursor.execute(f"""
        SELECT DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s 
        AND COLUMN_NAME = %s
    """, (DB_CONFIG['database'], table_name, column_name))
    
    result = cursor.fetchone()
    if result:
        data_type = result[0]
        max_length = result[1]
        if max_length:
            return f"{data_type}({max_length})"
        return data_type
    return None

def fix_barcode_columns():
    """Main function to fix barcode columns"""
    
    print_header("GRPO Barcode Column Fix - MySQL Migration")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DB_CONFIG['database']}")
    print()
    
    # Tables and columns to fix
    tables_to_fix = [
        ('grpo_items', 'barcode'),
        ('grpo_serial_numbers', 'barcode'),
        ('grpo_batch_numbers', 'barcode')
    ]
    
    try:
        # Connect to database
        print_info("Connecting to MySQL database...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print_success("Connected successfully!")
        
        # Check current column types
        print_header("Current Column Types")
        for table, column in tables_to_fix:
            current_type = check_column_type(cursor, table, column)
            if current_type:
                print(f"  {table}.{column}: {current_type}")
            else:
                print_error(f"Column {table}.{column} not found!")
        
        # Ask for confirmation
        print()
        print_info("This script will change all barcode columns to TEXT type")
        print_info("TEXT can store up to 65,535 characters (enough for base64 images)")
        print()
        
        confirmation = input("Do you want to proceed? (yes/no): ").strip().lower()
        if confirmation not in ['yes', 'y']:
            print_info("Migration cancelled by user")
            return
        
        # Apply fixes
        print_header("Applying Fixes")
        
        for table, column in tables_to_fix:
            try:
                print()
                print_info(f"Fixing {table}.{column}...")
                
                # Check if table exists
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if not cursor.fetchone():
                    print_error(f"Table {table} does not exist, skipping...")
                    continue
                
                # Check if column exists
                cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{column}'")
                if not cursor.fetchone():
                    print_error(f"Column {column} does not exist in {table}, skipping...")
                    continue
                
                # Alter column to TEXT
                alter_sql = f"ALTER TABLE {table} MODIFY COLUMN {column} TEXT"
                cursor.execute(alter_sql)
                connection.commit()
                
                # Verify the change
                new_type = check_column_type(cursor, table, column)
                if new_type == 'text':
                    print_success(f"{table}.{column} changed to TEXT successfully!")
                else:
                    print_error(f"{table}.{column} type is {new_type}, expected 'text'")
                    
            except pymysql.Error as e:
                print_error(f"Error fixing {table}.{column}: {e}")
                connection.rollback()
        
        # Verify all changes
        print_header("Verification - New Column Types")
        all_success = True
        for table, column in tables_to_fix:
            new_type = check_column_type(cursor, table, column)
            if new_type:
                status = "✅" if new_type == 'text' else "❌"
                print(f"  {status} {table}.{column}: {new_type}")
                if new_type != 'text':
                    all_success = False
            else:
                print(f"  ⚠️  {table}.{column}: Not found")
        
        print()
        if all_success:
            print_success("All barcode columns successfully updated to TEXT!")
            print_info("You can now add serial/batch numbers with barcodes")
        else:
            print_error("Some columns were not updated successfully")
            print_info("Please check the errors above and try again")
        
        # Close connection
        cursor.close()
        connection.close()
        print()
        print_info("Database connection closed")
        
    except pymysql.Error as e:
        print_error(f"Database error: {e}")
        print()
        print_info("Please check your database credentials in DB_CONFIG")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print()
    print("IMPORTANT: Before running this script:")
    print("1. Update DB_CONFIG with your MySQL credentials")
    print("2. Make sure MySQL server is running")
    print("3. Make sure you have a backup of your database")
    print()
    
    # Check if password is set
    if not DB_CONFIG['password']:
        print_error("Please set your MySQL password in DB_CONFIG")
        print_info("Edit this file and add your password on line 23")
        print()
        sys.exit(1)
    
    try:
        fix_barcode_columns()
        print()
        print_header("Migration Complete!")
        print()
        print("Next steps:")
        print("1. Restart your Flask application")
        print("2. Test adding serial/batch numbers")
        print("3. Verify barcodes are generated and saved")
        print()
        
    except KeyboardInterrupt:
        print()
        print_info("Migration cancelled by user (Ctrl+C)")
        sys.exit(0)
