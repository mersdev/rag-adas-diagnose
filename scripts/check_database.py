#!/usr/bin/env python3
"""
Database check script for ADAS Diagnostics Co-pilot.

This script checks if all required tables exist in the database.
"""

import asyncio
import asyncpg
import os
import sys

async def check_database():
    """Check database tables and structure."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        print("Example: postgresql://user:password@localhost:5432/database")
        return False
    
    try:
        print("🔄 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Check required tables
        required_tables = [
            'documents',
            'chunks', 
            'sessions',
            'messages'
        ]
        
        print("🔍 Checking required tables...")
        
        all_tables_exist = True
        for table in required_tables:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
            """, table)
            
            if exists:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"✅ {table} table exists (records: {count})")
            else:
                print(f"❌ {table} table missing")
                all_tables_exist = False
        
        # Check session management specific columns
        if all_tables_exist:
            print("\n🔍 Checking session table structure...")
            
            # Check sessions table columns
            sessions_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'sessions'
                ORDER BY ordinal_position
            """)
            
            expected_sessions_columns = ['id', 'user_id', 'metadata', 'created_at', 'updated_at', 'expires_at']
            actual_sessions_columns = [row['column_name'] for row in sessions_columns]
            
            for col in expected_sessions_columns:
                if col in actual_sessions_columns:
                    print(f"✅ sessions.{col} exists")
                else:
                    print(f"❌ sessions.{col} missing")
                    all_tables_exist = False
            
            # Check messages table columns
            print("\n🔍 Checking messages table structure...")
            
            messages_columns = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'messages'
                ORDER BY ordinal_position
            """)
            
            expected_messages_columns = ['id', 'session_id', 'role', 'content', 'metadata', 'created_at']
            actual_messages_columns = [row['column_name'] for row in messages_columns]
            
            for col in expected_messages_columns:
                if col in actual_messages_columns:
                    print(f"✅ messages.{col} exists")
                else:
                    print(f"❌ messages.{col} missing")
                    all_tables_exist = False
        
        await conn.close()
        return all_tables_exist
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

async def main():
    """Main function."""
    print("🚗 Mercedes-Benz E-Class Diagnostics Co-pilot")
    print("🔍 Database Structure Check")
    print("=" * 50)
    
    success = await check_database()
    
    if success:
        print("\n🎉 Database structure is complete!")
        print("✅ All required tables exist")
        print("✅ Session management is available")
    else:
        print("\n❌ Database structure is incomplete")
        print("💡 Run 'python migrate_database.py' to add missing tables")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
