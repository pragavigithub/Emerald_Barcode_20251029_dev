-- GRPO SAP B1 Integration Fix: BaseLineNumber Correction
-- Created: 2025-10-29
-- Description: Fixed BaseLineNumber in SAP B1 Purchase Delivery Note JSON payload
-- Type: Code Fix (No Database Schema Changes)

-- ISSUE DESCRIPTION:
-- When posting GRPO to SAP B1 as Purchase Delivery Notes, the BaseLineNumber
-- in BatchNumbers and SerialNumbers arrays was incorrectly using the PO line number
-- instead of the 0-indexed document line counter.

-- INCORRECT BEHAVIOR:
-- {
--   "DocumentLines": [
--     {
--       "BaseLine": 1,
--       "BatchNumbers": [{"BaseLineNumber": 1}]  -- WRONG: Should be 0
--     },
--     {
--       "BaseLine": 2,
--       "SerialNumbers": [{"BaseLineNumber": 2}]  -- WRONG: Should be 1
--     }
--   ]
-- }

-- CORRECT BEHAVIOR:
-- {
--   "DocumentLines": [
--     {
--       "BaseLine": 1,
--       "BatchNumbers": [{"BaseLineNumber": 0}]  -- CORRECT: 0-indexed
--     },
--     {
--       "BaseLine": 2,
--       "SerialNumbers": [{"BaseLineNumber": 1}]  -- CORRECT: 0-indexed
--     }
--   ]
-- }

-- CHANGES MADE:
-- File: sap_integration.py
-- Method: create_purchase_delivery_note()
-- Lines Changed:
--   - Line 2802: Changed from po_line_num to line_number (Serial Numbers)
--   - Line 2836: Changed from po_line_num to line_number (Batch Numbers)

-- IMPACT:
-- This fix ensures that GRPO documents post correctly to SAP B1 without
-- baseline number mismatches that could cause SAP API errors or incorrect
-- document linking.

-- SAP API ENDPOINT AFFECTED:
-- POST https://{sap_server}:50000/b1s/v1/PurchaseDeliveryNotes

-- NO DATABASE SCHEMA CHANGES REQUIRED
-- This is a code-only fix in the SAP integration layer.
