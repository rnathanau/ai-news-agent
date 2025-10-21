#!/usr/bin/env python3
"""
Quick script to add delivery_slot column to production database.
Run this via Render Shell: python add_delivery_slot.py
"""

import os
import sys

# Add backend to path
sys.path.insert(0, 'backend')

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def add_column():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ ERROR: DATABASE_URL not found")
        return False
    
    # Handle Render's postgres:// URL
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print("🔗 Connecting to database...")
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Add the column
                print("📝 Adding delivery_slot column...")
                conn.execute(text("""
                    ALTER TABLE user_preferences 
                    ADD COLUMN IF NOT EXISTS delivery_slot VARCHAR(20) DEFAULT 'morning'
                """))
                
                # Update any NULL values
                conn.execute(text("""
                    UPDATE user_preferences 
                    SET delivery_slot = 'morning' 
                    WHERE delivery_slot IS NULL
                """))
                
                trans.commit()
                print("✅ Column added successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Adding delivery_slot column to user_preferences")
    print("=" * 60)
    success = add_column()
    print("=" * 60)
    sys.exit(0 if success else 1)

