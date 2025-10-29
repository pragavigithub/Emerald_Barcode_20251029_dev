-- ================================================================
-- SAP B1 Inventory Counting - Local Storage Tables
-- Created: 2025-10-23
-- Purpose: Store SAP B1 Inventory Counting documents locally
--          for tracking, history, and offline access
-- ================================================================

-- ================================================================
-- 1. SAP Inventory Counts (Header Table)
-- ================================================================
CREATE TABLE IF NOT EXISTS sap_inventory_counts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doc_entry INT NOT NULL UNIQUE COMMENT 'SAP B1 DocumentEntry - unique identifier',
    doc_number INT NOT NULL COMMENT 'SAP B1 DocNumber - user-friendly number',
    series INT NOT NULL COMMENT 'SAP B1 Series',
    count_date DATETIME NULL COMMENT 'SAP B1 CountDate',
    counting_type VARCHAR(50) NULL COMMENT 'SAP B1 CountingType',
    count_time VARCHAR(10) NULL COMMENT 'SAP B1 CountTime',
    single_counter_type VARCHAR(50) NULL COMMENT 'SAP B1 SingleCounterType',
    document_status VARCHAR(20) NULL COMMENT 'SAP B1 DocumentStatus (Open/Closed)',
    remarks TEXT NULL COMMENT 'SAP B1 Remarks',
    reference_2 VARCHAR(100) NULL COMMENT 'SAP B1 Reference2',
    branch_id VARCHAR(10) NULL COMMENT 'SAP B1 BPL_IDAssignedToInvoice',
    financial_period INT NULL COMMENT 'SAP B1 FinancialPeriod',
    counter_type VARCHAR(50) NULL COMMENT 'SAP B1 CounterType',
    counter_id INT NULL COMMENT 'SAP B1 CounterID',
    multiple_counter_role VARCHAR(50) NULL COMMENT 'SAP B1 MultipleCounterRole',
    user_id INT NOT NULL COMMENT 'WMS User who loaded/updated this document',
    loaded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'When document was first loaded from SAP',
    last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last time document was updated',
    
    INDEX idx_doc_entry (doc_entry),
    INDEX idx_doc_number (doc_number),
    INDEX idx_user_id (user_id),
    INDEX idx_loaded_at (loaded_at),
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    COMMENT 'SAP B1 Inventory Counting Documents - Local storage for tracking'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- 2. SAP Inventory Count Lines (Detail Table)
-- ================================================================
CREATE TABLE IF NOT EXISTS sap_inventory_count_lines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    count_id INT NOT NULL COMMENT 'Reference to sap_inventory_counts.id',
    line_number INT NOT NULL COMMENT 'SAP B1 LineNumber',
    item_code VARCHAR(50) NOT NULL COMMENT 'SAP B1 ItemCode',
    item_description VARCHAR(200) NULL COMMENT 'SAP B1 ItemDescription',
    warehouse_code VARCHAR(10) NULL COMMENT 'SAP B1 WarehouseCode',
    bin_entry INT NULL COMMENT 'SAP B1 BinEntry',
    in_warehouse_quantity DECIMAL(19,6) DEFAULT 0 COMMENT 'SAP B1 InWarehouseQuantity',
    counted VARCHAR(5) DEFAULT 'tNO' COMMENT 'SAP B1 Counted (tYES/tNO)',
    uom_code VARCHAR(10) NULL COMMENT 'SAP B1 UoMCode',
    bar_code VARCHAR(100) NULL COMMENT 'SAP B1 BarCode',
    uom_counted_quantity DECIMAL(19,6) DEFAULT 0 COMMENT 'SAP B1 UoMCountedQuantity',
    items_per_unit DECIMAL(19,6) DEFAULT 1 COMMENT 'SAP B1 ItemsPerUnit',
    counter_type VARCHAR(50) NULL COMMENT 'SAP B1 CounterType',
    counter_id INT NULL COMMENT 'SAP B1 CounterID',
    multiple_counter_role VARCHAR(50) NULL COMMENT 'SAP B1 MultipleCounterRole',
    line_status VARCHAR(20) NULL COMMENT 'SAP B1 LineStatus',
    project_code VARCHAR(50) NULL COMMENT 'SAP B1 ProjectCode',
    manufacturer INT NULL COMMENT 'SAP B1 Manufacturer',
    supplier_catalog_no VARCHAR(50) NULL COMMENT 'SAP B1 SupplierCatalogNo',
    preferred_vendor VARCHAR(50) NULL COMMENT 'SAP B1 PreferredVendor',
    cost_code VARCHAR(50) NULL COMMENT 'SAP B1 CostCode',
    u_floor VARCHAR(50) NULL COMMENT 'SAP B1 User-defined field U_Floor',
    u_rack VARCHAR(50) NULL COMMENT 'SAP B1 User-defined field U_Rack',
    u_level VARCHAR(50) NULL COMMENT 'SAP B1 User-defined field U_Level',
    freeze VARCHAR(5) DEFAULT 'tNO' COMMENT 'SAP B1 Freeze (tYES/tNO)',
    u_invcount VARCHAR(50) NULL COMMENT 'SAP B1 User-defined field U_InvCount',
    variance DECIMAL(19,6) DEFAULT 0 COMMENT 'Calculated variance (UoMCountedQuantity - InWarehouseQuantity)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'When line was created locally',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'When line was last updated',
    
    INDEX idx_count_id (count_id),
    INDEX idx_item_code (item_code),
    INDEX idx_line_number (line_number),
    INDEX idx_warehouse_code (warehouse_code),
    
    FOREIGN KEY (count_id) REFERENCES sap_inventory_counts(id) ON DELETE CASCADE,
    
    COMMENT 'SAP B1 Inventory Counting Lines - Local storage for tracking'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ================================================================
-- MIGRATION VERIFICATION
-- ================================================================
-- Run these queries to verify the migration:

-- 1. Check if tables exist
-- SHOW TABLES LIKE 'sap_inventory%';

-- 2. Check table structure
-- DESCRIBE sap_inventory_counts;
-- DESCRIBE sap_inventory_count_lines;

-- 3. Check indexes
-- SHOW INDEX FROM sap_inventory_counts;
-- SHOW INDEX FROM sap_inventory_count_lines;

-- 4. Check foreign key constraints
-- SELECT 
--     TABLE_NAME,
--     COLUMN_NAME,
--     CONSTRAINT_NAME,
--     REFERENCED_TABLE_NAME,
--     REFERENCED_COLUMN_NAME
-- FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
-- WHERE TABLE_SCHEMA = DATABASE()
--   AND TABLE_NAME IN ('sap_inventory_counts', 'sap_inventory_count_lines')
--   AND REFERENCED_TABLE_NAME IS NOT NULL;


-- ================================================================
-- ROLLBACK SCRIPT (if needed)
-- ================================================================
-- To rollback this migration, run:
-- DROP TABLE IF EXISTS sap_inventory_count_lines;
-- DROP TABLE IF EXISTS sap_inventory_counts;


-- ================================================================
-- NOTES
-- ================================================================
-- 1. These tables store SAP B1 Inventory Counting documents locally
-- 2. Data is synchronized when documents are loaded from SAP B1
-- 3. Data is updated when documents are PATCHed back to SAP B1
-- 4. CASCADE DELETE ensures cleanup when parent records are deleted
-- 5. Timestamps track when documents were loaded/updated locally
-- 6. All SAP B1 field names are preserved for easy mapping
-- ================================================================
