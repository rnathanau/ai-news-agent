"""Migration script to convert delivery_slot to delivery_slots array."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DATABASE_URL

def migrate():
    """Migrate delivery_slot to delivery_slots."""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        try:
            # Check if delivery_slots column exists
            result = session.execute(text("PRAGMA table_info(user_preferences)"))
            columns = {row[1]: row for row in result.fetchall()}
            
            has_delivery_slots = 'delivery_slots' in columns
            has_delivery_slot = 'delivery_slot' in columns
            
            print(f"Has delivery_slots column: {has_delivery_slots}")
            print(f"Has delivery_slot column: {has_delivery_slot}")
            
            # Add delivery_slots column if it doesn't exist
            if not has_delivery_slots:
                print("Adding delivery_slots column...")
                session.execute(text(
                    "ALTER TABLE user_preferences ADD COLUMN delivery_slots JSON DEFAULT '[]'"
                ))
                session.commit()
                print("✓ Added delivery_slots column")
            
            # Migrate data from delivery_slot to delivery_slots if old column exists
            if has_delivery_slot:
                print("Migrating data from delivery_slot to delivery_slots...")
                # Get all rows with delivery_slot
                result = session.execute(text(
                    "SELECT id, delivery_slot FROM user_preferences WHERE delivery_slot IS NOT NULL"
                ))
                rows = result.fetchall()
                
                for row in rows:
                    user_id, delivery_slot = row
                    # Convert single slot to array format
                    slots_json = f'["{delivery_slot}"]'
                    session.execute(text(
                        "UPDATE user_preferences SET delivery_slots = :slots WHERE id = :id"
                    ), {"slots": slots_json, "id": user_id})
                
                session.commit()
                print(f"✓ Migrated {len(rows)} rows")
            
            # Set default for rows with empty delivery_slots
            print("Setting default delivery_slots for rows without any...")
            session.execute(text(
                """UPDATE user_preferences 
                   SET delivery_slots = '["morning"]' 
                   WHERE delivery_slots IS NULL OR delivery_slots = '[]'"""
            ))
            session.commit()
            print("✓ Set defaults")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()

