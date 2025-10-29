# Keep MySQL Migrations Updated - Quick Reference

## Important Reminder
Every time you make database changes to your models, you MUST create a corresponding MySQL migration file to keep the MySQL schema in sync with PostgreSQL.

## When to Create a Migration

### Always create a migration when you:
1. **Add or remove a table** in any model file
2. **Add or remove a column** from existing tables
3. **Change column types** (e.g., VARCHAR(50) → VARCHAR(100))
4. **Modify constraints** (nullable, unique, default values)
5. **Add or remove indexes** or foreign keys
6. **Rename tables or columns**

## Files to Monitor for Changes

### Core Models
- `models.py` - User, Branch, Session, PasswordResetToken
- `models_extensions.py` - Extended models (GRPO, Pick List, Inventory, etc.)

### Module Models
- `modules/multi_grn_creation/models.py` - Multi GRN tables
- `modules/grpo/models.py` - GRPO-specific tables (if exists)
- `modules/inventory_transfer/models.py` - Inventory transfer tables (if exists)
- `modules/serial_item_transfer/models.py` - Serial transfer tables (if exists)

## Quick Migration Creation Process

### Step 1: Create Migration File
```bash
touch migrations/mysql/changes/$(date +%Y-%m-%d_%H-%M)_your_description.sql
```

Example: `2025-10-13_15-30_add_customer_phone_column.sql`

### Step 2: Write Migration SQL
```sql
-- Migration: Add customer phone column
-- Date: 2025-10-13
-- Author: Your Name
-- Description: Adding phone number field to customer data

-- ==================== UP ====================
ALTER TABLE users 
ADD COLUMN phone_number VARCHAR(20) DEFAULT NULL;

CREATE INDEX idx_users_phone ON users(phone_number);

-- ==================== DOWN ====================
-- DROP INDEX idx_users_phone ON users;
-- ALTER TABLE users DROP COLUMN phone_number;
```

### Step 3: Update Migration Log
Edit `migrations/MIGRATION_LOG.md` and add your migration:

```markdown
### 2025-10-13 15:30 - Add Customer Phone Column
- **File**: `mysql/changes/2025-10-13_15-30_add_customer_phone_column.sql`
- **Description**: Added phone_number column to users table with index
- **Tables Affected**: users
- **Status**: ✅ Applied
- **Applied By**: Your Name
- **Notes**: Added for customer contact tracking feature
```

## Common Migration Examples

### Adding a New Table
```sql
-- ==================== UP ====================
CREATE TABLE customer_notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_code VARCHAR(50) NOT NULL,
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_customer_code (customer_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== DOWN ====================
-- DROP TABLE customer_notes;
```

### Adding a Column
```sql
-- ==================== UP ====================
ALTER TABLE grpo_documents 
ADD COLUMN delivery_date DATE DEFAULT NULL;

-- ==================== DOWN ====================
-- ALTER TABLE grpo_documents DROP COLUMN delivery_date;
```

### Modifying a Column
```sql
-- ==================== UP ====================
ALTER TABLE users 
MODIFY COLUMN email VARCHAR(255) NOT NULL;

-- ==================== DOWN ====================
-- ALTER TABLE users MODIFY COLUMN email VARCHAR(120) NOT NULL;
```

### Adding an Index
```sql
-- ==================== UP ====================
CREATE INDEX idx_grpo_doc_number ON grpo_documents(doc_num);

-- ==================== DOWN ====================
-- DROP INDEX idx_grpo_doc_number ON grpo_documents;
```

## Checklist for Every Database Change

- [ ] Modified a model file (models.py, models_extensions.py, or module models)
- [ ] Created migration file in `migrations/mysql/changes/`
- [ ] Wrote UP migration SQL (apply changes)
- [ ] Wrote DOWN migration SQL (rollback changes) in comments
- [ ] Added entry to `migrations/MIGRATION_LOG.md`
- [ ] Tested migration on development database (if applicable)
- [ ] Committed migration files to version control

## Why This Matters

This application supports dual databases:
- **PostgreSQL** (Primary) - Used in Replit environment, automatically synced from SQLAlchemy models
- **MySQL** (Secondary) - Used in local/production environments, requires manual migrations

Keeping migrations updated ensures:
- Local development environments stay in sync
- Production MySQL deployments can be safely updated
- Schema changes are documented and reversible
- Team members can track database evolution

## Quick Reference Commands

### Create migration file:
```bash
touch migrations/mysql/changes/$(date +%Y-%m-%d_%H-%M)_description.sql
```

### Apply migration to MySQL:
```bash
mysql -u username -p database_name < migrations/mysql/changes/YYYY-MM-DD_HH-MM_description.sql
```

### View migration log:
```bash
cat migrations/MIGRATION_LOG.md
```

## Need Help?

- See full documentation: `migrations/README.md`
- View migration history: `migrations/MIGRATION_LOG.md`
- Example migrations: `migrations/mysql/changes/` (once created)
- Initial schema reference: `migrations/mysql/schema/initial_schema.sql`
