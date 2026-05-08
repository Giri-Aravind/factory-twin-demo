"""One-time setup: create chat database, tables, verify connections."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__) + '/..')

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


def setup():
    print("\n" + "=" * 50)
    print("Setting up databases")
    print("=" * 50)

    # 1. Create chat database if it doesn't exist
    print("\n[1] Creating chat database...")
    try:
        # Connect to default postgres database to create our database
        admin_url = f"postgresql://{os.getenv("CHAT_DB_USER", "postgres")}:{os.getenv("CHAT_DB_PASSWORD", "")}@{os.getenv("CHAT_DB_HOST", "localhost")}:{os.getenv("CHAT_DB_PORT", "5432")}/postgres"
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{os.getenv("CHAT_DB_NAME", "factorytwin_chat")}'"))
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {os.getenv("CHAT_DB_NAME", "factorytwin_chat")}"))
                print(f"  ✓ Created database '{os.getenv("CHAT_DB_NAME", "factorytwin_chat")}'")
            else:
                print(f"  ✓ Database '{os.getenv("CHAT_DB_NAME", "factorytwin_chat")}' already exists")
        engine.dispose()
    except Exception as e:
        print(f"  ✗ Could not create database: {e}")
        print(f"  → Create it manually: CREATE DATABASE {os.getenv("CHAT_DB_NAME", "factorytwin_chat")};")

    # 2. Create tables
    print("\n[2] Creating tables...")
    try:
        from scripts.chatdb import chatdb
        chatdb.create_tables()
        print("  ✓ Tables created (conversations, messages)")
    except Exception as e:
        print(f"  ✗ Table creation failed: {e}")

    # 3. Verify FactoryTwin database connection
    print("\n[3] Verifying FactoryTwin database...")
    try:
        from scripts.postgres import postgres
        ok, result = postgres.verify_connection()
        if ok:
            print(f"  ✓ Connected to FactoryTwin DB ({result} sites found)")
        else:
            print(f"  ⚠ Cannot connect to FactoryTwin DB: {result}")
            print(f"  → This is OK if you haven't set up the FactoryTwin database yet")
    except Exception as e:
        print(f"  ⚠ FactoryTwin DB check skipped: {e}")

    print("\n" + "=" * 50)
    print("✓ Setup complete")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    setup()
