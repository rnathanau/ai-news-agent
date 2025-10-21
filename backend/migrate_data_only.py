"""Simple data migration - just migrate existing data, column already exists."""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import DATABASE_URL

def migrate():
    """Migrate delivery_slot data to delivery_slots."""
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        try:
            print("Migrating data from delivery_slot to delivery_slots...")
            
            # Get all rows with delivery_slot
            result = session.execute(text("""
                SELECT id, delivery_slot 
                FROM user_preferences 
                WHERE delivery_slot IS NOT NULL
            """))
            rows = result.fetchall()
            print(f"Found {len(rows)} rows to migrate")
            
            for row in rows:
                user_id, delivery_slot = row
                json_value = f'["{delivery_slot}"]'
                print(f"  Migrating user {user_id}: {delivery_slot} -> {json_value}")
                
                # Use string formatting to avoid parameter binding issues
                session.execute(text(f"""
                    UPDATE user_preferences 
                    SET delivery_slots = CAST('{json_value}' AS json)
                    WHERE id = {user_id}
                """))
            
            session.commit()
            print(f"✓ Migrated {len(rows)} rows")
            
            # Set default for rows with empty delivery_slots
            print("\nSetting defaults...")
            result = session.execute(text("""
                UPDATE user_preferences 
                SET delivery_slots = CAST('["morning"]' AS json)
                WHERE delivery_slots IS NULL 
                   OR CAST(delivery_slots AS text) = '[]'
                   OR CAST(delivery_slots AS text) = 'null'
            """))
            session.commit()
            print(f"✓ Set defaults for {result.rowcount} rows")
            
            # Verify
            print("\nVerifying migration...")
            result = session.execute(text("""
                SELECT id, delivery_slots 
                FROM user_preferences 
                LIMIT 5
            """))
            for row in result:
                print(f"  User {row[0]}: {row[1]}")
            
            print("\n✅ Migration completed successfully!")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    migrate()

