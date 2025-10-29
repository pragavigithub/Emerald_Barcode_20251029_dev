/**
 * Inventory Transfer Module - ItemCode Validation and Warehouse Selection
 * Implements dynamic form behavior based on item type (Serial/Batch/Non-Managed)
 */

let currentItemType = null;
let warehouseData = [];

// Auto-attach blur event listener when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const itemCodeInput = document.getElementById('item_code');
    if (itemCodeInput) {
        itemCodeInput.addEventListener('blur', validateItemCode);
    }
});

/**
 * Validate ItemCode and determine item type
 */
async function validateItemCode() {
    const itemCodeInput = document.getElementById('item_code');
    const itemCode = itemCodeInput.value.trim();
    
    if (!itemCode) {
        return;
    }
    
    try {
        showLoadingIndicator('Validating item code...');
        
        const response = await fetch('/inventory_transfer/api/validate-itemcode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ item_code: itemCode })
        });
        
        const data = await response.json();
        hideLoadingIndicator();
        
        if (data.success) {
            currentItemType = data.item_type;
            
            showNotification(`Item validated as ${data.item_type.toUpperCase()} managed`, 'success');
            
            adjustFormBasedOnItemType(data.item_type, data);
            
            await fetchWarehouseDetails(itemCode, data.item_type);
        } else {
            showNotification(`Error: ${data.error}`, 'error');
            resetFormFields();
        }
    } catch (error) {
        hideLoadingIndicator();
        console.error('Error validating item code:', error);
        showNotification('Error validating item code', 'error');
    }
}

/**
 * Adjust form fields based on item type
 */
function adjustFormBasedOnItemType(itemType, validationData) {
    const serialNumberGroup = document.getElementById('serial_number_group');
    const batchNumberGroup = document.getElementById('batch_number_group');
    const quantityInput = document.getElementById('quantity');
    const itemTypeIndicator = document.getElementById('item_type_indicator');
    
    if (itemTypeIndicator) {
        itemTypeIndicator.innerHTML = `<span class="badge bg-info">Type: ${itemType.toUpperCase()}</span>`;
    }
    
    if (itemType === 'serial') {
        serialNumberGroup.style.display = 'block';
        batchNumberGroup.style.display = 'none';
        
        document.getElementById('serial_number').required = true;
        document.getElementById('batch_number').required = false;
        
        quantityInput.value = 1;
        quantityInput.setAttribute('readonly', true);
        
    } else if (itemType === 'batch') {
        serialNumberGroup.style.display = 'none';
        batchNumberGroup.style.display = 'block';
        
        document.getElementById('serial_number').required = false;
        document.getElementById('batch_number').required = true;
        
        quantityInput.removeAttribute('readonly');
        
    } else {
        serialNumberGroup.style.display = 'none';
        batchNumberGroup.style.display = 'none';
        
        document.getElementById('serial_number').required = false;
        document.getElementById('batch_number').required = false;
        
        quantityInput.removeAttribute('readonly');
    }
}

/**
 * Fetch warehouse details based on item type
 */
async function fetchWarehouseDetails(itemCode, itemType) {
    try {
        showLoadingIndicator('Fetching warehouse details...');
        
        const response = await fetch('/inventory_transfer/api/get-item-warehouses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                item_code: itemCode,
                item_type: itemType 
            })
        });
        
        const data = await response.json();
        hideLoadingIndicator();
        
        if (data.success) {
            warehouseData = data.warehouses;
            populateWarehouseDropdowns(data.warehouses, itemType);
            showNotification(`Found ${data.count} warehouse entries`, 'success');
        } else {
            showNotification(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        hideLoadingIndicator();
        console.error('Error fetching warehouse details:', error);
        showNotification('Error fetching warehouse details', 'error');
    }
}

/**
 * Populate warehouse dropdowns based on item type
 */
function populateWarehouseDropdowns(warehouses, itemType) {
    const fromWarehouseSelect = document.getElementById('from_warehouse_select');
    const serialNumberSelect = document.getElementById('serial_number');
    const batchNumberSelect = document.getElementById('batch_number');
    
    fromWarehouseSelect.innerHTML = '<option value="">Select Warehouse</option>';
    
    if (itemType === 'serial') {
        const uniqueWarehouses = [...new Set(warehouses.map(w => w.WarehouseCode))];
        uniqueWarehouses.forEach(whCode => {
            const option = document.createElement('option');
            option.value = whCode;
            option.textContent = whCode;
            fromWarehouseSelect.appendChild(option);
        });
        
    } else if (itemType === 'batch') {
        const uniqueWarehouses = [...new Set(warehouses.map(w => w.WarehouseCode))];
        uniqueWarehouses.forEach(whCode => {
            const option = document.createElement('option');
            option.value = whCode;
            option.textContent = whCode;
            fromWarehouseSelect.appendChild(option);
        });
        
    } else {
        warehouses.forEach(wh => {
            const option = document.createElement('option');
            option.value = wh.WarehouseCode;
            option.textContent = `${wh.WarehouseCode} - ${wh.WarehouseName} (Qty: ${wh.AvailableQty})`;
            fromWarehouseSelect.appendChild(option);
        });
    }
}

