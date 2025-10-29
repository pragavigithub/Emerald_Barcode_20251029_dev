# Database Migration Tracking System

## Overview
This directory contains MySQL migration files to track all database schema changes for the Warehouse Management System.

## Directory Structure
```
migrations/
├── README.md                 # This file
├── MIGRATION_LOG.md         # Chronological log of all migrations
├── mysql/
│   ├── schema/              # Full schema definitions
│   │   └── initial_schema.sql
│   └── changes/             # Incremental migration files
│       └── YYYY-MM-DD_description.sql
```

## Migration Naming Convention
All migration files in `mysql/changes/` should follow this format:
- **Format**: `YYYY-MM-DD_HH-MM_description.sql`
- **Example**: `2025-10-13_12-30_add_multi_grn_tables.sql`

## How to Create a New Migration

### 1. Create Migration File
When you make database changes, create a new migration file:
```bash
# Create a new migration file
touch migrations/mysql/changes/$(date +%Y-%m-%d_%H-%M)_your_description.sql
```

### 2. Write Migration SQL
Include both UP (apply) and DOWN (rollback) migrations:
```sql
-- Migration: Add new column to users table
-- Date: 2025-10-13
-- Author: Developer Name
-- Description: Adding phone number field to users

-- ==================== UP ====================
ALTER TABLE users 
ADD COLUMN phone_number VARCHAR(20) DEFAULT NULL;

-- ==================== DOWN ====================
-- ALTER TABLE users DROP COLUMN phone_number;
```

### 3. Update Migration Log
Add an entry to `MIGRATION_LOG.md`:
```markdown
## 2025-10-13 12:30 - Add phone number to users
- **File**: `2025-10-13_12-30_add_phone_number.sql`
- **Description**: Added phone_number column to users table
- **Tables Affected**: users
- **Status**: Applied
```

### 4. Apply Migration
```bash
# Apply to MySQL database
mysql -u username -p database_name < migrations/mysql/changes/2025-10-13_12-30_add_phone_number.sql
```

## Current Schema
The initial schema is documented in `mysql/schema/initial_schema.sql` and includes:

### Core Tables
- **users** - User accounts and authentication
- **branches** - Branch/location information
- **user_sessions** - Session tracking
- **password_reset_tokens** - Password reset functionality

### GRPO Module
- **grpo_documents** - Goods Receipt PO documents
- **grpo_items** - GRPO line items

### Inventory Transfer Module
- **inventory_transfers** - Transfer documents
- **inventory_transfer_items** - Transfer line items

### Multi GRN Module
- **multi_grn_batches** - GRN batch headers
- **multi_grn_po_links** - PO links to batches
- **multi_grn_line_selections** - Selected line items

### Pick List Module
- **pick_lists** - Pick list documents
- **pick_list_items** - Pick list items
- **pick_list_lines** - Pick list lines
- **pick_list_bin_allocations** - Bin allocations

### Serial Number Tracking
- **serial_number_transfers** - Serial transfer documents
- **serial_number_transfer_items** - Serial transfer items
- **serial_number_transfer_serials** - Individual serial numbers

### Supporting Tables
- **bin_locations** - Warehouse bin locations
- **bin_items** - Items in bins
- **bin_scanning_logs** - Bin scanning activity
- **barcode_labels** - Generated barcode labels
- **qr_code_labels** - Generated QR labels
- **document_number_series** - Auto-number sequences
- **inventory_counts** - Inventory counting tasks
- **inventory_count_items** - Count items
- **sales_orders** - Sales order integration
- **sales_order_lines** - Sales order lines

## Best Practices

1. **Always backup** before applying migrations
2. **Test migrations** on development database first
3. **Include rollback** SQL in comments
4. **Document dependencies** between migrations
5. **Keep migrations small** and focused
6. **Never modify** existing migration files
7. **Update MIGRATION_LOG.md** immediately after creating a migration

## PostgreSQL vs MySQL
This project uses PostgreSQL as the primary database in Replit environment. MySQL migrations are maintained for:
- Local development environments
- Legacy system compatibility
- Multi-database support scenarios

## Automatic Schema Generation
To generate current schema from models:
```bash
# Using SQLAlchemy models
python scripts/generate_schema.py
```

## Migration Status
See `MIGRATION_LOG.md` for complete migration history and current database version.