"""
Database migration script: Add conversation_id column to RAG database

WARNING: This will DELETE all existing chunks data!
Make sure to backup important files before running this script.

Usage:
cd backend
venv/Scripts/python.exe migrate_rag_db.py Jade
"""
import sqlite3
import sys
from pathlib import Path
import shutil
from datetime import datetime

def migrate_rag_database(username):
    db_path = f"custom_rag_{username}.db"

    if not Path(db_path).exists():
        print(f"[INFO] RAG database not found: {db_path}")
        print("Nothing to migrate.")
        return

    print("\n" + "="*60)
    print("RAG DATABASE MIGRATION")
    print("="*60)
    print(f"\nDatabase: {db_path}")

    # Check current schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(chunks)")
    columns = [col[1] for col in cursor.fetchall()]

    print(f"\nCurrent chunks table columns: {', '.join(columns)}")

    if 'conversation_id' in columns:
        print("\n[OK] conversation_id column already exists!")
        print("No migration needed.")
        conn.close()
        return

    print("\n[WARNING] conversation_id column is MISSING!")
    print("\nThis script will:")
    print("  1. Backup the current database")
    print("  2. Delete all chunks data")
    print("  3. Recreate tables with conversation_id column")
    print("\n[IMPORTANT] All uploaded file data will be lost!")
    print("You will need to re-upload your documents.\n")

    response = input("Do you want to proceed? (yes/no): ").strip().lower()

    if response != 'yes':
        print("\nMigration cancelled.")
        conn.close()
        return

    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"custom_rag_{username}_backup_{timestamp}.db"

    print(f"\n[1/3] Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"[OK] Backup created")

    # Drop and recreate
    print("\n[2/3] Dropping old tables...")
    cursor.execute("DROP TABLE IF EXISTS chunks")
    cursor.execute("DROP TABLE IF EXISTS documents")
    conn.commit()
    print("[OK] Old tables dropped")

    print("\n[3/3] Creating new tables with conversation_id...")

    # Documents table
    cursor.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_hash TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chunks table with conversation_id
    cursor.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            conversation_id INTEGER,
            chunk_text TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
        )
    """)

    # Indexes
    cursor.execute("""
        CREATE INDEX idx_document_id ON chunks(document_id)
    """)

    cursor.execute("""
        CREATE INDEX idx_chunks_conversation_id ON chunks(conversation_id)
    """)

    cursor.execute("""
        CREATE INDEX idx_chunks_doc_conv ON chunks(document_id, conversation_id)
    """)

    conn.commit()
    print("[OK] New tables created with indexes")

    # Verify
    cursor.execute("PRAGMA table_info(chunks)")
    new_columns = [col[1] for col in cursor.fetchall()]
    print(f"\nNew chunks table columns: {', '.join(new_columns)}")

    conn.close()

    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print(f"\n[OK] RAG database migrated successfully!")
    print(f"[OK] Backup saved to: {backup_path}")
    print("\n[NEXT STEPS]:")
    print("  1. Re-upload your documents through the web interface")
    print("  2. Make sure to upload files AFTER starting a conversation")
    print("  3. Each conversation will have isolated document context\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_rag_db.py <username>")
        print("Example: python migrate_rag_db.py Jade")
        sys.exit(1)

    username = sys.argv[1]
    migrate_rag_database(username)
