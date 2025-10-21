#!/usr/bin/env python3
"""
Database migration script to add delivery_slot column to user_preferences table.

This script can be run directly on Render or locally to update the database schema.

Usage:
    python migrate_add_delivery_slot.py
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_delivery_slot_column():
    """Add delivery_slot column to user_preferences table."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Handle Render's postgres:// URL (SQLAlchemy needs postgresql://)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if column already exists
        if check_column_exists(engine, 'user_preferences', 'delivery_slot'):
            print("✅ Column 'delivery_slot' already exists in user_preferences table")
            print("   No migration needed!")
            return
        
        print("📝 Adding 'delivery_slot' column to user_preferences table...")
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE user_preferences 
                    ADD COLUMN delivery_slot VARCHAR(20) DEFAULT 'morning'
                """))
                
                # Update any existing NULL values
                conn.execute(text("""
                    UPDATE user_preferences 
                    SET delivery_slot = 'morning' 
                    WHERE delivery_slot IS NULL
                """))
                
                # Commit transaction
                trans.commit()
                
                print("✅ Successfully added 'delivery_slot' column!")
                print("   Default value: 'morning'")
                
                # Verify the column was added
                result = conn.execute(text("""
                    SELECT column_name, data_type, column_default 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_preferences' 
                      AND column_name = 'delivery_slot'
                """))
                
                row = result.fetchone()
                if row:
                    print(f"\n📊 Column details:")
                    print(f"   Name: {row[0]}")
                    print(f"   Type: {row[1]}")
                    print(f"   Default: {row[2]}")
                
            except Exception as e:
                trans.rollback()
                raise e
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: Migration failed")
        print(f"   {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 70)
    print("Database Migration: Add delivery_slot Column")
    print("=" * 70)
    print()
    
    add_delivery_slot_column()
    
    print()
    print("=" * 70)
    print("Migration Complete")
    print("=" * 70)


