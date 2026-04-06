import sqlite3

from app.config import APP_DB_FILE


class SubscriptionRepository:
    def __init__(self, path=APP_DB_FILE):
        self.path = path
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscription_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS subscription_channels (
                chat_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL
            )
            """
        )
        self.connection.execute("INSERT OR IGNORE INTO subscription_state (id, enabled) VALUES (1, 0)")
        self.connection.commit()

    def get_state(self) -> dict:
        state_row = self.connection.execute("SELECT enabled FROM subscription_state WHERE id = 1").fetchone()
        channel_rows = self.connection.execute(
            "SELECT chat_id, title, url FROM subscription_channels ORDER BY rowid DESC"
        ).fetchall()
        return {
            "enabled": bool(state_row["enabled"]) if state_row else False,
            "channels": [dict(row) for row in channel_rows],
        }

    def set_enabled(self, enabled: bool) -> None:
        self.connection.execute("UPDATE subscription_state SET enabled = ? WHERE id = 1", (1 if enabled else 0,))
        self.connection.commit()

    def add_channel(self, channel: dict) -> None:
        self.connection.execute(
            """
            INSERT INTO subscription_channels (chat_id, title, url)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title, url = excluded.url
            """,
            (str(channel["chat_id"]), channel.get("title", ""), channel.get("url", "")),
        )
        self.connection.commit()

    def remove_channel(self, chat_id: str | int) -> bool:
        cursor = self.connection.execute("DELETE FROM subscription_channels WHERE chat_id = ?", (str(chat_id),))
        self.connection.commit()
        return cursor.rowcount > 0
