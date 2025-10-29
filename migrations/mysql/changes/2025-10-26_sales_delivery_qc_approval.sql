-- Sales Delivery QC Approval Fields Migration
-- Created: 2025-10-26
-- Description: Adds QC approval workflow fields to sales delivery module

-- Add QC approval fields to delivery_documents table
ALTER TABLE delivery_documents 
ADD COLUMN qc_approver_id INT NULL AFTER user_id,
ADD COLUMN qc_approved_at DATETIME NULL AFTER qc_approver_id,
ADD COLUMN qc_notes TEXT NULL AFTER qc_approved_at,
ADD CONSTRAINT fk_delivery_qc_approver FOREIGN KEY (qc_approver_id) REFERENCES users(id);

-- Update status column comment to reflect new statuses
ALTER TABLE delivery_documents
MODIFY COLUMN status VARCHAR(20) DEFAULT 'draft' COMMENT 'draft, submitted, qc_approved, posted, rejected';

-- Add QC status field to delivery_items table
ALTER TABLE delivery_items
ADD COLUMN qc_status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, approved, rejected' AFTER warehouse_routing;

-- Add indexes for QC queries
CREATE INDEX idx_delivery_status ON delivery_documents(status);
CREATE INDEX idx_delivery_qc_approved_at ON delivery_documents(qc_approved_at);
CREATE INDEX idx_delivery_item_qc_status ON delivery_items(qc_status);
