# Inventory Transfer Module - ItemCode Validation & Warehouse Selection Feature

## Implementation Date
October 29, 2025

## Overview
Implemented comprehensive ItemCode validation and dynamic warehouse selection logic using SAP B1 Service Layer APIs for the Inventory Transfer Module. The system now automatically detects item types (Serial/Batch/Non-Managed) and adjusts the UI accordingly.

## Features Implemented

### 1. ItemCode Type Validation (Step 1)
- **API Endpoint**: `/inventory_transfer/api/validate-itemcode`
- **SAP SQL Query**: `ItemCode_Batch_Serial_Val`
- **Response Fields**:
  - `BatchNum`: 'Y' for batch-managed items
  - `SerialNum`: 'Y' for serial-managed items
  - `MngMethod`: Management method indicator

### 2. Warehouse Details Fetching (Step 2)

#### For Serial Managed Items
- **API Endpoint**: `/inventory_transfer/api/get-item-warehouses`
- **SAP SQL Query**: `GetSerialManagedItemWH`
- **Response**: Warehouses, Serial Numbers, and Available Quantities per serial
- **UI Behavior**:
  - Enable Serial Number dropdown
  - Disable Batch Number field
  - Set quantity to 1 (readonly)

#### For Batch Managed Items
- **SAP SQL Query**: `GetBatchManagedItemWH`
- **Response**: Warehouses, Batch Numbers, and Available Quantities per batch
- **UI Behavior**:
  - Enable Batch Number dropdown
  - Disable Serial Number field
  - Allow manual quantity entry (with max validation)

#### For Non-Managed Items
- **SAP SQL Query**: `GetNonSerialNonBatchManagedItemWH`
- **Response**: Warehouses and Available Quantities
- **UI Behavior**:
  - Disable both Serial and Batch fields
  - Allow free quantity entry (with available qty validation)

## Files Modified

### 1. Backend Changes

#### `sap_integration.py`
Added three new methods:
- `get_serial_managed_item_warehouses(item_code)`: Fetches serial item warehouse details
- `get_batch_managed_item_warehouses(item_code)`: Fetches batch item warehouse details
- `get_non_managed_item_warehouses(item_code)`: Fetches non-managed item warehouse details

#### `modules/inventory_transfer/routes.py`
Added two new API endpoints:
- `@transfer_bp.route('/api/validate-itemcode', methods=['POST'])`: Validates ItemCode and returns type
- `@transfer_bp.route('/api/get-item-warehouses', methods=['POST'])`: Fetches warehouse details by type

### 2. Frontend Changes

#### `static/js/inventory_transfer_item_validation.js` (NEW FILE)
Created comprehensive JavaScript module with functions:
- `validateItemCode()`: Calls validation API and determines item type
- `adjustFormBasedOnItemType()`: Shows/hides form fields based on item type
- `fetchWarehouseDetails()`: Fetches warehouse data from SAP
- `populateWarehouseDropdowns()`: Populates warehouse selection based on type
- `onWarehouseChange()`: Handles warehouse selection changes
- `populateSerialNumbers()`: Populates serial numbers for selected warehouse
- `populateBatchNumbers()`: Populates batch numbers for selected warehouse
- `updateAvailableQuantity()`: Updates max quantity for non-managed items

#### `templates/inventory_transfer_detail.html`
Enhanced the Add Item Modal with:
- Item Type Indicator badge
- Loading indicator for async operations
- Warehouse selection dropdown (dynamic population)
- Serial Number dropdown (hidden by default)
- Batch Number dropdown (hidden by default)
- Improved validation and user feedback

## UI/UX Flow

### User Workflow
1. User clicks "Add Item" button
2. User enters Item Code and clicks "Validate" (or blur event triggers validation)
3. System calls SAP B1 to validate item and determine type
4. UI displays item type badge and adjusts form fields:
   - **Serial Items**: Shows Serial Number dropdown, quantity set to 1
   - **Batch Items**: Shows Batch Number dropdown, allows quantity entry
   - **Non-Managed**: Shows only quantity field
5. System fetches warehouse data based on item type
6. User selects warehouse from dropdown
7. System populates Serial/Batch numbers based on selection
8. User completes transfer details and submits

## API Request/Response Examples

### Validate ItemCode
```javascript
POST /inventory_transfer/api/validate-itemcode
Request: { "item_code": "IPhone" }
Response: {
  "success": true,
  "item_code": "IPhone",
  "item_type": "serial",
  "serial_required": true,
  "batch_required": false
}
```

### Get Warehouse Details - Serial Item
```javascript
POST /inventory_transfer/api/get-item-warehouses
Request: { "item_code": "IPhone", "item_type": "serial" }
Response: {
  "success": true,
  "warehouses": [
    {
      "itemCode": "IPhone",
      "SerialNumber": "SN12345",
      "WarehouseCode": "WH01",
      "WarehouseName": "Main Warehouse",
      "AvailableQty": 1
    }
  ]
}
```

## Database Changes
**No database schema changes were required** for this feature. All data is fetched dynamically from SAP B1.

## Testing Recommendations

### Test Cases
1. **Serial Item Validation**
   - Enter a serial-managed item code
   - Verify serial number dropdown appears
   - Verify quantity is locked to 1
   - Select warehouse and verify serial numbers populate

2. **Batch Item Validation**
   - Enter a batch-managed item code
   - Verify batch number dropdown appears
   - Verify quantity field is editable
   - Select warehouse and verify batch numbers populate

3. **Non-Managed Item Validation**
   - Enter a non-managed item code
   - Verify both serial/batch fields are hidden
   - Verify quantity field is editable
   - Select warehouse and verify available quantity displays

4. **Error Handling**
   - Test with invalid item code
   - Test with no SAP connection
   - Test with empty warehouse data

## SAP B1 SQL Queries Required

These SQL queries must exist in SAP B1:
1. `ItemCode_Batch_Serial_Val` - For item type validation
2. `GetSerialManagedItemWH` - For serial item warehouses
3. `GetBatchManagedItemWH` - For batch item warehouses
4. `GetNonSerialNonBatchManagedItemWH` - For non-managed item warehouses

## Benefits
1. **Automatic Item Type Detection**: No manual selection needed
2. **Real-time SAP Data**: Always shows current warehouse availability
3. **Validation at Entry**: Prevents invalid transfers before submission
4. **User-Friendly**: Dynamic UI adapts to item characteristics
5. **Error Prevention**: Shows only valid options for each item type

## Future Enhancements
1. Add item description auto-fetch on validation
2. Implement barcode scanning for item codes
3. Add quantity validation against available stock
4. Cache warehouse data to reduce SAP API calls
5. Add transfer history for quick re-entry
