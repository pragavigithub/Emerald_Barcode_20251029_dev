# GRPO SAP B1 Integration Fix - BaseLineNumber Correction

## Date: 2025-10-29

## Problem
When posting GRPO to SAP B1 as Purchase Delivery Notes, the `BaseLineNumber` in `BatchNumbers` and `SerialNumbers` arrays was incorrectly starting from 1 instead of 0.

### Incorrect Behavior (Before Fix)
```json
{
  "DocumentLines": [
    {
      "BaseLine": 1,
      "ItemCode": "BatchItem_01",
      "BatchNumbers": [
        {
          "BatchNumber": "BATCH657",
          "Quantity": 10.0,
          "BaseLineNumber": 1  // ❌ WRONG - Should be 0
        }
      ]
    },
    {
      "BaseLine": 2,
      "ItemCode": "SerialItems",
      "SerialNumbers": [
        {
          "Quantity": 1.0,
          "BaseLineNumber": 2  // ❌ WRONG - Should be 1
        }
      ]
    }
  ]
}
```

### Correct Behavior (After Fix)
```json
{
  "DocumentLines": [
    {
      "BaseLine": 1,
      "ItemCode": "BatchItem_01",
      "BatchNumbers": [
        {
          "BatchNumber": "BATCHAH999-01",
          "Quantity": 10.0,
          "BaseLineNumber": 0  // ✅ CORRECT - 0-indexed
        }
      ]
    },
    {
      "BaseLine": 2,
      "ItemCode": "SerialItems",
      "SerialNumbers": [
        {
          "Quantity": 1.0,
          "BaseLineNumber": 1  // ✅ CORRECT - 0-indexed
        }
      ]
    }
  ]
}
```

## Solution
Updated `sap_integration.py` in the `create_purchase_delivery_note()` method:

### Changes Made:
1. **Line 2802** (Serial Numbers): Changed from `po_line_num` to `line_number`
2. **Line 2836** (Batch Numbers): Changed from `po_line_num` to `line_number`

The `line_number` variable is a 0-indexed counter that properly tracks the position of each item in the DocumentLines array.

## Files Modified
- `sap_integration.py` - Fixed BaseLineNumber logic

## Files Created
- `migrations/mysql/changes/2025-10-29_grpo_sap_baseline_number_fix.sql` - Migration documentation

## Impact
✅ GRPO documents now post correctly to SAP B1 without baseline number mismatches
✅ Prevents SAP API errors related to incorrect document linking
✅ Ensures proper batch and serial number tracking in SAP B1

## SAP API Endpoint
- **URL**: `POST https://{sap_server}:50000/b1s/v1/PurchaseDeliveryNotes`
- **Method**: POST

## Testing
To verify the fix:
1. Create a GRPO with batch and/or serial items
2. Approve the GRPO through QC
3. Check the JSON payload logged in the console
4. Verify BaseLineNumber starts from 0 for the first item

## Status
✅ **COMPLETED** - Application restarted and running successfully
