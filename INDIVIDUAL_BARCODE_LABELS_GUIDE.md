# 📦 Individual Barcode Labels for Serial/Batch Items - Complete Guide

## 🎯 WHAT'S BEEN IMPLEMENTED

I've added **individual QR/barcode label generation** for serial-managed and batch-managed items in the GRPO module.

### **Key Features**:
- ✅ **Individual labels for EACH serial number** (not one label for all)
- ✅ **Batch labels with quantity information**
- ✅ **Print all labels at once**
- ✅ **Smart button detection** (shows correct button based on item type)

---

## 🔍 WHERE TO FIND THE BUTTONS

After you add items to a GRPO, you'll see special buttons in the "Received Items" section:

### **For Serial-Managed Items** (like S1):
```
┌──────────────────────────────────────────────────┐
│ Item: S1 - 225MM Inspection Table Fan           │
│ Qty: 2                                           │
│ Actions: [🖨️ Print 2 QR Labels]  ← BLUE BUTTON │
└──────────────────────────────────────────────────┘
```

### **For Batch-Managed Items** (like 1248-114497):
```
┌──────────────────────────────────────────────────┐
│ Item: 1248-114497 - MAHLE ANAND                  │
│ Qty: 8                                           │
│ Actions: [🖨️ Print Batch Labels]  ← CYAN BUTTON │
└──────────────────────────────────────────────────┘
```

### **For Normal Items** (no serial/batch):
```
┌──────────────────────────────────────────────────┐
│ Item: ITEM123 - Regular Item                     │
│ Qty: 10                                          │
│ Actions: [🏷️ QR Label]  ← GREEN BUTTON (old feature) │
└──────────────────────────────────────────────────┘
```

---

## 📋 STEP-BY-STEP: GENERATE INDIVIDUAL SERIAL LABELS

### **Example: Item S1 with 2 Serial Numbers**

#### **Step 1: Add Item with Serial Numbers**

1. Go to GRPO detail page
2. Find item **S1** in "Purchase Order Items"
3. Click **"+ Add Item"**
4. System detects: **Serial-Managed** ✅
5. Enter details:
   ```
   Item Code: S1
   Quantity: 2
   Warehouse: 7000-FG-SYSTEM-BIN-LOCATION
   
   Serial Numbers:
   - Serial #1: 781
   - Serial #2: 782
   ```
6. Click **"Add Item"**
7. ✅ Item added to "Received Items" section

---

#### **Step 2: Generate Individual QR Labels**

1. **Find the item** in "Received Items" table:
   ```
   ╔══════════════════════════════════════════════════════╗
   ║ Item Code | Description          | Qty | Actions     ║
   ╠══════════════════════════════════════════════════════╣
   ║ S1        | 225MM Inspection...  | 2   | [Print 2 QR…║  ← Look here!
   ╚══════════════════════════════════════════════════════╝
   ```

2. **Click the BLUE button**: **"Print 2 QR Labels"**

3. **Modal opens** with **2 individual QR codes**:
   ```
   ┌─────────────────────────────────────────────────────┐
   │ # QR Code Labels                            [Close] │
   ├─────────────────────────────────────────────────────┤
   │                                                      │
   │ ┌─────────────────────┐  ┌─────────────────────┐  │
   │ │ S1 - 225MM...       │  │ S1 - 225MM...       │  │
   │ │ ███████████         │  │ ███████████         │  │
   │ │ █ ▄▄▄▄▄ █ ▀█       │  │ █ ▄▄▄▄▄ █ ▀█       │  │
   │ │ █ █   █ █▀ ▄       │  │ █ █   █ █▀ ▄       │  │
   │ │ █ █▄▄▄█ █▄ ▀       │  │ █ █▄▄▄█ █▄ ▀       │  │
   │ │ ███████████         │  │ ███████████         │  │
   │ │ Serial: 781         │  │ Serial: 782         │  │
   │ │ MFG: 781            │  │ MFG: 782            │  │
   │ └─────────────────────┘  └─────────────────────┘  │
   │                                                      │
   │         [Close]  [🖨️ Print All Labels]            │
   └─────────────────────────────────────────────────────┘
   ```

4. **Click "Print All Labels"** to print both labels

5. ✅ **Print dialog opens** with 2 individual barcode labels!

---

## 📋 STEP-BY-STEP: GENERATE BATCH LABELS

### **Example: Item 1248-114497 with Batch Number**

#### **Step 1: Add Item with Batch Number**

1. Find item **1248-114497** in "Purchase Order Items"
2. Click **"+ Add Item"**
3. System detects: **Batch-Managed** ✅
4. Enter details:
   ```
   Item Code: 1248-114497
   Quantity: 8
   Warehouse: 7000-FG-SYSTEM-BIN-LOCATION
   Batch Number: 4834800422
   Expiry Date: 2025-10-17
   ```
5. Click **"Add Item"**
6. ✅ Item added to "Received Items"

---

#### **Step 2: Generate Batch QR Label**

