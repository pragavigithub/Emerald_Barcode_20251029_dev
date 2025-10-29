# Multi GRN Module - Purchase Order Display Fix

## Date: October 14, 2025

## Issue Identified
The Multi GRN Module was fetching open Purchase Orders from SAP but not displaying them in the UI.

## Root Cause
The SAP API filter was using `CardCode` instead of `CardName`:
- **Previous filter**: `CardCode eq '3D SPL'` (CardCode value)
- **Working filter**: `CardName eq '3D SEALS PRIVATE LIMITED'` (CardName value)

The system was correctly storing both CardCode and CardName in Step 1, but Step 2 was trying to fetch POs using CardCode when SAP required CardName for this query.

## Solution Implemented

### 1. Created New Service Method
- **File**: `modules/multi_grn_creation/services.py`
- **New Method**: `fetch_open_purchase_orders_by_name(card_name)`
- **Filter**: Uses `CardName eq '{card_name}'` instead of `CardCode`

### 2. Updated Routes
- **File**: `modules/multi_grn_creation/routes.py`
- **Step 2** (Line 101): Changed from `fetch_open_purchase_orders(batch.customer_code)` to `fetch_open_purchase_orders_by_name(batch.customer_name)`
- **Step 3** (Line 155): Changed from `fetch_open_purchase_orders(batch.customer_code)` to `fetch_open_purchase_orders_by_name(batch.customer_name)`

### 3. Maintained Backward Compatibility
- Kept the original `fetch_open_purchase_orders(card_code)` method for other modules that might use CardCode

## MySQL Migration Status
✅ The MySQL migration file `mysql_multi_grn_migration.py` is already up to date and includes all required tables:
- `multi_grn_batches` - Main batch records
- `multi_grn_po_links` - Links between batches and POs
- `multi_grn_line_selections` - Selected line items

## Testing
The fix has been deployed and the application is running successfully. The Multi GRN module should now:
1. Display open Purchase Orders when filtering by CardName
2. Show the PO list correctly in the UI
3. Allow users to select POs for batch GRN creation

## API Example
**Working SAP Query**:
```
https://192.168.1.4:50000/b1s/v1/PurchaseOrders?$filter=CardName eq '3D SEALS PRIVATE LIMITED' and DocumentStatus eq 'bost_Open'
```

This query now matches what the Multi GRN module uses internally.

---

## Additional Fix: OpenQuantity KeyError

### Issue
When clicking "Next: Review" button in Step 3, the application crashed with:
```
KeyError: 'OpenQuantity'
```

### Root Cause
The SAP API doesn't consistently return the `OpenQuantity` field in all document line items. The code was using direct dictionary access `line_data['OpenQuantity']` which failed when this field was missing.

### Solution (Lines 128, 137-138 in routes.py)
Changed from direct dictionary access to safe `.get()` method with fallback values:

**Before:**
```python
selected_qty = Decimal(request.form.get(qty_key, line_data['OpenQuantity']))
open_quantity=Decimal(str(line_data['OpenQuantity']))
```

**After:**
```python
open_qty = line_data.get('OpenQuantity', line_data.get('Quantity', 0))
selected_qty = Decimal(request.form.get(qty_key, open_qty))
open_quantity=Decimal(str(line_data.get('OpenQuantity', line_data.get('Quantity', 0))))
```

### Result
✅ The application now handles SAP responses gracefully, even when `OpenQuantity` is missing
✅ Falls back to using `Quantity` field when `OpenQuantity` is not available
✅ Users can successfully proceed to the Review step without errors

---

## Additional Fix: Template TypeError in Review Step

### Issue
When accessing the Review step (Step 4), the application crashed with:
```
TypeError: unsupported operand type(s) for +: 'int' and 'builtin_function_or_method'
```

### Root Cause
In the template `step4_review.html` line 20, the code was trying to use:
```jinja
{{ batch.po_links | sum(attribute='line_selections.count') }}
```

The problem is that `count` is a method in SQLAlchemy relationships, not an attribute. When Jinja2 accessed it as an attribute, it got the method object itself, which cannot be summed with integers.

### Solution (Line 23 in step4_review.html)
Changed from using `sum` with `count` attribute to manually iterating and counting:

**Before:**
```jinja
{{ batch.po_links | sum(attribute='line_selections.count') }}
```

**After:**
```jinja
{% set total_items = namespace(count=0) %}
{% for po_link in batch.po_links %}
  {% set total_items.count = total_items.count + (po_link.line_selections | length) %}
{% endfor %}
{{ total_items.count }}
```

### Result
✅ The Review step now displays correctly
✅ Total items count is calculated properly using the `length` filter
✅ Users can review their selections before posting to SAP
