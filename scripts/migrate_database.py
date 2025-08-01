#!/usr/bin/env python3
"""
Database migration script for ADAS Diagnostics Co-pilot.

This script adds session management tables to existing databases.
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

async def run_migration():
    """Run the database migration."""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your PostgreSQL connection string")
        print("Example: postgresql://user:password@localhost:5435/database")
        return False
    
    try:
        print("🔄 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Read migration script
        migration_file = Path("sql/migrate_add_sessions.sql")
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        migration_sql = migration_file.read_text()
        
        print("🔄 Running session management migration...")
        await conn.execute(migration_sql)
        
        print("✅ Migration completed successfully!")
        
        # Test the new tables
        print("🧪 Testing new tables...")
        
        # Test sessions table
        session_count = await conn.fetchval("SELECT COUNT(*) FROM sessions")
        print(f"✅ Sessions table accessible (current count: {session_count})")
        
        # Test messages table
        message_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
        print(f"✅ Messages table accessible (current count: {message_count})")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

async def main():
    """Main function."""
    print("🚗 Mercedes-Benz E-Class Diagnostics Co-pilot")
    print("📊 Database Migration Tool")
    print("=" * 50)
    
    success = await run_migration()
    
    if success:
        print("\n🎉 Database migration completed successfully!")
        print("✅ Session management is now available")
        print("✅ Chat history will be persistent")
    else:
        print("\n❌ Migration failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
