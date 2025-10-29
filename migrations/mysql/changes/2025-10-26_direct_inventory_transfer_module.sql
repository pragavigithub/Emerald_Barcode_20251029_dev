-- Direct Inventory Transfer Module Migration
-- Created: 2025-10-26
-- Description: Adds tables for Direct Inventory Transfer module with barcode-driven transfers

-- Create direct_inventory_transfers table
CREATE TABLE IF NOT EXISTS direct_inventory_transfers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transfer_number VARCHAR(50) NOT NULL UNIQUE,
    sap_document_number VARCHAR(50),
    status VARCHAR(20) DEFAULT 'draft',
    user_id INT NOT NULL,
    qc_approver_id INT,
    qc_approved_at DATETIME,
    qc_notes TEXT,
    from_warehouse VARCHAR(50),
    to_warehouse VARCHAR(50),
    from_bin VARCHAR(50),
    to_bin VARCHAR(50),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (qc_approver_id) REFERENCES users(id),
    INDEX idx_transfer_number (transfer_number),
    INDEX idx_status (status),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create direct_inventory_transfer_items table
CREATE TABLE IF NOT EXISTS direct_inventory_transfer_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    direct_inventory_transfer_id INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_description VARCHAR(200),
    barcode VARCHAR(100),
    item_type VARCHAR(20),
    quantity DECIMAL(15,2) DEFAULT 1 NOT NULL,
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (direct_inventory_transfer_id) REFERENCES direct_inventory_transfers(id) ON DELETE CASCADE,
    INDEX idx_transfer_id (direct_inventory_transfer_id),
    INDEX idx_item_code (item_code),
    INDEX idx_validation_status (validation_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add document number series for direct inventory transfer if not exists
INSERT IGNORE INTO document_number_series (series_name, prefix, current_number, padding_length, description)
VALUES ('DIRECT_INVENTORY_TRANSFER', 'DIT', 0, 6, 'Direct Inventory Transfer Document Numbers');
