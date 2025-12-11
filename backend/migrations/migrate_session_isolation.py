"""
Database migration script to add conversation_id support for session isolation

This script:
1. Adds conversation_id column to user_documents table
2. Adds conversation_id column to chunks table in vector databases
3. Preserves existing data
"""
import sqlite3
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_users_db():
    """Migrate users.db to add conversation_id to user_documents"""
    db_path = "users.db"

    if not os.path.exists(db_path):
        logger.warning(f"{db_path} not found, skipping migration")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if conversation_id column already exists
        cursor.execute("PRAGMA table_info(user_documents)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'conversation_id' in columns:
            logger.info("users.db already migrated (conversation_id column exists)")
            return

        # Add conversation_id column
        logger.info("Adding conversation_id column to user_documents table...")
        cursor.execute("""
            ALTER TABLE user_documents
            ADD COLUMN conversation_id INTEGER
            REFERENCES conversations(id) ON DELETE CASCADE
        """)

        conn.commit()
        logger.info("✓ users.db migration completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed for users.db: {e}")
        raise
    finally:
        conn.close()


def migrate_vector_db(db_path):
    """Migrate a vector database to add conversation_id to chunks table"""
    if not os.path.exists(db_path):
        logger.warning(f"{db_path} not found, skipping")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if chunks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
        if not cursor.fetchone():
            logger.info(f"{db_path}: chunks table not found, skipping")
            return

        # Check if conversation_id column already exists
        cursor.execute("PRAGMA table_info(chunks)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'conversation_id' in columns:
            logger.info(f"{db_path}: already migrated (conversation_id column exists)")
            return

        # Add conversation_id column
        logger.info(f"Adding conversation_id column to chunks table in {db_path}...")
        cursor.execute("""
            ALTER TABLE chunks
            ADD COLUMN conversation_id INTEGER
        """)

        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_conversation_id
            ON chunks(conversation_id)
        """)

        conn.commit()
        logger.info(f"✓ {db_path} migration completed successfully")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed for {db_path}: {e}")
        raise
    finally:
        conn.close()


def migrate_all_vector_dbs():
    """Find and migrate all vector databases (custom_rag_*.db)"""
    backend_dir = Path(__file__).parent

    # Find all vector database files
    vector_dbs = list(backend_dir.glob("custom_rag_*.db"))

    if not vector_dbs:
        logger.info("No vector databases found to migrate")
        return

    logger.info(f"Found {len(vector_dbs)} vector database(s) to migrate")

    for db_path in vector_dbs:
        migrate_vector_db(str(db_path))


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("Starting Session Isolation Migration")
    logger.info("="*60)

    # Migrate main users database
    logger.info("\n[1/2] Migrating users.db...")
    migrate_users_db()

    # Migrate all vector databases
    logger.info("\n[2/2] Migrating vector databases...")
    migrate_all_vector_dbs()

    logger.info("\n" + "="*60)
    logger.info("Migration completed successfully!")
    logger.info("="*60)
    logger.info("\nNext steps:")
    logger.info("1. Restart your backend server")
    logger.info("2. Test the new conversation feature:")
    logger.info("   - Create a new conversation")
    logger.info("   - Upload a document")
    logger.info("   - Start another new conversation")
    logger.info("   - The previous document should NOT appear in searches")
