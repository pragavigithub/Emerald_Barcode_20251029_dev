-- MySQL Migration: Add doc_number field to grpo_documents table
-- Date: 2025-10-30
-- Description: Adds doc_number field to store unique GRPO document reference numbers

-- Add doc_number column to grpo_documents table
ALTER TABLE grpo_documents 
ADD COLUMN doc_number VARCHAR(50) NULL AFTER po_number;

-- Add index for faster lookups
CREATE INDEX idx_grpo_doc_number ON grpo_documents(doc_number);

-- Update existing records with generated doc_numbers
UPDATE grpo_documents
SET doc_number = CONCAT('GRN/', DATE_FORMAT(created_at, '%Y%m%d'), '/', LPAD(id, 10, '0'))
WHERE doc_number IS NULL;

-- Optional: Add comment to the column for documentation
ALTER TABLE grpo_documents 
MODIFY COLUMN doc_number VARCHAR(50) NULL COMMENT 'Unique GRN document number in format GRN/YYYYMMDD/NNNNNNNNNN';

-- Verify the migration
SELECT COUNT(*) as total_records, 
       COUNT(doc_number) as records_with_doc_number,
       COUNT(*) - COUNT(doc_number) as records_missing_doc_number
FROM grpo_documents;
