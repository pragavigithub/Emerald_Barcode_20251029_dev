# Database Migration Log

## Purpose
This file tracks all database schema changes chronologically. Each migration represents a specific change to the database structure.

## Current Database Version
- **PostgreSQL (Primary)**: Latest schema from models
- **MySQL (Secondary)**: Tracked via migrations below

---

## Migration History

### 2025-10-13 - Initial Schema
- **File**: `mysql/schema/initial_schema.sql`
- **Description**: Initial database schema for Warehouse Management System
- **Tables Created**: 
  - Core: users, branches, user_sessions, password_reset_tokens
  - GRPO: grpo_documents, grpo_items
  - Inventory: inventory_transfers, inventory_transfer_items
  - Multi GRN: multi_grn_batches, multi_grn_po_links, multi_grn_line_selections
  - Pick List: pick_lists, pick_list_items, pick_list_lines, pick_list_bin_allocations
  - Serial: serial_number_transfers, serial_number_transfer_items, serial_number_transfer_serials
  - Serial Item: serial_item_transfers, serial_item_transfer_items
  - Supporting: bin_locations, bin_items, bin_scanning_logs, barcode_labels, qr_code_labels, document_number_series, inventory_counts, inventory_count_items, sales_orders, sales_order_lines
- **Status**: ✅ Documented
- **Applied By**: System
- **Notes**: 
  - Baseline schema from SQLAlchemy models
  - **Fixes Applied**: 
    - Added missing `created_by` column to `password_reset_tokens` table (INT, nullable, foreign key to users.id)
    - Corrected `password_reset_tokens.token` column from VARCHAR(255) to VARCHAR(256) to match SQLAlchemy model
  - Schema validated and ready for MySQL deployment

---

## Future Migrations
Add new migrations below in reverse chronological order (newest first).

### 2025-11-03 - GRPO Non-Managed Items Support
- **File**: `mysql/changes/2025-11-03_grpo_non_managed_items.sql`
- **Description**: Added support for non-batch, non-serial managed items in GRPO module with number of bags and QR label generation
- **Tables Created**: 
  - `grpo_non_managed_items` - Non-managed items tracking (when both BatchNum='N' and SerialNum='N')
- **Status**: ✅ Applied
- **Applied By**: Replit Agent
- **Changes**:
  - **grpo_non_managed_items Table**:
    - `id` INT AUTO_INCREMENT PRIMARY KEY
    - `grpo_item_id` INT NOT NULL (FK to grpo_items)
    - `quantity` DECIMAL(15,3) NOT NULL - Item quantity
    - `base_line_number` INT DEFAULT 0 - Line number for SAP posting
    - `expiry_date` DATE - Item expiry date
    - `grn_number` VARCHAR(50) - Unique GRN number for tracking
    - `qty_per_pack` DECIMAL(15,3) - Quantity per pack/bag
    - `no_of_packs` INT DEFAULT 1 - Number of packs/bags
    - `created_at` TIMESTAMP - Creation timestamp
  - **Indexes Added**:
    - `idx_grpo_item_id` on grpo_item_id
    - `idx_grn_number` on grn_number
    - `idx_created_at` on created_at
- **Application Integration**:
  - Model class `GRPONonManagedItem` added to `modules/grpo/models.py`
  - Supports QR code generation with PO Number, Quantity, ItemCode, GRN Number, GRN Date, ExpiryDate in JSON format
  - Number of bags input determines how many QR labels are generated (similar to batch items)
- **SAP B1 Integration**:
  - Uses API endpoint `SQLQueries('ItemCode_Batch_Serial_Val')/List` to detect non-managed items
  - When both `BatchNum='N'` and `SerialNum='N'`, item is treated as non-managed
- **Notes**: 
  - Enables complete inventory tracking for non-serialized, non-batch items
  - QR labels contain same information as batch items for consistency

---

