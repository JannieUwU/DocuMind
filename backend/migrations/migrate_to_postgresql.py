"""
Database Migration Script

Migrate data from SQLite to PostgreSQL

Usage:
    python migrate_to_postgresql.py --source sqlite:///users.db --target postgresql://user:pass@localhost/ragchat
"""

import argparse
import logging
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Migrate data between databases"""

    def __init__(self, source_url: str, target_url: str):
        self.source_url = source_url
        self.target_url = target_url

        logger.info(f"Source: {source_url}")
        logger.info(f"Target: {target_url}")

        # Create engines
        self.source_engine = create_engine(source_url)
        self.target_engine = create_engine(target_url)

        # Create sessions
        SourceSession = sessionmaker(bind=self.source_engine)
        TargetSession = sessionmaker(bind=self.target_engine)

        self.source_session = SourceSession()
        self.target_session = TargetSession()

    def get_tables(self):
        """Get list of tables from source database"""
        inspector = inspect(self.source_engine)
        tables = inspector.get_table_names()
        logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")
        return tables

    def migrate_table(self, table_name: str):
        """Migrate a single table"""
        logger.info(f"Migrating table: {table_name}")

        # Reflect table structure
        metadata = MetaData()
        source_table = Table(table_name, metadata, autoload_with=self.source_engine)
        target_table = Table(table_name, metadata, autoload_with=self.target_engine)

        # Get all rows from source
        source_conn = self.source_engine.connect()
        rows = source_conn.execute(source_table.select()).fetchall()
        logger.info(f"  Found {len(rows)} rows")

        if len(rows) == 0:
            logger.info(f"  No data to migrate")
            source_conn.close()
            return

        # Insert into target (batch insert for performance)
        target_conn = self.target_engine.connect()
        trans = target_conn.begin()

        try:
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]

                # Convert Row objects to dicts
                batch_dicts = [dict(row._mapping) for row in batch]

                # Insert batch
                target_conn.execute(target_table.insert(), batch_dicts)

                logger.info(f"  Inserted batch {i//batch_size + 1} ({len(batch)} rows)")

            trans.commit()
            logger.info(f"✓ Successfully migrated {len(rows)} rows")

        except Exception as e:
            trans.rollback()
            logger.error(f"✗ Failed to migrate table {table_name}: {e}")
            raise

        finally:
            source_conn.close()
            target_conn.close()

    def verify_migration(self, table_name: str) -> bool:
        """Verify data migration for a table"""
        logger.info(f"Verifying table: {table_name}")

        metadata = MetaData()
        source_table = Table(table_name, metadata, autoload_with=self.source_engine)
        target_table = Table(table_name, metadata, autoload_with=self.target_engine)

        # Count rows
        source_conn = self.source_engine.connect()
        target_conn = self.target_engine.connect()

        source_count = source_conn.execute(source_table.select().count()).scalar()
        target_count = target_conn.execute(target_table.select().count()).scalar()

        source_conn.close()
        target_conn.close()

        if source_count == target_count:
            logger.info(f"✓ Verification passed: {source_count} rows match")
            return True
        else:
            logger.error(f"✗ Verification failed: source={source_count}, target={target_count}")
            return False

    def migrate_all(self, verify: bool = True):
        """Migrate all tables"""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("Starting database migration")
        logger.info("=" * 60)

        tables = self.get_tables()

        # Migrate each table
        for table in tables:
            try:
                self.migrate_table(table)

                # Verify if requested
                if verify:
                    if not self.verify_migration(table):
                        logger.warning(f"Migration verification failed for {table}")

            except Exception as e:
                logger.error(f"Failed to migrate table {table}: {e}")
                raise

        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"Migration completed successfully!")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Tables migrated: {len(tables)}")
        logger.info("=" * 60)

    def close(self):
        """Close all connections"""
        self.source_session.close()
        self.target_session.close()
        self.source_engine.dispose()
        self.target_engine.dispose()


def main():
    parser = argparse.ArgumentParser(description='Migrate database from SQLite to PostgreSQL')
    parser.add_argument(
        '--source',
        required=True,
        help='Source database URL (e.g., sqlite:///users.db)'
    )
    parser.add_argument(
        '--target',
        required=True,
        help='Target database URL (e.g., postgresql://user:pass@localhost/ragchat)'
    )
    parser.add_argument(
        '--no-verify',
        action='store_true',
        help='Skip verification step'
    )

    args = parser.parse_args()

    # Confirm migration
    print("\n" + "=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    print(f"Source: {args.source}")
    print(f"Target: {args.target}")
    print("=" * 60)
    print("\n⚠️  WARNING: This will copy all data from source to target.")
    print("Make sure the target database is empty or you want to overwrite data.")
    print("\n")

    confirm = input("Do you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)

    # Run migration
    migrator = None
    try:
        migrator = DatabaseMigrator(args.source, args.target)
        migrator.migrate_all(verify=not args.no_verify)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

    finally:
        if migrator:
            migrator.close()


if __name__ == '__main__':
    main()
