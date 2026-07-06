"""
Setup additional tables in the database
Runs the additional_tables.sql script
"""

import psycopg2
import os
from pathlib import Path

# Database connection
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASS = "root"
DB_NAME = "rm_ai_advisory"

print("=" * 60)
print("SETTING UP ADDITIONAL TABLES")
print("=" * 60)

try:
    # Connect to database
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )
    print(f"\n✅ Connected to database: {DB_NAME}")
    
    # Read SQL file
    sql_file = Path(__file__).parent.parent / "db" / "additional_tables.sql"
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    # Execute SQL
    cursor = conn.cursor()
    cursor.execute(sql)
    conn.commit()
    
    print("✅ Additional tables created successfully!")
    
    # Verify tables exist
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        AND table_name IN ('conversations', 'fd_rates')
        ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"\n📋 New tables created:")
    for table in tables:
        print(f"   - {table[0]}")
        
        # Show row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"     Rows: {count}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPlease check:")
    print("1. PostgreSQL is running")
    print("2. Database 'rm_ai_advisory' exists")
    print("3. User 'postgres' with password 'root' has access")
