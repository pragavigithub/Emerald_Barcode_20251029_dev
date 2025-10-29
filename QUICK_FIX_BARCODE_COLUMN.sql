-- ========================================
-- QUICK FIX: Barcode Column Size Issue
-- Date: October 22, 2025
-- Issue: Data too long for column 'barcode'
-- ========================================

-- ERROR: (pymysql.err.DataError) (1406, "Data too long for column 'barcode' at row 1")
-- CAUSE: Barcode column is VARCHAR(100-200) but base64 PNG images are 2000-10000 chars
-- FIX: Change barcode columns to TEXT

USE wms_db;  -- Change to your database name

-- Fix barcode column in grpo_items
ALTER TABLE grpo_items 
MODIFY COLUMN barcode TEXT;

-- Fix barcode column in grpo_serial_numbers
ALTER TABLE grpo_serial_numbers 
MODIFY COLUMN barcode TEXT;

-- Fix barcode column in grpo_batch_numbers  
ALTER TABLE grpo_batch_numbers 
MODIFY COLUMN barcode TEXT;

-- Verify the changes
DESCRIBE grpo_items;
DESCRIBE grpo_serial_numbers;
DESCRIBE grpo_batch_numbers;

-- You should see barcode columns now showing as 'text' type

SELECT 'Barcode columns updated successfully!' as status;
