-- MySQL Migration: Add doc_number field to grpo_documents table
-- Date: 2025-10-30
-- Description: Adds doc_number field to store unique GRPO document reference numbers
-- Updated: Fixed to ensure uniqueness with UNIQUE constraint

-- Step 1: Add doc_number column to grpo_documents table
ALTER TABLE grpo_documents 
ADD COLUMN doc_number VARCHAR(50) NULL AFTER po_number;

-- Step 2: Update existing records with generated doc_numbers based on ID (guaranteed unique)
UPDATE grpo_documents
SET doc_number = CONCAT('GRN/', DATE_FORMAT(created_at, '%Y%m%d'), '/', LPAD(id, 10, '0'))
WHERE doc_number IS NULL;

-- Step 3: Add UNIQUE constraint to prevent duplicate doc_numbers
ALTER TABLE grpo_documents 
ADD UNIQUE INDEX idx_grpo_doc_number_unique (doc_number);

-- Step 4: Add comment to the column for documentation
ALTER TABLE grpo_documents 
MODIFY COLUMN doc_number VARCHAR(50) NULL COMMENT 'Unique GRN document number in format GRN/YYYYMMDD/NNNNNNNNNN - guaranteed unique by using auto-increment ID';

-- Verify the migration
SELECT COUNT(*) as total_records, 
       COUNT(doc_number) as records_with_doc_number,
       COUNT(DISTINCT doc_number) as unique_doc_numbers,
       COUNT(*) - COUNT(doc_number) as records_missing_doc_number
FROM grpo_documents;

-- Test uniqueness constraint (this should fail if run twice with same doc_number)
-- INSERT INTO grpo_documents (po_number, doc_number, user_id, status) VALUES ('TEST_PO', 'GRN/20251030/0000000001', 1, 'draft');
