-- Add delivery_slot column to user_preferences table
-- Run this on your Render PostgreSQL database

-- Add the column with a default value
ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS delivery_slot VARCHAR(20) DEFAULT 'morning';

-- Update any existing NULL values to 'morning'
UPDATE user_preferences 
SET delivery_slot = 'morning' 
WHERE delivery_slot IS NULL;

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'user_preferences' 
  AND column_name = 'delivery_slot';


