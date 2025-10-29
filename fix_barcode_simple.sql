-- ========================================
-- FIX BARCODE COLUMNS - SIMPLE VERSION
-- ========================================
-- Run this file directly in MySQL:
-- mysql -u root -p wms_db < fix_barcode_simple.sql
-- ========================================

USE wms_db;

-- Fix grpo_items.barcode column
ALTER TABLE grpo_items MODIFY COLUMN barcode TEXT;

-- Fix grpo_serial_numbers.barcode column  
ALTER TABLE grpo_serial_numbers MODIFY COLUMN barcode TEXT;

-- Fix grpo_batch_numbers.barcode column
ALTER TABLE grpo_batch_numbers MODIFY COLUMN barcode TEXT;

-- Show success message
SELECT '✅ Barcode columns updated successfully!' as Status;
SELECT 'Restart your Flask application and test adding serial numbers.' as NextStep;
