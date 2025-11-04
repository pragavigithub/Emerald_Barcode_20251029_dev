-- Migration: Add support for non-batch, non-serial managed items in GRPO
-- Date: 2025-11-03
-- Description: Creates table for storing non-managed items (when both BatchNum='N' and SerialNum='N')
--              with support for number of bags and QR code label generation

-- Create grpo_non_managed_items table
CREATE TABLE IF NOT EXISTS grpo_non_managed_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grpo_item_id INT NOT NULL,
    quantity  INT NOT NULL,
    base_line_number INT DEFAULT 0,
    expiry_date DATE NULL,
    admin_date DATE NULL,
    grn_number VARCHAR(50) NULL,
    qty_per_pack DECIMAL(15,3) NULL,
    no_of_packs INT DEFAULT 1,
    pack_number INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_grpo_non_managed_items_item_id 
        FOREIGN KEY (grpo_item_id) 
        REFERENCES grpo_items(id) 
        ON DELETE CASCADE,
    
    -- Indexes for performance
    INDEX idx_grpo_item_id (grpo_item_id),
    INDEX idx_grn_number (grn_number),
    INDEX idx_created_at (created_at),
    INDEX idx_pack_number (pack_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add comment to table
ALTER TABLE grpo_non_managed_items COMMENT = 
'Non-batch, non-serial managed items for GRPO. Used when both BatchNum=N and SerialNum=N. Supports number of bags for QR label generation.';