### 2025-11-02 - SAP B1 SQL Queries Auto-Validation Feature
- **File**: `migrations/mysql/changes/2025-11-02_sap_sql_queries_auto_validation.sql`
- **Description**: Implemented automatic validation and creation of required SAP B1 SQL queries on application startup
- **Status**: ✅ Applied
- **Applied By**: Replit Agent
- **Changes**:
  - **New Module**: Created `sap_query_manager.py` - SAP B1 SQL Query Manager
    - Validates 17 required SQL queries on application startup
    - Automatically creates missing queries via SAP B1 Service Layer API
    - Provides detailed logging of query validation results
    - Gracefully handles SAP connection failures without blocking app startup
  - **Application Integration**:
    - Integrated into `app.py` startup sequence after database initialization
    - Runs after dual database support and before blueprint registration
    - Non-blocking - application continues if SAP validation fails
  - **SQL Queries Managed** (17 total):
    - **Item Validation**: ItemCode_Validation, ItemCode_Batch_Serial_Val
    - **Inventory Queries**: GetSerialManagedItemWH, GetBatchManagedItemWH, GetNonSerialNonBatchManagedItemWH
    - **Document Series**: Get_SO_Series, Get_PO_Series, Get_INVT_Series, Get_INVCNT_Series
    - **Document Lookup**: Get_SO_Details, Get_PO_DocEntry, Get_INVT_DocEntry, Get_INVCNT_DocEntry
    - **Open Documents**: Get_Open_SO_DocNum, Get_Open_PO_DocNum, Get_Open_INVTRNF_DocNum, Get_Open_INVCNT_DocNum
  - **API Endpoints Used**:
    - GET `/b1s/v1/SQLQueries('{SqlCode}')` - Check if query exists
    - POST `/b1s/v1/SQLQueries` - Create new query
  - **Logging Output**:
    - Reports existing, created, and failed query counts
    - Provides detailed info for each query validation step
- **Configuration**:
  - Uses existing SAP B1 environment variables from app.config:
    - SAP_B1_SERVER, SAP_B1_USERNAME, SAP_B1_PASSWORD, SAP_B1_COMPANY_DB
  - Requires no additional configuration
- **Workflow**:
  1. App starts → Database initialized → Dual DB support configured
  2. SAP Query Manager initializes and logs into SAP B1
  3. Checks each of 17 queries for existence
  4. Creates any missing queries via Service Layer POST
  5. Logs results summary and logs out
  6. App continues startup regardless of SAP availability
- **Error Handling**:
  - Graceful degradation if SAP B1 is unavailable
  - Application continues startup without SAP query validation
  - All errors logged with warning level
- **Benefits**:
  - Eliminates manual SQL query setup in SAP B1
  - Ensures WMS application has required queries available
  - Supports multi-environment deployments (dev, staging, prod)
  - Self-healing - recreates queries if accidentally deleted
- **Database Requirements**: None - queries stored in SAP B1, not MySQL/PostgreSQL
- **Notes**: 
  - Documentation file serves as reference for all managed queries
  - To add new queries: update `required_queries` list in sap_query_manager.py
  - All queries use SAP B1 parameter syntax (:paramName)
  - Queries are read-only SELECT statements
  - SSL verification disabled for SAP B1 API calls (uses verify=False)

### 2025-10-28 - GRPO Comprehensive QR Label System for Batch Items
- **Files**: `modules/grpo/routes.py`, `modules/grpo/templates/grpo/grpo_detail.html`
- **Description**: Complete overhaul of QR label generation for batch items - now generates multiple QR codes based on received quantity with comprehensive tracking information
- **Status**: ✅ Completed
- **Applied By**: Replit Agent
- **Changes**:
  - **Backend Changes** (`modules/grpo/routes.py`):
    - Modified `get_batch_numbers()` route to return GRPO document details
    - Added fields: po_number, grn_date, item_code, item_name, received_quantity
    - Enables frontend to generate comprehensive QR codes with complete tracking data
  - **Frontend Changes** (`modules/grpo/templates/grpo/grpo_detail.html`):
    - **Phase 1**: Modified `generateBarcodeLabels()` to use QR codes instead of CODE128 barcodes
    - **Phase 2**: Enhanced `generateBatchQRLabels()` to generate multiple QR codes per batch based on received quantity
    - Each QR code now contains comprehensive JSON data with all tracking fields
    - Added internal identification number system (format: GRN/{day}/{sequence})
    - QR codes are 150x150 pixels with high error correction level
