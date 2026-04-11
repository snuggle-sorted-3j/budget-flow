"""
Data Persistence Tests

Verifies that:
1. Committed data survives database reconnection (simulating container restart)
2. Backup scripts create valid, restorable SQL dumps
3. Retention policy works correctly

These tests use REAL commits (no transaction rollback) so they require explicit
cleanup in teardown. They are separated into two pytest markers:

  pytest -m persistence   # Reconnection/survival tests only
  pytest -m backup        # Backup/restore workflow tests only

Run both:
  pytest tests/integration/test_data_persistence.py -v
"""
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Generator, List, Tuple

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import get_password_hash
from app.models.currency import Currency
from app.models.user import User

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PERSISTENCE_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/budget_flow_test",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def fresh_connection(url: str) -> Tuple[Session, object]:
    """
    Create a brand-new SQLAlchemy engine with no shared connection pool state.
    Simulates a reconnection after container restart.
    Returns (session, engine) — caller must close both.
    """
    engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal(), engine


def _cleanup(session: Session, created: List[Tuple[str, uuid.UUID]]) -> None:
    """
    Delete test rows in FK-safe reverse order.
    created is a list of (table_name, id) tuples in creation order.
    """
    # Reverse insertion order so we respect FK constraints
    for table, row_id in reversed(created):
        try:
            session.execute(
                text(f"DELETE FROM {table} WHERE id = :id"),
                {"id": str(row_id)},
            )
        except Exception:
            pass  # Already gone or FK-cascaded away
    try:
        session.commit()
    except Exception:
        session.rollback()


def _get_script_path(script_name: str) -> str:
    """
    Resolve absolute path to scripts/<script_name>.
    File layout: tests/integration/ -> tests/ -> backend/ -> repo_root/ -> scripts/
    Skips the test if the script is not found.
    """
    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent.parent  # 4 levels up
    script = repo_root / "scripts" / script_name
    if not script.exists():
        pytest.skip(f"Script not found at {script} — skipping backup test")
    return str(script)