1. **Find the item** in "Received Items" table:
   ```
   ╔══════════════════════════════════════════════════════════╗
   ║ Item Code    | Description          | Qty | Actions     ║
   ╠══════════════════════════════════════════════════════════╣
   ║ 1248-114497  | MAHLE ANAND...       | 8   | [Print Bat…║  ← Look here!
   ╚══════════════════════════════════════════════════════════╝
   ```

2. **Click the CYAN button**: **"Print Batch Labels"**

3. **Modal opens** with batch QR code:
   ```
   ┌─────────────────────────────────────────────────────┐
   │ # QR Code Labels                            [Close] │
   ├─────────────────────────────────────────────────────┤
   │                                                      │
   │         ┌─────────────────────────┐                 │
   │         │ 1248-114497 - MAHLE...  │                 │
   │         │ ███████████████         │                 │
   │         │ █ ▄▄▄▄▄ █▀█▄█          │                 │
   │         │ █ █   █ █ ▀▄█          │                 │
   │         │ █ █▄▄▄█ █▄▀ █          │                 │
   │         │ ███████████████         │                 │
   │         │ Batch: 4834800422       │                 │
   │         │ Qty: 8                  │                 │
   │         │ Expiry: 2025-10-17      │                 │
   │         └─────────────────────────┘                 │
   │                                                      │
   │         [Close]  [🖨️ Print All Labels]            │
   └─────────────────────────────────────────────────────┘
   ```

4. **Click "Print All Labels"** to print batch label

5. ✅ **Print dialog opens** with batch barcode label!

---

## 🎯 WHAT MAKES THIS DIFFERENT FROM OLD QR LABEL?

### **OLD QR Label Feature** (Green "QR Label" button):
- ✅ Single QR code for the item
- ✅ Shows item code, batch, SAP document number
- ✅ Used for general item tracking

### **NEW Individual Serial Labels** (Blue "Print 2 QR Labels" button):
- ✅ **SEPARATE QR code for EACH serial number**
- ✅ Example: 10 serials = 10 individual labels
- ✅ Each label shows:
  - Item code & description
  - **Specific serial number**
  - Manufacturer serial (if any)
  - Expiry date (if any)
- ✅ **Perfect for attaching physical labels to each unit**

### **NEW Batch Labels** (Cyan "Print Batch Labels" button):
- ✅ QR code with batch information
- ✅ Shows batch number, quantity, expiry
- ✅ Used for batch tracking

---

## 🔧 TROUBLESHOOTING: IF LABELS DON'T SHOW

### **Issue: "QR library not loaded"**

**Cause**: Browser cache hasn't loaded the new QRCode library

**Solution**: Do a **hard refresh**:
- **Windows/Linux**: `Ctrl + Shift + R`
- **Mac**: `Cmd + Shift + R`

---

### **Issue: Buttons not appearing**

**Check**:
1. ✅ Item has been **added to GRPO** (in "Received Items" section)
2. ✅ Item has **serial numbers saved** (for serial items)
3. ✅ Item has **batch number saved** (for batch items)

**Where to look**: "Received Items" section (below the purchase order items)

---

## 📊 BUTTON DETECTION LOGIC

The system **automatically shows the correct button** based on item type:

```python
# Backend logic in modules/grpo/routes.py

if item has serial numbers:
    → Show BLUE "Print X QR Labels" button
    
elif item has batch numbers:
    → Show CYAN "Print Batch Labels" button
    
else:
    → Show GREEN "QR Label" button (old feature)
```

---

## ✅ COMPLETE WORKFLOW EXAMPLE

### **Scenario**: Receive 2 units of Item S1 with serial tracking

```
1. Create GRPO for PO #3642
   ↓
2. Add Item S1:
   - Quantity: 2
   - Serial #1: SN-001
   - Serial #2: SN-002
   ↓
3. Item appears in "Received Items" with blue button
   ↓
4. Click "Print 2 QR Labels"
   ↓
5. Modal shows 2 QR codes (one for SN-001, one for SN-002)
   ↓
6. Click "Print All Labels"
   ↓
7. Print 2 physical labels
   ↓
8. Attach label with SN-001 to first unit
   ↓
9. Attach label with SN-002 to second unit
   ↓
10. Submit GRPO for QC
   ↓
11. QC approves
   ↓
12. Post to SAP B1
   ↓
✅ Both serial numbers posted to SAP successfully!
```

---

## 🎊 SUMMARY

**Individual Barcode Label Feature**:
- ✅ **Implemented and working** in Replit
- ✅ **Blue buttons** for serial items (e.g., "Print 2 QR Labels")
- ✅ **Cyan buttons** for batch items (e.g., "Print Batch Labels")
- ✅ **One QR code per serial number** (10 serials = 10 labels)
- ✅ **Print all labels at once**
- ✅ **Ready for production use**

**How to Use**:
1. Add items with serial/batch numbers to GRPO
2. Look for colored buttons in "Received Items" section
3. Click the button to open modal with individual QR codes
4. Print all labels
5. Attach to physical items

**Your GRPO module now supports complete individual barcode label generation for warehouse tracking!** 🚀
