import json
import sqlite3
from datetime import datetime, timezone

from app.config import APP_DB_FILE


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserRepository:
    def __init__(self, path=APP_DB_FILE):
        self.path = path
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL DEFAULT '',
                full_name TEXT NOT NULL DEFAULT '',
                joined_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                message_count INTEGER NOT NULL DEFAULT 0,
                requested_movie_codes TEXT NOT NULL DEFAULT '[]',
                saved_movie_codes TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        self._ensure_columns(
            {
                "saved_movie_codes": "TEXT NOT NULL DEFAULT '[]'",
            }
        )
        self.connection.commit()

    def _ensure_columns(self, columns: dict[str, str]) -> None:
        existing = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(users)").fetchall()
        }
        for name, sql_type in columns.items():
            if name not in existing:
                self.connection.execute(f"ALTER TABLE users ADD COLUMN {name} {sql_type}")

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        result = dict(row)
        result["requested_movie_codes"] = json.loads(result.get("requested_movie_codes") or "[]")
        result["saved_movie_codes"] = json.loads(result.get("saved_movie_codes") or "[]")
        return result

    def all(self) -> list[dict]:
        rows = self.connection.execute("SELECT * FROM users ORDER BY user_id DESC").fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get(self, user_id: int | str) -> dict | None:
        row = self.connection.execute("SELECT * FROM users WHERE user_id = ?", (int(user_id),)).fetchone()
        return self._row_to_dict(row) if row else None

    def upsert(self, user_data: dict) -> dict:
        existing = self.get(user_data["user_id"])
        now = utc_now_iso()
        if existing:
            self.connection.execute(
                """
                UPDATE users
                SET username = ?, full_name = ?, last_seen_at = ?
                WHERE user_id = ?
                """,
                (
                    user_data.get("username", existing.get("username", "")),
                    user_data.get("full_name", existing.get("full_name", "")),
                    now,
                    int(user_data["user_id"]),
                ),
            )
            self.connection.commit()
            return self.get(user_data["user_id"])

        self.connection.execute(
            """
            INSERT INTO users (user_id, username, full_name, joined_at, last_seen_at, message_count, requested_movie_codes)
            VALUES (?, ?, ?, ?, ?, 0, '[]')
            """,
            (
                int(user_data["user_id"]),
                user_data.get("username", ""),
                user_data.get("full_name", ""),
                now,
                now,
            ),
        )
        self.connection.commit()
        return self.get(user_data["user_id"])

    def increment_message_count(self, user_id: int | str) -> dict | None:
        user = self.get(user_id)
        if not user:
            return None
        self.connection.execute(
            """
            UPDATE users
            SET message_count = message_count + 1, last_seen_at = ?
            WHERE user_id = ?
            """,
            (utc_now_iso(), int(user_id)),
        )
        self.connection.commit()
        return self.get(user_id)

    def toggle_saved_movie(self, user_id: int | str, code: str) -> tuple[dict | None, bool]:
        user = self.get(user_id)
        if not user:
            return None, False
        saved_codes = list(user.get("saved_movie_codes", []))
        is_saved = str(code) not in saved_codes
        if is_saved:
            saved_codes.insert(0, str(code))
        else:
            saved_codes = [item for item in saved_codes if str(item) != str(code)]
        self.connection.execute(
            """
            UPDATE users
            SET saved_movie_codes = ?, last_seen_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(saved_codes[:200], ensure_ascii=False), utc_now_iso(), int(user_id)),
        )
        self.connection.commit()
        return self.get(user_id), is_saved

    def add_requested_movie(self, user_id: int | str, code: str) -> dict | None:
        user = self.get(user_id)
        if not user:
            return None
        codes = list(user.get("requested_movie_codes", []))
        if code in codes:
            codes.remove(code)
        codes.insert(0, code)
        self.connection.execute(
            """
            UPDATE users
            SET requested_movie_codes = ?, last_seen_at = ?
            WHERE user_id = ?
            """,
            (json.dumps(codes[:20], ensure_ascii=False), utc_now_iso(), int(user_id)),
        )
        self.connection.commit()
        return self.get(user_id)
