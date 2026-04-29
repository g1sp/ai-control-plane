"""Database migration runner service."""

from alembic.config import Config
from alembic.command import upgrade, downgrade, current as alembic_current, history
from alembic.script import ScriptDirectory
from pathlib import Path
import os
from sqlalchemy import text
from src.database import SessionLocal, engine


class MigrationRunner:
    """Run and manage database migrations."""

    def __init__(self):
        migrations_dir = Path(__file__).parent.parent.parent / "migrations"
        self.config = Config(str(migrations_dir.parent / "alembic.ini"))
        self.config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", "sqlite:///./data/audit.db"))
        self.config.set_main_option("script_location", str(migrations_dir))

    def get_current_revision(self) -> str:
        """Get current database revision."""
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            row = result.fetchone()
            return row[0] if row else None
        except Exception:
            return None
        finally:
            db.close()

    def get_migration_history(self):
        """Get list of all available migrations."""
        script = ScriptDirectory.from_config(self.config)
        migrations = []
        for rev in script.walk_revisions(head="head", base="base"):
            migrations.append({
                "revision": rev.revision,
                "message": rev.doc if rev.doc else "No description",
                "down_revision": rev.down_revision,
            })
        return migrations

    def upgrade_to_head(self) -> bool:
        """Run all pending migrations."""
        try:
            upgrade(self.config, "head")
            return True
        except Exception as e:
            print(f"Migration upgrade failed: {e}")
            return False

    def downgrade_one(self) -> bool:
        """Rollback to previous migration."""
        try:
            downgrade(self.config, "-1")
            return True
        except Exception as e:
            print(f"Migration downgrade failed: {e}")
            return False

    def get_pending_migrations(self) -> list:
        """Get list of pending migrations to apply."""
        current = self.get_current_revision()
        history_list = self.get_migration_history()
        pending = []
        found_current = current is None
        for migration in history_list:
            if found_current:
                pending.append(migration)
            if migration["revision"] == current:
                found_current = True
        return pending


def init_migrations():
    """Initialize database with migrations on startup."""
    runner = MigrationRunner()
    current = runner.get_current_revision()
    if current is None:
        print("No migrations applied. Running initial migration...")
        if runner.upgrade_to_head():
            print(f"Migrations applied successfully. Current version: {runner.get_current_revision()}")
        else:
            print("Failed to apply migrations")
    else:
        print(f"Database is at migration: {current}")
        pending = runner.get_pending_migrations()
        if pending:
            print(f"Found {len(pending)} pending migrations. Applying...")
            if runner.upgrade_to_head():
                print(f"Migrations applied successfully. Current version: {runner.get_current_revision()}")
            else:
                print("Failed to apply pending migrations")
