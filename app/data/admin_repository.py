import sqlite3

from app.config import APP_DB_FILE


class AdminRepository:
    def __init__(self, path=APP_DB_FILE):
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER
            )
            """
        )
        self.connection.commit()

    def all_ids(self) -> set[int]:
        rows = self.connection.execute("SELECT user_id FROM admins").fetchall()
        return {int(row["user_id"]) for row in rows}

    def add(self, user_id: int, added_by: int | None = None) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO admins (user_id, added_by) VALUES (?, ?)",
            (int(user_id), int(added_by) if added_by else None),
        )
        self.connection.commit()

    def remove(self, user_id: int) -> bool:
        cursor = self.connection.execute("DELETE FROM admins WHERE user_id = ?", (int(user_id),))
        self.connection.commit()
        return cursor.rowcount > 0
