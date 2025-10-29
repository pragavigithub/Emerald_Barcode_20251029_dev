-- MySQL Migration: SalesOrder Against Delivery Module
-- Date: 2025-10-23
-- Description: Add delivery_documents and delivery_items tables for tracking Sales Order deliveries

-- Table: delivery_documents
-- Purpose: Store delivery note drafts and submitted documents against Sales Orders
CREATE TABLE IF NOT EXISTS delivery_documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    so_doc_entry INT NOT NULL,
    so_doc_num INT NOT NULL,
    so_series INT NOT NULL,
    card_code VARCHAR(50),
    card_name VARCHAR(200),
    doc_currency VARCHAR(10),
    doc_date DATETIME,
    delivery_series INT,
    status VARCHAR(20) DEFAULT 'draft',
    sap_doc_entry INT,
    sap_doc_num INT,
    remarks TEXT,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    submitted_at DATETIME,
    last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_so_doc_entry (so_doc_entry),
    INDEX idx_sap_doc_entry (sap_doc_entry),
    INDEX idx_user_id (user_id),
    
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Delivery Note Documents - Local tracking';

-- Table: delivery_items
-- Purpose: Store individual line items for delivery notes with batch/serial tracking
CREATE TABLE IF NOT EXISTS delivery_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    delivery_id INT NOT NULL,
    line_number INT NOT NULL,
    base_line INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_description VARCHAR(200),
    warehouse_code VARCHAR(10),
    quantity DECIMAL(19,6) NOT NULL DEFAULT 0,
    open_quantity DECIMAL(19,6) DEFAULT 0,
    unit_price DECIMAL(19,6) DEFAULT 0,
    uom_code VARCHAR(10),
    batch_required BOOLEAN DEFAULT FALSE,
    serial_required BOOLEAN DEFAULT FALSE,
    batch_number VARCHAR(100),
    serial_number VARCHAR(100),
    expiry_date DATETIME,
    manufacture_date DATETIME,
    bin_location VARCHAR(50),
    project_code VARCHAR(50),
    cost_code VARCHAR(50),
    qr_code_generated BOOLEAN DEFAULT FALSE,
    warehouse_routing VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_delivery_id (delivery_id),
    INDEX idx_item_code (item_code),
    
    FOREIGN KEY (delivery_id) REFERENCES delivery_documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Delivery Note Line Items - Individual tracking';

-- Migration verification query
SELECT 
    'delivery_documents' AS table_name,
    COUNT(*) AS row_count,
    MAX(created_at) AS latest_record
FROM delivery_documents
UNION ALL
SELECT 
    'delivery_items' AS table_name,
    COUNT(*) AS row_count,
    MAX(created_at) AS latest_record
FROM delivery_items;