- **QR Code Data Structure**:
  ```json
  {
    "id": "GRN/28/0000000001",
    "po": "252630003",
    "item": "1248-114497",
    "batch": "48348004225_001",
    "qty": 1,
    "pack": "1 of 10",
    "grn_date": "2025-10-28",
    "exp_date": "2025-11-08"
  }
  ```
- **Functionality**:
  - When user clicks "Print Batch Labels", system generates one QR code per unit of received quantity
  - Example: If received quantity = 10, generates 10 QR codes labeled "1 of 10", "2 of 10", etc.
  - Each label displays: Internal ID, PO Number, Item Code, Batch Number, Quantity, Pack sequence, GRN Date, Expiry Date
  - When scanned, QR code reveals complete JSON data structure with all tracking information
  - Labels are printable in a 3-column responsive grid layout
- **Internal ID Format**:
  - Pattern: `GRN/{day_of_month}/{10-digit_sequence}`
  - Example: GRN/28/0000000001, GRN/28/0000000002, etc.
  - Provides unique identification for each individual pack/unit
- **Database Requirements**: None - uses existing schema, all enhancements are UI and API response improvements
- **Notes**: 
  - Backward compatible - existing batch data works without modification
  - Uses existing qrcode.js library
  - Comprehensive scanning capability - all data embedded in QR code
  - Supports inventory tracking at individual pack level

### 2025-10-26 - QC Workflow Enforcement for Sales Delivery and Direct Inventory Transfer
- **Files**: `modules/sales_delivery/routes.py`, `routes.py`, `templates/edit_user.html`
- **Description**: Enforced QC approval workflow to ensure SAP B1 posting only occurs after QC approval for both Sales Delivery and Direct Inventory Transfer modules
- **Status**: ✅ Completed
- **Applied By**: Replit Agent
- **Changes**:
  - **Sales Delivery Module (`modules/sales_delivery/routes.py`)**:
    - Modified `api_submit_delivery` route to only set status to 'submitted' (removed SAP posting)
    - Submission now validates required data from SAP but does not post to SAP B1
    - Documents wait in 'submitted' status for QC approval
  - **Sales Delivery QC Approval (`routes.py`)**:
    - Modified `approve_sales_delivery_qc` route to post to SAP B1 after QC approval
    - Builds delivery document payload with batch/serial numbers
    - Sets status to 'posted' after successful SAP posting
    - Includes proper error handling with database rollback on SAP failures
  - **User Management (`templates/edit_user.html`)**:
    - Added permission checkbox for 'direct_inventory_transfer' module
    - Added permission checkbox for 'sales_delivery' module
    - Both modules now appear in user permissions management interface
  - **Direct Inventory Transfer**:
    - No changes required - already correctly enforces QC approval before SAP posting
    - Verified workflow: submit → QC approve → post to SAP
- **Workflow**:
  1. User creates delivery/transfer (status='draft')
  2. User submits for QC approval (status='submitted') - NO SAP posting
  3. QC approves (status='qc_approved') and system posts to SAP B1 (status='posted')
  4. QC can reject with notes (status='rejected') - NO SAP posting
- **Database Requirements**:
  - **IMPORTANT**: This enforcement requires the `2025-10-26_sales_delivery_qc_approval.sql` migration to be applied first
  - Migration adds: qc_approver_id, qc_approved_at, qc_notes columns to delivery_documents table
  - Migration adds: qc_status column to delivery_items table
- **Notes**: 
  - QC approval is now mandatory for both modules before SAP B1 posting
  - No bypass routes exist - all SAP posting goes through QC approval
  - Proper transaction management ensures data consistency
  - Error messages clearly indicate QC vs SAP failures

### 2025-10-26 - Sales Delivery QC Approval Workflow
- **File**: `migrations/mysql/changes/2025-10-26_sales_delivery_qc_approval.sql`
- **Description**: Added QC approval workflow to Sales Delivery module
- **Tables Affected**: delivery_documents, delivery_items
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **delivery_documents Table**:
    - Added `qc_approver_id` INT (FK to users.id) - QC approver reference
    - Added `qc_approved_at` DATETIME - QC approval timestamp
    - Added `qc_notes` TEXT - QC approval/rejection notes
    - Updated `status` column comment to include new statuses (draft, submitted, qc_approved, posted, rejected)
  - **delivery_items Table**:
    - Added `qc_status` VARCHAR(20) DEFAULT 'pending' - Item QC status (pending, approved, rejected)
  - **Indexes Added**:
    - `idx_delivery_status` on delivery_documents.status
    - `idx_delivery_qc_approved_at` on delivery_documents.qc_approved_at
    - `idx_delivery_item_qc_status` on delivery_items.qc_status
