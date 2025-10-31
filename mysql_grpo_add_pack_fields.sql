-- MySQL Migration: Add qty_per_pack, no_of_packs, and grn_number fields to GRPO tables
-- Run this migration on your local MySQL database to support the new QR label generation features
-- Date: 2025-10-31

-- Add fields to grpo_serial_numbers table
-- Check if columns exist before adding
SET @exist_grn_serial = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_serial_numbers' AND COLUMN_NAME = 'grn_number');
SET @exist_qty_serial = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_serial_numbers' AND COLUMN_NAME = 'qty_per_pack');
SET @exist_packs_serial = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_serial_numbers' AND COLUMN_NAME = 'no_of_packs');

SET @sql_serial = IF(@exist_grn_serial = 0, 'ALTER TABLE grpo_serial_numbers ADD COLUMN grn_number VARCHAR(50);', 'SELECT "Column grn_number already exists in grpo_serial_numbers";');
PREPARE stmt FROM @sql_serial; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql_serial = IF(@exist_qty_serial = 0, 'ALTER TABLE grpo_serial_numbers ADD COLUMN qty_per_pack DECIMAL(15,3) DEFAULT 1.0;', 'SELECT "Column qty_per_pack already exists in grpo_serial_numbers";');
PREPARE stmt FROM @sql_serial; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql_serial = IF(@exist_packs_serial = 0, 'ALTER TABLE grpo_serial_numbers ADD COLUMN no_of_packs INT DEFAULT 1;', 'SELECT "Column no_of_packs already exists in grpo_serial_numbers";');
PREPARE stmt FROM @sql_serial; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Add fields to grpo_batch_numbers table
SET @exist_grn_batch = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_batch_numbers' AND COLUMN_NAME = 'grn_number');
SET @exist_qty_batch = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_batch_numbers' AND COLUMN_NAME = 'qty_per_pack');
SET @exist_packs_batch = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_batch_numbers' AND COLUMN_NAME = 'no_of_packs');

SET @sql_batch = IF(@exist_grn_batch = 0, 'ALTER TABLE grpo_batch_numbers ADD COLUMN grn_number VARCHAR(50);', 'SELECT "Column grn_number already exists in grpo_batch_numbers";');
PREPARE stmt FROM @sql_batch; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql_batch = IF(@exist_qty_batch = 0, 'ALTER TABLE grpo_batch_numbers ADD COLUMN qty_per_pack DECIMAL(15,3);', 'SELECT "Column qty_per_pack already exists in grpo_batch_numbers";');
PREPARE stmt FROM @sql_batch; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql_batch = IF(@exist_packs_batch = 0, 'ALTER TABLE grpo_batch_numbers ADD COLUMN no_of_packs INT DEFAULT 1;', 'SELECT "Column no_of_packs already exists in grpo_batch_numbers";');
PREPARE stmt FROM @sql_batch; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Create indexes for better query performance
-- Check if indexes exist before creating
SET @exist_idx_serial = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_serial_numbers' AND INDEX_NAME = 'idx_grpo_serial_grn');
SET @exist_idx_batch = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'grpo_batch_numbers' AND INDEX_NAME = 'idx_grpo_batch_grn');

SET @sql_idx = IF(@exist_idx_serial = 0, 'CREATE INDEX idx_grpo_serial_grn ON grpo_serial_numbers(grn_number);', 'SELECT "Index idx_grpo_serial_grn already exists";');
PREPARE stmt FROM @sql_idx; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql_idx = IF(@exist_idx_batch = 0, 'CREATE INDEX idx_grpo_batch_grn ON grpo_batch_numbers(grn_number);', 'SELECT "Index idx_grpo_batch_grn already exists";');
PREPARE stmt FROM @sql_idx; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Verification queries
SELECT 'Migration completed successfully. Verify the new columns:' AS Status;
SHOW COLUMNS FROM grpo_serial_numbers LIKE '%pack%';
SHOW COLUMNS FROM grpo_serial_numbers LIKE 'grn_number';
SHOW COLUMNS FROM grpo_batch_numbers LIKE '%pack%';
SHOW COLUMNS FROM grpo_batch_numbers LIKE 'grn_number';
