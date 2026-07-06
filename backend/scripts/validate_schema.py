"""
Schema validation script
Checks that the existing PostgreSQL database has all required tables and columns
"""

import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Database connection
DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:root@localhost:5432/rm_ai_advisory")
# Parse asyncpg URL to psycopg2 format
db_parts = DB_URL.replace("postgresql+asyncpg://", "").split("@")
user_pass = db_parts[0].split(":")
host_db = db_parts[1].split("/")
host_port = host_db[0].split(":")

DB_USER = user_pass[0]
DB_PASS = user_pass[1]
DB_HOST = host_port[0]
DB_PORT = host_port[1] if len(host_port) > 1 else "5432"
DB_NAME = host_db[1]


def validate_schema():
    """Validate database schema against requirements"""
    
    print("=" * 60)
    print("DATABASE SCHEMA VALIDATION")
    print("=" * 60)
    
    # Check database connection
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"\n✅ Database connected: PostgreSQL")
        print(f"   Version: {version[:50]}...")
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        return False
    
    # Check required tables exist
    required_tables = {
        "clients": [
            "client_id", "client_name", "age", "risk_factor", 
            "monthly_income", "city"
        ],
        "portfolios": [
            "client_id", "total_value", "ytd_return"
        ],
        "holdings": [
            "client_id", "asset_type", "ticker", "scheme_name",
            "quantity", "current_value", "sector"
        ]
    }
    
    print("\n" + "=" * 60)
    print("CHECKING EXISTING TABLES")
    print("=" * 60)
    
    all_valid = True
    
    # Get list of all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public'
        ORDER BY table_name
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"\nFound tables: {', '.join(existing_tables)}")
    
    # Check each required table
    for table_name, required_columns in required_tables.items():
        print(f"\n📋 Checking table: {table_name}")
        
        if table_name not in existing_tables:
            print(f"   ❌ Table '{table_name}' NOT FOUND")
            all_valid = False
            continue
        
        print(f"   ✅ Table exists")
        
        # Get columns for this table
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='{table_name}'
            ORDER BY ordinal_position
        """)
        
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Check required columns
        missing_columns = []
        for col in required_columns:
            if col in columns:
                print(f"   ✅ {col} ({columns[col]})")
            else:
                print(f"   ❌ {col} (MISSING)")
                missing_columns.append(col)
                all_valid = False
        
        # Show extra columns (not required but present)
        extra_columns = [c for c in columns if c not in required_columns]
        if extra_columns:
            print(f"   ℹ️  Additional columns: {', '.join(extra_columns)}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   📊 Row count: {count}")
        
        if table_name == "clients" and count < 10:
            print(f"   ⚠️  WARNING: Expected at least 10 clients (spec mentions 30)")
    
    # Check if new tables need to be created
    print("\n" + "=" * 60)
    print("CHECKING NEW TABLES (to be created)")
    print("=" * 60)
    
    new_tables = ["conversations", "fd_rates"]
    for table in new_tables:
        if table in existing_tables:
            print(f"\n✅ {table} - Already exists")
            
            # Show structure
            cursor.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name='{table}'
                ORDER BY ordinal_position
            """)
            for row in cursor.fetchall():
                print(f"   - {row[0]} ({row[1]})")
        else:
            print(f"\n⚠️  {table} - Will be created by running additional_tables.sql")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ SCHEMA VALIDATION PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. If conversations/fd_rates tables don't exist, run:")
        print("   python backend/scripts/setup_tables.py")
        print("2. Activate venv: .\\venv\\Scripts\\activate")
        print("3. Run backend: python backend/app/main.py")
        print("4. Visit: http://localhost:8000")
        return True
    else:
        print("❌ SCHEMA VALIDATION FAILED")
        print("=" * 60)
        print("\nSome required tables or columns are missing.")
        print("Please check your database schema matches the spec.")
        return False


if __name__ == "__main__":
    validate_schema()