def _pg_dump_available() -> bool:
    """
    Return True if backup-db.sh can run successfully.
    Checks: pg_dump in PATH, OR docker available with budget-flow-postgres running.
    """
    if shutil.which("pg_dump"):
        return True
    if shutil.which("docker"):
        result = subprocess.run(
            ["docker", "exec", "budget-flow-postgres", "pg_dump", "--version"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True
    return False


def _backup_env(db_name: str, backup_dir: str) -> dict:
    """Build environment dict for backup-db.sh invocations."""
    env = {**os.environ}
    env["BUDGET_DB_NAME"] = db_name
    env["BUDGET_BACKUP_DIR"] = backup_dir
    # When running inside the backend container, postgres is the Docker service hostname
    env.setdefault("BUDGET_DB_HOST", "postgres")
    env.setdefault("BUDGET_DB_USER", "postgres")
    return env


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def committed_session() -> Generator[Tuple[Session, List], None, None]:
    """
    Provides a (session, created_ids) pair where session commits for real.
    Unlike the standard `db` fixture, no transaction rollback is used here.
    All rows added to created_ids are cleaned up in teardown.
    """
    engine = create_engine(PERSISTENCE_DB_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    created: List[Tuple[str, uuid.UUID]] = []

    yield session, created

    session.close()
    cleanup_session = SessionLocal()
    _cleanup(cleanup_session, created)
    cleanup_session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# TestDataSurvivesReconnection
# ---------------------------------------------------------------------------


@pytest.mark.persistence
class TestDataSurvivesReconnection:
    """
    Verify that committed data is visible from a completely fresh connection.
    engine.dispose() is called between write and read to flush all pooled
    connections — simulating what happens after a container restart.
    """

    def test_user_survives_new_connection(
        self, committed_session: Tuple[Session, List]
    ) -> None:
        """Committed user row is readable from a brand-new engine."""
        session, created = committed_session
        uid = uuid.uuid4()
        email = f"persist-user-{uid.hex[:8]}@test.com"

        user = User(
            id=uid,
            email=email,
            password_hash=get_password_hash("TestPass123!"),
            full_name="Persistence Test",
            is_active=True,
        )
        session.add(user)
        session.commit()
        created.append(("users", uid))

        # Dispose all pooled connections (simulates reconnect)
        session.get_bind().dispose()

        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            fetched = new_session.get(User, uid)
            assert fetched is not None, "User not found after reconnect"
            assert fetched.email == email
            assert fetched.full_name == "Persistence Test"
            assert fetched.is_active is True
        finally:
            new_session.close()
            new_engine.dispose()

    def test_relational_chain_persists(
        self, committed_session: Tuple[Session, List]
    ) -> None:
        """User → Currency relationship survives reconnection."""
        session, created = committed_session

        uid = uuid.uuid4()
        cid = uuid.uuid4()
        unique_ticker = f"P{uid.hex[:4].upper()}"

        user = User(
            id=uid,
            email=f"chain-{uid.hex[:8]}@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Chain Test",
            is_active=True,
        )
        session.add(user)
        session.flush()  # Populate PK before FK reference

        currency = Currency(
            id=cid,
            user_id=uid,
            ticker=unique_ticker,
            name="Persistence Dollar",
            is_default=True,
        )
        session.add(currency)
        session.commit()

        created.append(("currencies", cid))
        created.append(("users", uid))

        # Dispose and reconnect
        session.get_bind().dispose()

        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            fetched_currency = new_session.get(Currency, cid)
            assert fetched_currency is not None, "Currency not found after reconnect"
            assert fetched_currency.ticker == unique_ticker
            assert fetched_currency.user_id == uid

            fetched_user = new_session.get(User, uid)
            assert fetched_user is not None, "User not found after reconnect"
        finally:
            new_session.close()
            new_engine.dispose()

    def test_multi_tenant_isolation_persists(
        self, committed_session: Tuple[Session, List]
    ) -> None:
        """User A's currency is NOT returned when filtering by User B's ID."""
        session, created = committed_session

        uid_a = uuid.uuid4()
        uid_b = uuid.uuid4()
        cid_a = uuid.uuid4()

        user_a = User(
            id=uid_a,
            email=f"tenant-a-{uid_a.hex[:8]}@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Tenant A",
            is_active=True,
        )
        user_b = User(
            id=uid_b,
            email=f"tenant-b-{uid_b.hex[:8]}@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Tenant B",
            is_active=True,
        )
        session.add_all([user_a, user_b])
        session.flush()

        currency_a = Currency(
            id=cid_a,
            user_id=uid_a,
            ticker=f"A{uid_a.hex[:3].upper()}",
            name="Tenant A Dollar",
            is_default=True,
        )
        session.add(currency_a)
        session.commit()

        created.extend([("currencies", cid_a), ("users", uid_a), ("users", uid_b)])

        session.get_bind().dispose()

        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            # Querying User B's currencies should return nothing
            result = new_session.execute(
                select(Currency).where(Currency.user_id == uid_b)
            ).scalars().all()
            assert len(result) == 0, "User B should have no currencies"

            # Querying User A's currencies should return the one we created
            result_a = new_session.execute(
                select(Currency).where(Currency.user_id == uid_a)
            ).scalars().all()
            assert len(result_a) == 1
            assert result_a[0].id == cid_a
        finally:
            new_session.close()
            new_engine.dispose()

    def test_update_persists_across_reconnect(
        self, committed_session: Tuple[Session, List]
    ) -> None:
        """UPDATE is visible from a fresh connection after pool dispose."""
        session, created = committed_session

        uid = uuid.uuid4()
        user = User(
            id=uid,
            email=f"update-{uid.hex[:8]}@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Original Name",
            is_active=True,
        )
        session.add(user)
        session.commit()
        created.append(("users", uid))

        # Update
        user.full_name = "Updated Name"
        session.commit()

        session.get_bind().dispose()

        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            fetched = new_session.get(User, uid)
            assert fetched is not None
            assert fetched.full_name == "Updated Name"
        finally:
            new_session.close()
            new_engine.dispose()

    def test_delete_persists_across_reconnect(
        self, committed_session: Tuple[Session, List]
    ) -> None:
        """DELETE is visible (row absent) from a fresh connection."""
        session, created = committed_session

        uid = uuid.uuid4()
        user = User(
            id=uid,
            email=f"delete-{uid.hex[:8]}@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="To Be Deleted",
            is_active=True,
        )
        session.add(user)
        session.commit()
        # Do NOT add to created — we delete it ourselves below

        session.delete(user)
        session.commit()

        session.get_bind().dispose()

        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            fetched = new_session.get(User, uid)
            assert fetched is None, "Deleted user should not exist after reconnect"
        finally:
            new_session.close()
            new_engine.dispose()

    def test_cascade_delete_persists(
        self, committed_session: Tuple[Session, List]
    ) -> None:
        """Deleting a user cascades to their currencies (ON DELETE CASCADE)."""
        session, created = committed_session

        uid = uuid.uuid4()
        cid = uuid.uuid4()

        user = User(
            id=uid,
            email=f"cascade-{uid.hex[:8]}@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Cascade User",
            is_active=True,
        )
        session.add(user)
        session.flush()

        currency = Currency(
            id=cid,
            user_id=uid,
            ticker=f"C{uid.hex[:3].upper()}",
            name="Cascade Currency",
            is_default=True,
        )
        session.add(currency)
        session.commit()
        # No entries in created — we handle deletion below

        # Delete user (should cascade to currency)
        session.delete(user)
        session.commit()

        session.get_bind().dispose()

        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            assert new_session.get(User, uid) is None, "User should be deleted"
            assert new_session.get(Currency, cid) is None, "Currency should be cascade-deleted"
        finally:
            new_session.close()
            new_engine.dispose()


# ---------------------------------------------------------------------------
# TestBackupWorkflow
# ---------------------------------------------------------------------------


@pytest.mark.backup
class TestBackupWorkflow:
    """
    Shell-level backup/restore workflow tests.

    These tests invoke scripts/backup-db.sh and scripts/restore-db.sh via
    subprocess. They require pg_dump to be available either directly in PATH
    or via docker exec (budget-flow-postgres container).

    If neither is available, all tests in this class are skipped.
    """

    @pytest.fixture(autouse=True)
    def require_pg_dump(self) -> None:
        """Skip entire class if pg_dump is not accessible."""
        if not _pg_dump_available():
            pytest.skip("pg_dump not available — skipping backup tests")

    def test_backup_creates_nonempty_file(self, tmp_path: Path) -> None:
        """Running backup-db.sh produces a non-empty .sql file."""
        backup_dir = str(tmp_path / "backups")
        os.makedirs(backup_dir)

        script = _get_script_path("backup-db.sh")
        result = subprocess.run(
            ["bash", script, "--db-name", "budget_flow_test", "--output-dir", backup_dir],
            capture_output=True,
            text=True,
            env=_backup_env("budget_flow_test", backup_dir),
            timeout=60,
        )

        assert result.returncode == 0, (
            f"backup-db.sh exited {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        sql_files = list(Path(backup_dir).glob("budget_flow_[0-9]*.sql"))
        assert len(sql_files) == 1, f"Expected 1 backup file, found {len(sql_files)}"
        assert sql_files[0].stat().st_size > 100, "Backup file is suspiciously small"

    def test_backup_contains_valid_sql(self, tmp_path: Path) -> None:
        """Backup file contains PostgreSQL dump header."""
        backup_dir = str(tmp_path / "backups")
        os.makedirs(backup_dir)

        script = _get_script_path("backup-db.sh")
        subprocess.run(
            ["bash", script, "--db-name", "budget_flow_test", "--output-dir", backup_dir],
            check=True,
            capture_output=True,
            text=True,
            env=_backup_env("budget_flow_test", backup_dir),
            timeout=60,
        )

        sql_file = next(Path(backup_dir).glob("budget_flow_[0-9]*.sql"))
        header = sql_file.read_text(errors="replace")[:500]

        assert "PostgreSQL" in header, (
            f"Backup file does not look like a valid pg_dump output.\nFirst 500 chars:\n{header}"
        )

    def test_retention_keeps_7_files(self, tmp_path: Path) -> None:
        """After 9 backup runs only 7 scheduled backups remain."""
        backup_dir = str(tmp_path / "backups")
        os.makedirs(backup_dir)

        script = _get_script_path("backup-db.sh")
        env = _backup_env("budget_flow_test", backup_dir)

        for i in range(9):
            result = subprocess.run(
                ["bash", script, "--db-name", "budget_flow_test", "--output-dir", backup_dir],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            assert result.returncode == 0, (
                f"Run {i + 1}/9 failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
            # Ensure distinct timestamps (format: YYYYMMDD_HHMMSS)
            time.sleep(1)

        remaining = list(Path(backup_dir).glob("budget_flow_[0-9]*.sql"))
        assert len(remaining) == 7, (
            f"Expected 7 backups after retention, found {len(remaining)}:\n"
            + "\n".join(f.name for f in sorted(remaining))
        )

    def test_prestop_backups_not_affected_by_retention(self, tmp_path: Path) -> None:
        """Retention policy on budget_flow_[0-9]* does NOT delete prestop backups."""
        backup_dir = str(tmp_path / "backups")
        os.makedirs(backup_dir)

        # Manually create 8 fake pre-stop backup files
        for i in range(8):
            (Path(backup_dir) / f"budget_flow_prestop_202601{i:02d}_000000.sql").write_text(
                "-- fake prestop backup\n"
            )

        script = _get_script_path("backup-db.sh")
        env = _backup_env("budget_flow_test", backup_dir)

        # Run 2 real backups (should trigger retention on scheduled files only)
        for _ in range(2):
            subprocess.run(
                ["bash", script, "--db-name", "budget_flow_test", "--output-dir", backup_dir],
                check=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            time.sleep(1)

        prestop_files = list(Path(backup_dir).glob("budget_flow_prestop_*.sql"))
        assert len(prestop_files) == 8, (
            "Retention policy should NOT delete pre-stop backup files"
        )

    def test_restore_round_trip(
        self, tmp_path: Path, committed_session: Tuple[Session, List]
    ) -> None:
        """
        Full round-trip: commit known data → backup → restore → verify data present.
        Uses budget_flow_test database to avoid touching production data.
        """
        session, created = committed_session

        # Write a known user to the test database
        uid = uuid.uuid4()
        test_email = f"backup-rt-{uid.hex[:8]}@test.com"
        user = User(
            id=uid,
            email=test_email,
            password_hash=get_password_hash("RoundTrip123!"),
            full_name="Round Trip User",
            is_active=True,
        )
        session.add(user)
        session.commit()
        created.append(("users", uid))

        backup_dir = str(tmp_path / "backups")
        os.makedirs(backup_dir)

        # --- Backup ---
        backup_script = _get_script_path("backup-db.sh")
        env = _backup_env("budget_flow_test", backup_dir)

        subprocess.run(
            ["bash", backup_script, "--db-name", "budget_flow_test", "--output-dir", backup_dir],
            check=True,
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )

        backup_file = next(Path(backup_dir).glob("budget_flow_[0-9]*.sql"))
        assert backup_file.exists()

        # --- Restore (echo y to confirm prompt) ---
        restore_script = _get_script_path("restore-db.sh")
        restore_env = {**env, "BUDGET_DB_NAME": "budget_flow_test"}

        result = subprocess.run(
            ["bash", restore_script, str(backup_file)],
            input="y\n",
            capture_output=True,
            text=True,
            env=restore_env,
            timeout=120,
        )

        assert result.returncode == 0, (
            f"restore-db.sh failed (exit {result.returncode})\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert "SUCCESS" in result.stdout, (
            f"restore-db.sh did not report SUCCESS:\n{result.stdout}"
        )

        # --- Verify data present after restore ---
        new_session, new_engine = fresh_connection(PERSISTENCE_DB_URL)
        try:
            fetched = new_session.execute(
                select(User).where(User.email == test_email)
            ).scalar_one_or_none()
            assert fetched is not None, (
                f"User '{test_email}' not found in database after restore"
            )
            assert fetched.full_name == "Round Trip User"
        finally:
            new_session.close()
            new_engine.dispose()
