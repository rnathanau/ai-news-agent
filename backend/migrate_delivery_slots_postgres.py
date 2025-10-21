"""Migration script to convert delivery_slot to delivery_slots array - PostgreSQL version."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DATABASE_URL

def migrate():
    """Migrate delivery_slot to delivery_slots for PostgreSQL."""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        try:
            # Check if delivery_slots column exists (PostgreSQL way)
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user_preferences' 
                AND column_name='delivery_slots'
            """))
            has_delivery_slots = result.fetchone() is not None
            
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='user_preferences' 
                AND column_name='delivery_slot'
            """))
            has_delivery_slot = result.fetchone() is not None
            
            print(f"Has delivery_slots column: {has_delivery_slots}")
            print(f"Has delivery_slot column: {has_delivery_slot}")
            
            # Add delivery_slots column if it doesn't exist
            if not has_delivery_slots:
                print("Adding delivery_slots column...")
                session.execute(text("""
                    ALTER TABLE user_preferences 
                    ADD COLUMN delivery_slots JSON DEFAULT '[]'::json
                """))
                session.commit()
                print("✓ Added delivery_slots column")
            else:
                print("Column delivery_slots already exists, skipping creation")
            
            # Migrate data from delivery_slot to delivery_slots if old column exists
            if has_delivery_slot:
                print("Migrating data from delivery_slot to delivery_slots...")
                
                # Get all rows with delivery_slot
                result = session.execute(text("""
                    SELECT id, delivery_slot 
                    FROM user_preferences 
                    WHERE delivery_slot IS NOT NULL
                """))
                rows = result.fetchall()
                
                for row in rows:
                    user_id, delivery_slot = row
                    # Convert single slot to JSON array format
                    session.execute(text("""
                        UPDATE user_preferences 
                        SET delivery_slots = :slots::json
                        WHERE id = :id
                    """), {"slots": f'["{delivery_slot}"]', "id": user_id})
                
                session.commit()
                print(f"✓ Migrated {len(rows)} rows")
            else:
                print("Old delivery_slot column not found, skipping data migration")
            
            # Set default for rows with empty delivery_slots
            print("Setting default delivery_slots for rows without any...")
            result = session.execute(text("""
                UPDATE user_preferences 
                SET delivery_slots = '["morning"]'::json
                WHERE delivery_slots IS NULL 
                   OR delivery_slots::text = '[]'
                   OR delivery_slots::text = 'null'
            """))
            session.commit()
            print(f"✓ Set defaults for {result.rowcount} rows")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    migrate()

