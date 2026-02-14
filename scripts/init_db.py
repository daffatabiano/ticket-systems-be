#!/usr/bin/env python3
"""
Database initialization script for Complaint Triage System.
This script creates the database and runs the schema.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

def create_database():
    """Create the database if it doesn't exist."""
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    db_name = os.getenv("DB_NAME", "complaint_triage")
    
    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
        (db_name,)
    )
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creating database '{db_name}'...")
        cursor.execute(f'CREATE DATABASE {db_name}')
        print(f"✅ Database '{db_name}' created successfully!")
    else:
        print(f"ℹ️  Database '{db_name}' already exists.")
    
    cursor.close()
    conn.close()

def run_schema():
    """Run the database schema."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_name = os.getenv("DB_NAME", "complaint_triage")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Connect to the database
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # Read schema file
    schema_path = Path(__file__).parent.parent.parent / "database_schema.sql"
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return False
    
    print(f"Running schema from: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Schema executed successfully!")
        
        # Verify tables created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print("\n📋 Created tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error executing schema: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def verify_setup():
    """Verify the database setup."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_name = os.getenv("DB_NAME", "complaint_triage")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("\n🔍 Verification:")
    
    # Check ENUM types
    cursor.execute("""
        SELECT typname FROM pg_type 
        WHERE typname IN ('ticket_category', 'ticket_urgency', 'ticket_status')
        ORDER BY typname
    """)
    enums = cursor.fetchall()
    print(f"\n✅ ENUM types created: {len(enums)}")
    for enum in enums:
        print(f"  - {enum[0]}")
    
    # Check indexes
    cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public' AND tablename = 'tickets'
        ORDER BY indexname
    """)
    indexes = cursor.fetchall()
    print(f"\n✅ Indexes created: {len(indexes)}")
    for idx in indexes[:5]:  # Show first 5
        print(f"  - {idx[0]}")
    if len(indexes) > 5:
        print(f"  ... and {len(indexes) - 5} more")
    
    # Check views
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.views 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    views = cursor.fetchall()
    print(f"\n✅ Views created: {len(views)}")
    for view in views:
        print(f"  - {view[0]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Complaint Triage System - Database Setup")
    print("=" * 60)
    
    try:
        # Step 1: Create database
        create_database()
        
        # Step 2: Run schema
        if run_schema():
            # Step 3: Verify setup
            verify_setup()
            
            print("\n" + "=" * 60)
            print("✅ Database setup completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Start Redis: redis-server")
            print("2. Start Celery worker: celery -A app.workers.celery_worker worker --loglevel=info")
            print("3. Start FastAPI: uvicorn app.main:app --reload")
        else:
            print("\n❌ Database setup failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)
