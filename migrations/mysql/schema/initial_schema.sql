-- ============================================================================
-- Warehouse Management System - Initial MySQL Schema
-- ============================================================================
-- Generated: 2025-10-13
-- Database: MySQL 8.0+
-- Description: Complete initial schema for all modules
-- ============================================================================

-- This schema represents the current state of the database as defined by
-- SQLAlchemy models. It includes all tables for:
-- - User management and authentication
-- - GRPO (Goods Receipt PO) module
-- - Inventory Transfer module  
-- - Multi GRN Creation module
-- - Pick List module
-- - Serial Number Tracking
-- - Supporting tables

-- ============================================================================
-- CORE TABLES - User Management & Authentication
-- ============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    branch_id VARCHAR(20),
    branch_name VARCHAR(100),
    default_branch_id VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    must_change_password BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    permissions JSON,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_branch_id (branch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Branches table
CREATE TABLE IF NOT EXISTS branches (
    id VARCHAR(20) PRIMARY KEY,
    branch_code VARCHAR(50) UNIQUE NOT NULL,
    branch_name VARCHAR(100) NOT NULL,
    name VARCHAR(100),
    description TEXT,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    manager_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    sap_branch_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_branch_code (branch_code),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- User Sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_user_id (user_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Password Reset Tokens table
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    token VARCHAR(256) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP NULL,
    created_by INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_token (token),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- GRPO MODULE - Goods Receipt Purchase Order
-- ============================================================================

-- GRPO Documents table
CREATE TABLE IF NOT EXISTS grpo_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_num VARCHAR(50) UNIQUE,
    po_doc_entry INT,
    po_doc_num INT,
    vendor_code VARCHAR(50),
    vendor_name VARCHAR(200),
    doc_date DATE,
    posting_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    qc_status VARCHAR(20),
    qc_approved_by INT,
    qc_approved_at TIMESTAMP NULL,
    qc_notes TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP NULL,
    total_amount DECIMAL(18, 6),
    remarks TEXT,
    sap_doc_entry INT,
    sap_doc_num INT,
    sync_status VARCHAR(20),
    sync_error TEXT,
    synced_at TIMESTAMP NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (qc_approved_by) REFERENCES users(id),
    INDEX idx_doc_num (doc_num),
    INDEX idx_po_doc_entry (po_doc_entry),
    INDEX idx_status (status),
    INDEX idx_qc_status (qc_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- GRPO Items table
CREATE TABLE IF NOT EXISTS grpo_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_id INT NOT NULL,
    line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    quantity DECIMAL(18, 6),
    warehouse_code VARCHAR(20),
    bin_location VARCHAR(50),
    batch_number VARCHAR(50),
    serial_numbers JSON,
    unit_price DECIMAL(18, 6),
    line_total DECIMAL(18, 6),
    qc_status VARCHAR(20),
    qc_notes TEXT,
    po_line_num INT,
    FOREIGN KEY (grpo_id) REFERENCES grpo_documents(id) ON DELETE CASCADE,
    INDEX idx_grpo_id (grpo_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- INVENTORY TRANSFER MODULE
-- ============================================================================

-- Inventory Transfers table
CREATE TABLE IF NOT EXISTS inventory_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_num VARCHAR(50) UNIQUE,
    transfer_request_doc_entry INT,
    from_warehouse VARCHAR(20),
    to_warehouse VARCHAR(20),
    from_bin VARCHAR(50),
    to_bin VARCHAR(50),
    doc_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    qc_status VARCHAR(20),
    qc_approved_by INT,
    qc_approved_at TIMESTAMP NULL,
    qc_notes TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP NULL,
    remarks TEXT,
    sap_doc_entry INT,
    sap_doc_num INT,
    sync_status VARCHAR(20),
    sync_error TEXT,
    synced_at TIMESTAMP NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (qc_approved_by) REFERENCES users(id),
    INDEX idx_doc_num (doc_num),
    INDEX idx_status (status),
    INDEX idx_qc_status (qc_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Inventory Transfer Items table
CREATE TABLE IF NOT EXISTS inventory_transfer_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_id INT NOT NULL,
    line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    quantity DECIMAL(18, 6),
    from_warehouse VARCHAR(20),
    to_warehouse VARCHAR(20),
    from_bin VARCHAR(50),
    to_bin VARCHAR(50),
    batch_number VARCHAR(50),
    serial_numbers JSON,
    qc_status VARCHAR(20),
    qc_notes TEXT,
    FOREIGN KEY (transfer_id) REFERENCES inventory_transfers(id) ON DELETE CASCADE,
    INDEX idx_transfer_id (transfer_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- MULTI GRN MODULE - Multiple GRN Creation
-- ============================================================================

-- Multi GRN Batches table
CREATE TABLE IF NOT EXISTS multi_grn_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_num VARCHAR(50) UNIQUE,
    user_id INT NOT NULL,
    customer_code VARCHAR(50),
    customer_name VARCHAR(200),
    status VARCHAR(20) DEFAULT 'draft',
    total_pos INT DEFAULT 0,
    total_grns_created INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    error_log TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_customer_code (customer_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Multi GRN PO Links table
CREATE TABLE IF NOT EXISTS multi_grn_po_links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    po_doc_entry INT,
    po_doc_num INT,
    po_card_code VARCHAR(50),
    po_card_name VARCHAR(200),
    po_doc_date DATE,
    po_doc_total DECIMAL(18, 6),
    status VARCHAR(20) DEFAULT 'selected',
    sap_grn_doc_entry INT,
    sap_grn_doc_num INT,
    posted_at TIMESTAMP NULL,
    error_message TEXT,
    FOREIGN KEY (batch_id) REFERENCES multi_grn_batches(id) ON DELETE CASCADE,
    INDEX idx_batch_id (batch_id),
    INDEX idx_po_doc_entry (po_doc_entry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Multi GRN Line Selections table
CREATE TABLE IF NOT EXISTS multi_grn_line_selections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    po_link_id INT NOT NULL,
    po_line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    ordered_quantity DECIMAL(18, 6),
    open_quantity DECIMAL(18, 6),
    selected_quantity DECIMAL(18, 6),
    warehouse_code VARCHAR(20),
    unit_price DECIMAL(18, 6),
    line_status VARCHAR(20),
    inventory_type VARCHAR(20),
    FOREIGN KEY (po_link_id) REFERENCES multi_grn_po_links(id) ON DELETE CASCADE,
    INDEX idx_po_link_id (po_link_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- PICK LIST MODULE
-- ============================================================================

-- Pick Lists table
CREATE TABLE IF NOT EXISTS pick_lists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pick_list_no VARCHAR(50) UNIQUE,
    sap_pick_list_no INT,
    sales_order_doc_entry INT,
    sales_order_doc_num INT,
    customer_code VARCHAR(50),
    customer_name VARCHAR(200),
    pick_date DATE,
    status VARCHAR(20) DEFAULT 'open',
    remarks TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    picked_by INT,
    picked_at TIMESTAMP NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (picked_by) REFERENCES users(id),
    INDEX idx_pick_list_no (pick_list_no),
    INDEX idx_sales_order_doc_entry (sales_order_doc_entry),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Pick List Items table
CREATE TABLE IF NOT EXISTS pick_list_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pick_list_id INT NOT NULL,
    line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    ordered_quantity DECIMAL(18, 6),
    picked_quantity DECIMAL(18, 6),
    warehouse_code VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE,
    INDEX idx_pick_list_id (pick_list_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Pick List Lines table
CREATE TABLE IF NOT EXISTS pick_list_lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pick_list_id INT NOT NULL,
    absolute_entry INT,
    line_number INT,
    order_entry INT,
    order_line INT,
    order_number INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    warehouse VARCHAR(20),
    picked_quantity DECIMAL(18, 6),
    released_quantity DECIMAL(18, 6),
    previously_released_qty DECIMAL(18, 6),
    base_line_number INT,
    series_string VARCHAR(100),
    FOREIGN KEY (pick_list_id) REFERENCES pick_lists(id) ON DELETE CASCADE,
    INDEX idx_pick_list_id (pick_list_id),
    INDEX idx_absolute_entry (absolute_entry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Pick List Bin Allocations table
CREATE TABLE IF NOT EXISTS pick_list_bin_allocations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pick_list_line_id INT NOT NULL,
    bin_abs_entry INT,
    bin_code VARCHAR(50),
    quantity DECIMAL(18, 6),
    serial_and_batch_numbers_base_line INT,
    base_line_number INT,
    allow_negative_quantity BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (pick_list_line_id) REFERENCES pick_list_lines(id) ON DELETE CASCADE,
    INDEX idx_pick_list_line_id (pick_list_line_id),
    INDEX idx_bin_code (bin_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SERIAL NUMBER TRACKING MODULE
-- ============================================================================

-- Serial Number Transfers table
CREATE TABLE IF NOT EXISTS serial_number_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_num VARCHAR(50) UNIQUE,
    from_warehouse VARCHAR(20),
    to_warehouse VARCHAR(20),
    doc_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP NULL,
    remarks TEXT,
    sap_doc_entry INT,
    sap_doc_num INT,
    sync_status VARCHAR(20),
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_doc_num (doc_num),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Serial Number Transfer Items table
CREATE TABLE IF NOT EXISTS serial_number_transfer_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_id INT NOT NULL,
    line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    quantity DECIMAL(18, 6),
    from_warehouse VARCHAR(20),
    to_warehouse VARCHAR(20),
    FOREIGN KEY (transfer_id) REFERENCES serial_number_transfers(id) ON DELETE CASCADE,
    INDEX idx_transfer_id (transfer_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Serial Number Transfer Serials table
CREATE TABLE IF NOT EXISTS serial_number_transfer_serials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_item_id INT NOT NULL,
    serial_number VARCHAR(100),
    item_code VARCHAR(50),
    system_serial_number VARCHAR(100),
    internal_serial_number VARCHAR(100),
    mfr_serial_number VARCHAR(100),
    lot_number VARCHAR(50),
    expiry_date DATE,
    manufacturing_date DATE,
    admission_date DATE,
    notes TEXT,
    FOREIGN KEY (transfer_item_id) REFERENCES serial_number_transfer_items(id) ON DELETE CASCADE,
    INDEX idx_transfer_item_id (transfer_item_id),
    INDEX idx_serial_number (serial_number),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Serial Item Transfers table
CREATE TABLE IF NOT EXISTS serial_item_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_num VARCHAR(50) UNIQUE,
    from_warehouse VARCHAR(20),
    to_warehouse VARCHAR(20),
    doc_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    submitted_at TIMESTAMP NULL,
    remarks TEXT,
    sap_doc_entry INT,
    sap_doc_num INT,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_doc_num (doc_num),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Serial Item Transfer Items table
CREATE TABLE IF NOT EXISTS serial_item_transfer_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_id INT NOT NULL,
    line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    quantity DECIMAL(18, 6),
    from_warehouse VARCHAR(20),
    to_warehouse VARCHAR(20),
    serial_numbers JSON,
    FOREIGN KEY (transfer_id) REFERENCES serial_item_transfers(id) ON DELETE CASCADE,
    INDEX idx_transfer_id (transfer_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SUPPORTING TABLES
-- ============================================================================

-- Bin Locations table
CREATE TABLE IF NOT EXISTS bin_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    warehouse_code VARCHAR(20),
    bin_code VARCHAR(50),
    bin_name VARCHAR(100),
    abs_entry INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_warehouse_bin (warehouse_code, bin_code),
    INDEX idx_warehouse_code (warehouse_code),
    INDEX idx_bin_code (bin_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bin Items table
CREATE TABLE IF NOT EXISTS bin_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bin_location_id INT NOT NULL,
    item_code VARCHAR(50),
    item_name VARCHAR(200),
    quantity DECIMAL(18, 6),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (bin_location_id) REFERENCES bin_locations(id) ON DELETE CASCADE,
    INDEX idx_bin_location_id (bin_location_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bin Scanning Logs table
CREATE TABLE IF NOT EXISTS bin_scanning_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    bin_location_id INT,
    item_code VARCHAR(50),
    scanned_quantity DECIMAL(18, 6),
    scan_type VARCHAR(20),
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (bin_location_id) REFERENCES bin_locations(id),
    INDEX idx_user_id (user_id),
    INDEX idx_scanned_at (scanned_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Barcode Labels table
CREATE TABLE IF NOT EXISTS barcode_labels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50),
    label_type VARCHAR(50),
    barcode_data VARCHAR(200),
    generated_by INT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(id),
    INDEX idx_item_code (item_code),
    INDEX idx_barcode_data (barcode_data)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- QR Code Labels table
CREATE TABLE IF NOT EXISTS qr_code_labels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_code VARCHAR(50),
    qr_data TEXT,
    label_type VARCHAR(50),
    generated_by INT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (generated_by) REFERENCES users(id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Document Number Series table
CREATE TABLE IF NOT EXISTS document_number_series (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module VARCHAR(50),
    prefix VARCHAR(10),
    current_number INT DEFAULT 0,
    padding INT DEFAULT 4,
    UNIQUE KEY unique_module_prefix (module, prefix),
    INDEX idx_module (module)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Inventory Counts table
CREATE TABLE IF NOT EXISTS inventory_counts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    count_num VARCHAR(50) UNIQUE,
    warehouse_code VARCHAR(20),
    count_date DATE,
    status VARCHAR(20) DEFAULT 'open',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_count_num (count_num),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Inventory Count Items table
CREATE TABLE IF NOT EXISTS inventory_count_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    count_id INT NOT NULL,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    system_quantity DECIMAL(18, 6),
    counted_quantity DECIMAL(18, 6),
    variance DECIMAL(18, 6),
    FOREIGN KEY (count_id) REFERENCES inventory_counts(id) ON DELETE CASCADE,
    INDEX idx_count_id (count_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sales Orders table (for pick list integration)
CREATE TABLE IF NOT EXISTS sales_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_entry INT UNIQUE,
    doc_num INT,
    customer_code VARCHAR(50),
    customer_name VARCHAR(200),
    doc_date DATE,
    doc_total DECIMAL(18, 6),
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_doc_entry (doc_entry),
    INDEX idx_customer_code (customer_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sales Order Lines table
CREATE TABLE IF NOT EXISTS sales_order_lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    line_num INT,
    item_code VARCHAR(50),
    item_description VARCHAR(200),
    quantity DECIMAL(18, 6),
    warehouse_code VARCHAR(20),
    FOREIGN KEY (order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
    INDEX idx_order_id (order_id),
    INDEX idx_item_code (item_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default branch
INSERT IGNORE INTO branches (id, branch_code, branch_name, name, is_active, is_default) 
VALUES ('BR001', 'BR001', 'Main Branch', 'Main Branch', TRUE, TRUE);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================