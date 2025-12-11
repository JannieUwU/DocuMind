"""
Database Cleanup Tool - Remove Orphaned Documents

This script removes documents with NULL conversation_id from the vector database.
These orphaned documents cause cross-conversation pollution.

Usage:
    python cleanup_orphan_documents.py --username <username>
    python cleanup_orphan_documents.py --all  # Clean all users
"""
import sqlite3
import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cleanup_orphan_documents(db_path: str, dry_run: bool = True):
    """
    Remove chunks with NULL conversation_id from vector database.

    Args:
        db_path: Path to the RAG database (e.g., custom_rag_username.db)
        dry_run: If True, only show what would be deleted without actually deleting
    """
    if not os.path.exists(db_path):
        logger.warning(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Count orphaned chunks
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE conversation_id IS NULL")
        orphan_count = cursor.fetchone()[0]

        # Count orphaned documents
        cursor.execute("SELECT COUNT(DISTINCT document_id) FROM chunks WHERE conversation_id IS NULL")
        orphan_docs = cursor.fetchone()[0]

        # Get document details
        cursor.execute("""
            SELECT DISTINCT d.filename, COUNT(c.id) as chunk_count
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.conversation_id IS NULL
            GROUP BY d.id, d.filename
        """)
        orphan_details = cursor.fetchall()

        if orphan_count == 0:
            logger.info(f"No orphaned documents found in {db_path}")
            return

        logger.warning(f"Found {orphan_count} orphaned chunks from {orphan_docs} documents:")
        for filename, chunk_count in orphan_details:
            logger.warning(f"   - {filename}: {chunk_count} chunks")

        if dry_run:
            logger.info("DRY RUN - No changes made. Run with --execute to delete orphaned data.")
        else:
            # Delete orphaned chunks
            cursor.execute("DELETE FROM chunks WHERE conversation_id IS NULL")
            deleted_chunks = cursor.rowcount

            # Delete orphaned documents (documents with no chunks left)
            cursor.execute("""
                DELETE FROM documents
                WHERE id NOT IN (SELECT DISTINCT document_id FROM chunks)
            """)
            deleted_docs = cursor.rowcount

            conn.commit()
            logger.info(f"CLEANUP COMPLETE:")
            logger.info(f"   - Deleted {deleted_chunks} orphaned chunks")
            logger.info(f"   - Deleted {deleted_docs} orphaned documents")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Clean up orphaned documents from RAG databases")
    parser.add_argument("--username", type=str, help="Username to clean (e.g., 'testuser')")
    parser.add_argument("--all", action="store_true", help="Clean all user databases")
    parser.add_argument("--execute", action="store_true", help="Actually perform cleanup (default is dry-run)")
    args = parser.parse_args()

    dry_run = not args.execute

    if dry_run:
        logger.info("RUNNING IN DRY-RUN MODE - No changes will be made")
        logger.info("   Use --execute to actually delete orphaned data")
        logger.info("")

    backend_dir = os.path.dirname(os.path.abspath(__file__))

    if args.all:
        # Clean all custom_rag_*.db files
        logger.info("Scanning for all RAG databases...")
        db_files = [f for f in os.listdir(backend_dir) if f.startswith("custom_rag_") and f.endswith(".db")]

        if not db_files:
            logger.info("No RAG databases found.")
            return

        logger.info(f"Found {len(db_files)} RAG databases")
        for db_file in db_files:
            db_path = os.path.join(backend_dir, db_file)
            username = db_file.replace("custom_rag_", "").replace(".db", "")
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing user: {username}")
            logger.info(f"Database: {db_file}")
            logger.info(f"{'='*60}")
            cleanup_orphan_documents(db_path, dry_run=dry_run)

    elif args.username:
        db_file = f"custom_rag_{args.username}.db"
        db_path = os.path.join(backend_dir, db_file)
        logger.info(f"Processing user: {args.username}")
        logger.info(f"Database: {db_file}")
        cleanup_orphan_documents(db_path, dry_run=dry_run)

    else:
        parser.print_help()
        logger.error("\nError: Please specify --username <name> or --all")
        sys.exit(1)

    if dry_run:
        logger.info("\n" + "="*60)
        logger.info("DRY RUN COMPLETE - No changes were made")
        logger.info("   To actually delete orphaned data, run with --execute")
        logger.info("="*60)


if __name__ == "__main__":
    main()
