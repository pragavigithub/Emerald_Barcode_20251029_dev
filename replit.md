# Warehouse Management System (WMS)

## Overview
A Flask-based Warehouse Management System (WMS) designed to streamline inventory operations by integrating seamlessly with SAP for functionalities such as barcode scanning, goods receipt, pick list generation, and inventory transfers. The system aims to enhance efficiency, accuracy, and control over warehouse logistics, ultimately minimizing manual errors and maximizing throughput for small to medium-sized enterprises.

## User Preferences
*   Keep MySQL migration files updated when database schema changes occur
*   SQL query validation should only run on initial startup, not on every application restart

## Recent Changes

### 2025-11-03
*   **Optimized SAP SQL Query Validation**: Modified SAP B1 SQL query validation to run only on initial startup instead of every restart, improving startup performance and avoiding repeated connection attempts when SAP is unavailable. Implemented flag-based system at `.local/state/sap_queries_validated.flag` that records validation attempts (success/failure) and prevents re-runs on subsequent restarts. Added `FORCE_SAP_VALIDATION` environment variable to allow manual re-validation when needed.

### 2025-10-31
*   **Fixed Inventory Counting UI Issue**: Resolved issue where SAP Inventory Counting documents (counted and posted) were not displaying in the UI. Added dashboard statistics card, recent activities section, and comprehensive history page (`/inventory_counting_history`) to view all counted documents with filtering capabilities.

## System Architecture
The system is built on a Flask web application backend, utilizing Jinja2 for server-side rendering. A core architectural decision is the deep integration with the SAP B1 Service Layer API for all critical warehouse operations, ensuring data consistency and real-time updates. PostgreSQL is the primary database target for cloud deployments, with SQLite serving as a fallback. User authentication uses Flask-Login with robust role-based access control. The application is designed for production deployment using Gunicorn with autoscale capabilities.

**Key Features:**
*   **User Management:** Comprehensive authentication, role-based access, and self-service profile management with deactivation for audit trails.
*   **GRPO Management:** Standard Goods Receipt PO processing, intelligent batch/serial field management, and a module for batch creation of multiple GRNs from multiple Purchase Orders via a 5-step workflow with SAP B1 integration. It includes dynamic batch/serial detection and specific entry processes for serial and batch numbers.
*   **Inventory Transfer:** Enhanced module for creating inventory transfer requests with document series selection and SAP B1 validation. Includes ItemCode validation with automatic item type detection (Serial/Batch/Non-Managed) and dynamic warehouse selection based on real-time SAP B1 data using SQL Query APIs (`GetSerialManagedItemWH`, `GetBatchManagedItemWH`, `GetNonSerialNonBatchManagedItemWH`).
*   **Direct Inventory Transfer:** Barcode-based inventory transfer module with automatic serial/batch detection, real-time SAP B1 validation, intelligent serial number tracking, batch number validation, warehouse and bin selection via SAP, QC approval workflow, and direct posting to SAP B1 as StockTransfers documents.
*   **Sales Order Against Delivery:** Module for creating Delivery Notes against Sales Orders with SAP B1 integration, including SO series dropdown selection with proper series name display, cascading dropdown for open SO document numbers (using SQL Query `Get_Open_SO_DocNum` with OData fallback), document loading, item picking with batch/serial validation, individual QR code label generation, and direct SAP B1 posting. The module follows the same UI pattern as GRPO for consistency.
*   **Pick List Management:** Generation and processing of pick lists.
*   **Barcode Scanning:** Integrated camera-based scanning for various modules (GRPO, Bin Scanning, Pick List, Inventory Transfer, Barcode Reprint).
*   **Inventory Counting:** SAP B1 integrated inventory counting with local PostgreSQL database storage for tracking, audit trails, user tracking, and timestamps. Includes a comprehensive history view for all counted and posted documents, with dashboard integration showing statistics and recent counting activities.
*   **Branch Management:** Functionality for managing different warehouse branches.
*   **Quality Control Dashboard:** Provides oversight for quality processes.
*   **UI/UX:** Focuses on intuitive workflows for managing inventory, including serial number transfers and real-time validation against SAP B1.
*   **Database Migrations:** A comprehensive MySQL migration tracking system is in place for schema changes, complementing the primary PostgreSQL strategy.

**Technical Implementations:**
*   **SAP B1 Integration:** Utilizes a dedicated `SAPMultiGRNService` class for secure and robust communication with the SAP B1 Service Layer, including SSL/TLS verification and optimized OData filtering.
*   **Modular Design:** New features are implemented as modular blueprints with their own templates and services.
*   **Frontend:** Jinja2 templating with JavaScript libraries like Select2 for enhanced UI components.
*   **Error Handling:** Comprehensive validation and error logging for API communications and user inputs.

## External Dependencies
*   **SAP B1 Service Layer API**: For all core inventory and document management functionalities (GRPO, pick lists, inventory transfers, serial numbers, business partners, inventory counts).
*   **PostgreSQL**: Primary relational database for production environments.
*   **SQLite**: Local relational database for development and initial setup.
*   **Gunicorn**: WSGI HTTP server for deploying the Flask application in production.
*   **Flask-Login**: Library for managing user sessions and authentication.