- **Application Integration**:
  - QC Dashboard now displays pending Sales Deliveries for approval
  - QC approval/rejection routes integrated
  - Sales Delivery appears in User Management permission checkboxes
- **Notes**: 
  - Enables quality control workflow for sales deliveries
  - Maintains consistency with other modules (GRPO, Inventory Transfer, etc.)
  - QC approval required before posting to SAP B1

### 2025-10-26 - Direct Inventory Transfer Module
- **File**: `mysql/changes/2025-10-26_direct_inventory_transfer_module.sql`
- **Description**: Added complete Direct Inventory Transfer module for barcode-driven warehouse transfers
- **Tables Created**: 
  - `direct_inventory_transfers` - Transfer document headers
  - `direct_inventory_transfer_items` - Transfer line items with batch/serial support
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **direct_inventory_transfers Table**:
    - `id` INT PRIMARY KEY AUTO_INCREMENT
    - `transfer_number` VARCHAR(50) UNIQUE - Document number
    - `sap_document_number` VARCHAR(50) - SAP B1 document reference
    - `status` VARCHAR(20) - draft, submitted, qc_approved, posted, rejected
    - `user_id` INT - Creator user reference (FK to users)
    - `qc_approver_id` INT - QC approver reference (FK to users)
    - `qc_approved_at` DATETIME - QC approval timestamp
    - `qc_notes` TEXT - QC approval/rejection notes
    - `from_warehouse` VARCHAR(50) - Source warehouse code
    - `to_warehouse` VARCHAR(50) - Destination warehouse code
    - `from_bin` VARCHAR(50) - Source bin location
    - `to_bin` VARCHAR(50) - Destination bin location
    - `notes` TEXT - Transfer notes
    - `created_at` DATETIME - Creation timestamp
    - `updated_at` DATETIME - Last update timestamp
  - **direct_inventory_transfer_items Table**:
    - `id` INT PRIMARY KEY AUTO_INCREMENT
    - `direct_inventory_transfer_id` INT - Parent transfer reference (FK, CASCADE DELETE)
    - `item_code` VARCHAR(50) - SAP item code
    - `item_description` VARCHAR(200) - Item description
    - `barcode` VARCHAR(100) - Scanned barcode value
    - `item_type` VARCHAR(20) - serial, batch, or none
    - `quantity` DECIMAL(15,2) - Transfer quantity
    - `unit_of_measure` VARCHAR(10) - UOM (default 'EA')
    - `from_warehouse_code` VARCHAR(50) - Source warehouse
    - `to_warehouse_code` VARCHAR(50) - Destination warehouse
    - `from_bin_code` VARCHAR(50) - Source bin
    - `to_bin_code` VARCHAR(50) - Destination bin
    - `batch_number` VARCHAR(100) - Batch number for batch-managed items
    - `serial_numbers` TEXT - JSON array of serial numbers for serial-managed items
    - `qc_status` VARCHAR(20) - pending, approved, rejected
    - `validation_status` VARCHAR(20) - pending, validated, failed
    - `validation_error` TEXT - Validation error messages
    - `created_at` DATETIME - Creation timestamp
    - `updated_at` DATETIME - Last update timestamp
  - **Document Number Series**:
    - Added 'DIRECT_INVENTORY_TRANSFER' series with prefix 'DIT'
- **Application Enhancements**:
  - Added custom Jinja2 filter `from_json` for parsing JSON serial numbers in templates
  - Integrated SAP B1 validation for item codes and warehouse/bin locations
  - Automatic detection of serial/batch managed items via SAP API
  - QC approval workflow before posting to SAP B1
  - Dynamic form fields based on item management type
