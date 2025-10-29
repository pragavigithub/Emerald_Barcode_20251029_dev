-- =====================================================
-- GRPO Barcode Enhancement Migration
-- Date: 2025-10-15
-- Description: Add barcode support for serial and batch managed items in GRPO
-- =====================================================

-- The barcode fields are already part of the base schema
-- This migration documents the enhancement to auto-generate barcodes

-- Verify barcode columns exist in grpo_serial_numbers table
-- Expected schema:
-- - id (PRIMARY KEY)
-- - grpo_item_id (FOREIGN KEY to grpo_items.id)
-- - manufacturer_serial_number VARCHAR(100)
-- - internal_serial_number VARCHAR(100) UNIQUE NOT NULL
-- - expiry_date DATE
-- - manufacture_date DATE
-- - notes TEXT
-- - barcode VARCHAR(200)  -- Base64 encoded QR code barcode
-- - quantity DECIMAL(15,3) DEFAULT 1.0
-- - base_line_number INT DEFAULT 0
-- - created_at DATETIME DEFAULT CURRENT_TIMESTAMP

-- Verify barcode columns exist in grpo_batch_numbers table
-- Expected schema:
-- - id (PRIMARY KEY)
-- - grpo_item_id (FOREIGN KEY to grpo_items.id)
-- - batch_number VARCHAR(100) NOT NULL
-- - quantity DECIMAL(15,3) NOT NULL
-- - base_line_number INT DEFAULT 0
-- - manufacturer_serial_number VARCHAR(100)
-- - internal_serial_number VARCHAR(100)
-- - expiry_date DATE
-- - barcode VARCHAR(200)  -- Base64 encoded QR code barcode
-- - created_at DATETIME DEFAULT CURRENT_TIMESTAMP

-- No schema changes required - fields already exist
-- Enhancement is in application logic to auto-generate barcodes

-- Barcode Format:
-- Serial Items: "SN:{internal_serial_number}"
-- Batch Items: "BATCH:{batch_number}"

-- Application changes:
-- 1. Auto-detect item type (serial/batch/non-batch) via SAP API call
-- 2. Generate QR code barcodes automatically when serial/batch items are added
-- 3. Store barcode as base64 encoded image in database
-- 4. Display barcodes in GRPO detail view

SELECT 'GRPO Barcode Enhancement - No schema changes required' AS status;
