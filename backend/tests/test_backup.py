import sqlite3

from app.backup import backup_databases, verify_backup


def test_backup_is_consistent_and_digest_verified(tmp_path):
    source = tmp_path / "source.sqlite3"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE evidence(value TEXT)")
        connection.execute("INSERT INTO evidence VALUES ('research-only')")
    destination = tmp_path / "snapshot"
    backup_databases([source], destination)
    assert verify_backup(destination)["files"] == 1
    with sqlite3.connect(destination / source.name) as connection:
        assert connection.execute("SELECT value FROM evidence").fetchone()[0] == "research-only"