- **Routes Added**: 
  - `/direct-inventory-transfer/` - Index page with pagination
  - `/direct-inventory-transfer/create` - Create new transfer
  - `/direct-inventory-transfer/<id>` - Transfer detail view
  - `/direct-inventory-transfer/<id>/add_item` - Add item via barcode
  - `/direct-inventory-transfer/<id>/submit` - Submit for QC approval
  - `/direct-inventory-transfer/<id>/approve` - QC approve and post to SAP
  - `/direct-inventory-transfer/<id>/reject` - QC reject transfer
  - `/direct-inventory-transfer/api/validate-item` - Validate item code from SAP
  - `/direct-inventory-transfer/api/get-warehouses` - Fetch warehouse list
  - `/direct-inventory-transfer/api/get-bins` - Fetch bin locations
- **Notes**: 
  - Fully integrated with SAP B1 Service Layer API
  - Supports serial and batch number tracking
  - QC approval workflow ensures data quality
  - Barcode-driven scanning for warehouse efficiency
  - Custom filter required to parse JSON serial numbers in templates

### 2025-10-15 - SAP B1 JSON Consolidation Fixes
- **File**: `sap_integration.py` (create_purchase_delivery_note method)
- **Description**: Fixed critical bugs in SAP B1 Purchase Delivery Note JSON generation
- **Status**: ✅ Completed
- **Changes**:
  - **SerialNumbers Array**:
    - Fixed `BaseLineNumber` to use PO BaseLine (`po_line_num`) instead of document line counter
    - Fixed `Quantity` to always be 1.0 for each serial entry (SAP requirement)
    - Fixed line-level `Quantity` to sum all serial quantities correctly
    - Fixed date format to YYYY-MM-DD (removed ISO timestamp format)
    - Added proper ManufactureDate and Notes fields
  - **BatchNumbers Array**:
    - Fixed `BaseLineNumber` to use PO BaseLine (`po_line_num`) instead of document line counter
    - Fixed line-level `Quantity` to sum all batch quantities correctly
    - Ensured proper quantity calculation from batch records
- **SAP B1 Integration**:
  - JSON now matches exact SAP B1 Service Layer API format
  - Properly consolidates serial/batch data for posting
  - Eliminates "Quantity: 0.0" errors
  - Fixes BaseLineNumber reference issues
- **Impact**: Critical fix for GRPO posting to SAP B1
- **Notes**: 
  - Validated against user-provided SAP B1 JSON examples
  - Architect-reviewed and approved
  - Ready for production testing

### 2025-10-15 - GRPO Serial and Batch Number Tables
- **File**: `mysql_grpo_serial_batch_migration.py`
- **Description**: Added dedicated tables for serial and batch number management with barcode support
- **Tables Created**: 
  - `grpo_serial_numbers` - Individual serial number tracking
  - `grpo_batch_numbers` - Batch number tracking with quantities
- **Status**: ⏳ Pending
- **Changes**:
  - **grpo_serial_numbers**:
    - `id` INT AUTO_INCREMENT PRIMARY KEY
    - `grpo_item_id` INT NOT NULL (FK to grpo_items)
    - `manufacturer_serial_number` VARCHAR(100) - Manufacturer's serial number
    - `internal_serial_number` VARCHAR(100) UNIQUE NOT NULL - Internal tracking serial (must be unique)
    - `expiry_date` DATE - Expiration date
    - `manufacture_date` DATE - Manufacturing date
    - `notes` TEXT - Additional notes
    - `barcode` VARCHAR(200) - Base64 encoded barcode image
    - `quantity` DECIMAL(15,3) DEFAULT 1.0 - Quantity (typically 1 for serial items)
    - `base_line_number` INT DEFAULT 0 - SAP base line reference
    - `created_at` DATETIME
  - **grpo_batch_numbers**:
    - `id` INT AUTO_INCREMENT PRIMARY KEY
    - `grpo_item_id` INT NOT NULL (FK to grpo_items)
    - `batch_number` VARCHAR(100) NOT NULL - Batch identifier
    - `quantity` DECIMAL(15,3) NOT NULL - Batch quantity
    - `base_line_number` INT DEFAULT 0 - SAP base line reference
    - `manufacturer_serial_number` VARCHAR(100) - Optional manufacturer serial
    - `internal_serial_number` VARCHAR(100) - Optional internal serial
    - `expiry_date` DATE - Batch expiration date
    - `barcode` VARCHAR(200) - Base64 encoded barcode image
    - `created_at` DATETIME
