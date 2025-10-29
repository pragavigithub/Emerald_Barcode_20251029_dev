-- =====================================================
-- MySQL Migration: Serial Number Multi-Select Enhancement
-- Date: 2025-10-29
-- Description: Enhancements to Serial Number Transfer Module
-- =====================================================

-- NOTE: No database schema changes required for this enhancement.
-- The existing database structure already supports multiple serial numbers per transfer item.
-- This migration documents the functional changes made to the system.

-- =====================================================
-- EXISTING SCHEMA (No Changes Required)
-- =====================================================

-- The following tables already support multiple serial number selection:
-- 
-- 1. serial_number_transfers (Header table)
--    - Stores transfer document header information
--    - No changes needed
--
-- 2. serial_number_transfer_items (Line items table)
--    - Stores item-level information for each transfer
--    - quantity field already supports multiple serials
--    - No changes needed
--
-- 3. serial_number_transfer_serials (Serial numbers table)
--    - Stores individual serial numbers for each transfer item
--    - is_validated field tracks SAP validation status
--    - Unique constraint was previously removed to allow duplicates for user review
--    - No changes needed

-- =====================================================
-- FUNCTIONAL ENHANCEMENTS
-- =====================================================

-- 1. SAP B1 Integration Update:
--    Updated create_serial_number_stock_transfer() method in sap_integration.py
--    to use correct SAP B1 StockTransferLines JSON structure:
--    
--    StockTransferLines: [
--        {
--            "LineNum": 0,
--            "ItemCode": "Item123",
--            "Quantity": 5,  # Total number of serial numbers
--            "WarehouseCode": "7000-QFG",
--            "FromWarehouseCode": "7000-FG",
--            "UoMCode": "Each",
--            "SerialNumbers": [
--                {
--                    "BaseLineNumber": 0,        # References parent line's LineNum (always 0 for LineNum 0)
--                    "InternalSerialNumber": "SN001",
--                    "Quantity": 1,              # Always 1 for serial items
--                    "SystemSerialNumber": "SN001",
--                    "ExpiryDate": null,
--                    "ManufactureDate": null,
--                    "ReceptionDate": null,
--                    "WarrantyStart": null,
--                    "WarrantyEnd": null
--                },
--                {
--                    "BaseLineNumber": 0,        # All serials in same line have same BaseLineNumber
--                    "InternalSerialNumber": "SN002",
--                    "Quantity": 1,
--                    "SystemSerialNumber": "SN002",
--                    ...
--                },
--                ...
--            ]
--        }
--    ]

-- 2. New API Endpoint:
--    Added /api/get-available-serial-numbers endpoint to fetch available serial numbers
--    from SAP B1 for a given item code and warehouse code
--    
--    Parameters:
--      - item_code: The item code to search for
--      - warehouse_code: The warehouse to search in
--    
--    Returns: List of available serial numbers with status = 0 (available)

-- 3. New SAP Integration Method:
--    Added get_available_serial_numbers() method to fetch serial numbers from
--    SAP B1 SerialNumberDetails API with proper filtering

-- =====================================================
-- USAGE NOTES
-- =====================================================

-- Users can now:
-- 1. Select multiple serial numbers from a dropdown (populated from SAP)
-- 2. Scan QR codes to add serial numbers
-- 3. Manually enter serial numbers
-- 4. The system validates all serial numbers against SAP B1
-- 5. Only validated serial numbers are posted to SAP when transfer is approved

-- =====================================================
-- ROLLBACK NOTES
-- =====================================================

-- To rollback this enhancement:
-- 1. Revert sap_integration.py changes to previous version
-- 2. Remove /api/get-available-serial-numbers endpoint from api_routes.py
-- 3. No database changes needed as schema remains unchanged

-- =====================================================
-- END OF MIGRATION
-- =====================================================
