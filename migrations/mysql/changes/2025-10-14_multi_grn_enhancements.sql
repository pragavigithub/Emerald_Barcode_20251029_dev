-- Migration: MultiGRN Enhancements - Serial/Batch Number Support and Barcode Generation
-- Created: 2025-10-14
-- Description: Add batch_number tracking and serial/batch number support to MultiGRN module

-- UP SQL (Apply Changes)

-- Add batch_number column to multi_grn_batches for better tracking
ALTER TABLE multi_grn_batches 
ADD COLUMN batch_number VARCHAR(50) UNIQUE AFTER id;

-- Add serial/batch number fields to multi_grn_line_selections
ALTER TABLE multi_grn_line_selections
ADD COLUMN serial_numbers TEXT AFTER inventory_type,
ADD COLUMN batch_numbers TEXT AFTER serial_numbers,
ADD COLUMN barcode_generated BOOLEAN DEFAULT FALSE AFTER posting_payload;

-- Create index for batch_number lookup
CREATE INDEX idx_multi_grn_batches_batch_number ON multi_grn_batches(batch_number);

-- Create index for barcode generation status
CREATE INDEX idx_multi_grn_line_selections_barcode_generated ON multi_grn_line_selections(barcode_generated);

-- DOWN SQL (Rollback Changes)
-- ALTER TABLE multi_grn_batches DROP COLUMN batch_number;
-- ALTER TABLE multi_grn_line_selections DROP COLUMN serial_numbers;
-- ALTER TABLE multi_grn_line_selections DROP COLUMN batch_numbers;
-- ALTER TABLE multi_grn_line_selections DROP COLUMN barcode_generated;
-- DROP INDEX idx_multi_grn_batches_batch_number ON multi_grn_batches;
-- DROP INDEX idx_multi_grn_line_selections_barcode_generated ON multi_grn_line_selections;