- **SAP B1 Integration**:
  - Supports SAP DocumentLines SerialNumbers array format
  - Supports SAP DocumentLines BatchNumbers array format
  - Each serial entry generates unique barcode for tracking
- **Notes**: 
  - Internal serial numbers must be unique across the system
  - Supports quantity-based entry for serial items
  - Barcode generation using QRCode library

---

### 2025-10-17 - GRPO Dynamic Batch/Serial Field UI Enhancement
- **File**: `modules/grpo/templates/grpo_detail.html`
- **Description**: Enhanced GRPO module with dynamic batch/serial number field management based on SAP item validation
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **Dynamic Field Control**:
    - Added JavaScript function `validateItemCodeFromSAP()` to fetch item validation from SAP B1
    - Implemented automatic show/hide logic for Batch Number vs Serial Number fields
    - Fields now dynamically enable based on SAP ItemCode validation response (BatchNum='Y' or SerialNum='Y')
  - **Serial Number Management**:
    - Added `serial_section` container with dynamic serial number input generation
    - Serial inputs automatically generated based on received quantity (up to 100 items)
    - Each serial number input includes barcode generation capability
    - Added `prepareSerialDataForSubmit()` function to collect serial data as JSON before form submission
  - **Batch Number Management**:
    - Batch fields shown only when item is batch-managed (BatchNum='Y')
    - Expiration date field linked to batch selection
  - **Barcode Generation**:
    - Automatic barcode generation for each serial number with format `SN:{ItemCode}-{SerialNumber}`
    - Visual barcode preview for individual serial entries
  - **Validation**:
    - Client-side validation ensures all serial numbers are entered before submission
    - Serial data stored in hidden field `serial_numbers_json` as JSON array
    - Backend validates serial count matches received quantity
- **API Integration**:
  - Uses existing `/grpo/validate-item/<item_code>` endpoint to fetch item management type
  - Response fields: `batch_required`, `serial_required`, `manage_method`
  - Integrates with SAP B1 SQL Query 'ItemCode_Batch_Serial_Val'
- **User Experience**:
  - Clean, intuitive interface showing only relevant fields
  - No manual dropdown switching - fields appear automatically
  - Quantity change triggers serial input regeneration
  - Supports up to 100 serial numbers via UI (with bulk upload fallback for larger quantities)
- **Database Impact**: No schema changes - uses existing `grpo_serial_numbers` and `grpo_batch_numbers` tables
- **Notes**: 
  - Frontend-only enhancement, no backend route changes required
  - Compatible with existing GRPO workflow and SAP B1 posting logic
  - Improves data entry efficiency for warehouse operators

---

### 2025-10-15 - GRPO Item Validation Fields (Batch/Serial Requirements)
- **File**: `mysql_grpo_item_validation_migration.py`
- **Description**: Added ItemCode validation fields to GRPO items for batch and serial number management
- **Tables Affected**: grpo_items
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - Added `batch_required` VARCHAR(1) DEFAULT 'N' to `grpo_items` - Indicates if batch number is required (Y/N)
  - Added `serial_required` VARCHAR(1) DEFAULT 'N' to `grpo_items` - Indicates if serial number is required (Y/N)
  - Added `manage_method` VARCHAR(1) DEFAULT 'N' to `grpo_items` - Item management method (A=Average, R=FIFO/Release, N=None)
- **API Integration**:
  - Added SAP API method `validate_item_code()` in `sap_integration.py` to call SQLQuery 'ItemCode_Batch_Serial_Val'
  - Added validation endpoint `/grpo/validate-item/<item_code>` in GRPO routes
  - Frontend dynamically enables/disables batch and serial number fields based on SAP validation
- **Notes**: 
  - Validation is performed via SAP B1 SQL Query: `SQLQueries('ItemCode_Batch_Serial_Val')/List`
  - Fields are dynamically enabled/disabled in the GRPO detail modal based on item properties
  - Supports FIFO/Release method (R) for quantity-based management

---