/**
 * Handle warehouse selection change
 */
function onWarehouseChange() {
    const fromWarehouseSelect = document.getElementById('from_warehouse_select');
    const selectedWarehouse = fromWarehouseSelect.value;
    
    if (!selectedWarehouse || !currentItemType) {
        return;
    }
    
    // Update the from_warehouse_code field (both hidden and visible)
    const fromWarehouseCodeFields = document.querySelectorAll('[name="from_warehouse_code"]');
    fromWarehouseCodeFields.forEach(field => {
        field.value = selectedWarehouse;
    });
    
    if (currentItemType === 'serial') {
        populateSerialNumbers(selectedWarehouse);
    } else if (currentItemType === 'batch') {
        populateBatchNumbers(selectedWarehouse);
    } else {
        updateAvailableQuantity(selectedWarehouse);
    }
}

/**
 * Populate serial numbers for selected warehouse
 */
function populateSerialNumbers(warehouseCode) {
    const serialNumberSelect = document.getElementById('serial_number');
    serialNumberSelect.innerHTML = '<option value="">Select Serial Number</option>';
    
    const serialsForWarehouse = warehouseData.filter(w => w.WarehouseCode === warehouseCode);
    
    serialsForWarehouse.forEach(serial => {
        const option = document.createElement('option');
        option.value = serial.SerialNumber;
        option.textContent = `${serial.SerialNumber} (Qty: ${serial.AvailableQty})`;
        option.setAttribute('data-qty', serial.AvailableQty);
        option.setAttribute('data-sys-number', serial.SysNumber);
        serialNumberSelect.appendChild(option);
    });
}

/**
 * Populate batch numbers for selected warehouse
 */
function populateBatchNumbers(warehouseCode) {
    const batchNumberSelect = document.getElementById('batch_number');
    batchNumberSelect.innerHTML = '<option value="">Select Batch Number</option>';
    
    const batchesForWarehouse = warehouseData.filter(w => w.WarehouseCode === warehouseCode);
    
    batchesForWarehouse.forEach(batch => {
        const option = document.createElement('option');
        option.value = batch.BatchNumber;
        option.textContent = `${batch.BatchNumber} (Qty: ${batch.AvailableQty})`;
        option.setAttribute('data-qty', batch.AvailableQty);
        option.setAttribute('data-sys-number', batch.SysNumber);
        batchNumberSelect.appendChild(option);
    });
}

/**
 * Update available quantity for non-managed items
 */
function updateAvailableQuantity(warehouseCode) {
    const quantityInput = document.getElementById('quantity');
    const warehouse = warehouseData.find(w => w.WarehouseCode === warehouseCode);
    
    if (warehouse) {
        const maxQty = warehouse.AvailableQty;
        quantityInput.setAttribute('max', maxQty);
        quantityInput.setAttribute('placeholder', `Max: ${maxQty}`);
        
        const qtyInfo = document.getElementById('quantity_info');
        if (qtyInfo) {
            qtyInfo.textContent = `Available: ${maxQty}`;
        }
    }
}

/**
 * Handle serial number selection
 */
function onSerialNumberChange() {
    const serialNumberSelect = document.getElementById('serial_number');
    const selectedOption = serialNumberSelect.options[serialNumberSelect.selectedIndex];
    
    if (selectedOption && selectedOption.value) {
        const qty = selectedOption.getAttribute('data-qty');
        document.getElementById('quantity').value = qty || 1;
    }
}

/**
 * Handle batch number selection
 */
function onBatchNumberChange() {
    const batchNumberSelect = document.getElementById('batch_number');
    const selectedOption = batchNumberSelect.options[batchNumberSelect.selectedIndex];
    
    if (selectedOption && selectedOption.value) {
        const maxQty = selectedOption.getAttribute('data-qty');
        const quantityInput = document.getElementById('quantity');
        quantityInput.setAttribute('max', maxQty);
        quantityInput.setAttribute('placeholder', `Max: ${maxQty}`);
        
        const batchInfo = document.getElementById('batch_info');
        if (batchInfo) {
            batchInfo.textContent = `Available: ${maxQty}`;
        }
    }
}

/**
 * Reset form fields
 */
function resetFormFields() {
    currentItemType = null;
    warehouseData = [];
    
    document.getElementById('serial_number_group').style.display = 'none';
    document.getElementById('batch_number_group').style.display = 'none';
    
    const itemTypeIndicator = document.getElementById('item_type_indicator');
    if (itemTypeIndicator) {
        itemTypeIndicator.innerHTML = '';
    }
}

/**
 * Show loading indicator
 */
function showLoadingIndicator(message) {
    const indicator = document.getElementById('loading_indicator');
    if (indicator) {
        indicator.textContent = message;
        indicator.style.display = 'block';
    }
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const indicator = document.getElementById('loading_indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

/**
 * Show notification
 */
function showNotification(message, type) {
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = 9999;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