### 2025-10-15 - GRPO Automatic Barcode Generation Enhancement
- **File**: `mysql/changes/2025-10-15_grpo_barcode_enhancements.sql`
- **Description**: Enhanced GRPO module with automatic barcode generation for serial and batch managed items
- **Tables Affected**: grpo_serial_numbers, grpo_batch_numbers (existing tables)
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - **Application Logic Enhancements**:
    - Auto-detect item type (Serial/Batch/Non-Batch) via SAP B1 API endpoint `SQLQueries('ItemCode_Batch_Serial_Val')/List`
    - Automatically generate QR code barcodes when serial/batch items are added to GRPO
    - Store barcodes as base64 encoded PNG images in database
    - Display barcodes in GRPO detail view for scanning/printing
  - **Barcode Formats**:
    - Serial Items: `SN:{internal_serial_number}`
    - Batch Items: `BATCH:{batch_number}`
  - **JavaScript Enhancements**:
    - Real-time item type validation on item code entry
    - Dynamic show/hide of serial/batch input fields
    - Automatic serial number input generation based on quantity
  - **SAP B1 Integration**:
    - JSON consolidation for Purchase Delivery Note creation
    - Proper SerialNumbers and BatchNumbers array formatting
    - Support for ManufacturerSerialNumber, InternalSerialNumber, ExpiryDate, ManufactureDate
- **Routes Updated**: 
  - `/grpo/<grpo_id>/add_item` - Enhanced with barcode generation
  - `/grpo/validate-item/<item_code>` - Item type validation via SAP
- **Notes**: 
  - No schema changes required - barcode fields already existed
  - Enhancement focuses on automatic generation and proper SAP integration
  - Barcodes generated using QRCode library with error correction level L

---

### 2025-10-14 - MultiGRN Serial/Batch Number Support and Barcode Generation
- **File**: `mysql/changes/2025-10-14_multi_grn_enhancements.sql`
- **Description**: Added serial/batch number support and barcode generation to MultiGRN module
- **Tables Affected**: multi_grn_batches, multi_grn_line_selections
- **Status**: ✅ Applied
- **Applied By**: System
- **Changes**:
  - Added `batch_number` VARCHAR(50) UNIQUE column to `multi_grn_batches` for better tracking
  - Added `serial_numbers` TEXT column to `multi_grn_line_selections` to store serial number data (JSON format)
  - Added `batch_numbers` TEXT column to `multi_grn_line_selections` to store batch number data (JSON format)
  - Added `barcode_generated` BOOLEAN column to `multi_grn_line_selections` to track barcode generation status
  - Created index on `multi_grn_batches.batch_number` for faster lookups
  - Created index on `multi_grn_line_selections.barcode_generated` for filtering
- **Notes**: 
  - Serial and batch numbers are stored as JSON text for flexibility with SAP B1 API format
  - Batch numbers are auto-generated with format: MGRN-YYYYMMDDHHmmss
  - Barcode generation API endpoint added at `/multi-grn/api/generate-barcode`

---

### Template for New Migration Entry
```markdown
### YYYY-MM-DD HH:MM - Migration Title
- **File**: `mysql/changes/YYYY-MM-DD_HH-MM_description.sql`
- **Description**: Brief description of changes
- **Tables Affected**: table1, table2
- **Status**: ✅ Applied / ⏳ Pending / ❌ Failed / 🔄 Rolled Back
- **Applied By**: Developer Name
- **Notes**: Any important notes or dependencies
```

---

## Migration Guidelines

### When to Create a Migration
1. Adding/removing tables
2. Adding/removing columns
3. Changing column types or constraints
4. Adding/removing indexes
5. Modifying foreign key relationships
6. Data transformations

### Migration Checklist
- [ ] Create migration file with proper naming
- [ ] Include UP and DOWN SQL
- [ ] Add entry to this log
- [ ] Test on development database
- [ ] Document any manual steps required
- [ ] Update schema documentation if needed

### Rollback Procedure
If a migration needs to be rolled back:
1. Run the DOWN SQL (from comments in migration file)
2. Update status in this log to 🔄 Rolled Back
3. Document reason for rollback
4. Create new migration if changes are still needed

---

## Notes
- This system tracks MySQL migrations for secondary database support
- Primary PostgreSQL database uses SQLAlchemy ORM migrations
- Always keep this log updated when making schema changes
- Each migration should be atomic and reversible