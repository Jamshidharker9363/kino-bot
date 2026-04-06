import json
import sqlite3
from pathlib import Path

from app.config import APP_DB_FILE, MOVIES_FILE


class MovieRepository:
    def __init__(self, db_path=APP_DB_FILE, legacy_json_path=MOVIES_FILE):
        self.db_path = Path(db_path)
        self.legacy_json_path = Path(legacy_json_path)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self._ensure_schema()
        self._migrate_legacy_json()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                code TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                country TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT '',
                genres_json TEXT NOT NULL DEFAULT '[]',
                quality TEXT NOT NULL DEFAULT '',
                year TEXT NOT NULL DEFAULT '',
                views INTEGER NOT NULL DEFAULT 0,
                rating TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                actors_json TEXT NOT NULL DEFAULT '[]',
                media_type TEXT NOT NULL DEFAULT '',
                media_file_id TEXT NOT NULL DEFAULT '',
                poster TEXT NOT NULL DEFAULT '',
                video TEXT NOT NULL DEFAULT '',
                poster_url TEXT NOT NULL DEFAULT '',
                trailer_url TEXT NOT NULL DEFAULT '',
                source_chat_id TEXT,
                source_message_id INTEGER,
                plot TEXT NOT NULL DEFAULT '',
                runtime TEXT NOT NULL DEFAULT '',
                director TEXT NOT NULL DEFAULT '',
                writer TEXT NOT NULL DEFAULT '',
                awards TEXT NOT NULL DEFAULT '',
                imdb_votes TEXT NOT NULL DEFAULT '',
                imdb_id TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_movies_views ON movies(views DESC)")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year)")
        self._ensure_columns(
            {
                "plot": "TEXT NOT NULL DEFAULT ''",
                "runtime": "TEXT NOT NULL DEFAULT ''",
                "director": "TEXT NOT NULL DEFAULT ''",
                "writer": "TEXT NOT NULL DEFAULT ''",
                "awards": "TEXT NOT NULL DEFAULT ''",
                "imdb_votes": "TEXT NOT NULL DEFAULT ''",
                "imdb_id": "TEXT NOT NULL DEFAULT ''",
            }
        )
        self.connection.commit()

    def _ensure_columns(self, columns: dict[str, str]) -> None:
        existing = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(movies)").fetchall()
        }
        for name, sql_type in columns.items():
            if name not in existing:
                self.connection.execute(f"ALTER TABLE movies ADD COLUMN {name} {sql_type}")

    def _migrate_legacy_json(self) -> None:
        count = self.connection.execute("SELECT COUNT(*) AS count FROM movies").fetchone()["count"]
        if count or not self.legacy_json_path.exists():
            return

        with self.legacy_json_path.open("r", encoding="utf-8") as file:
            movies = json.load(file)
        for movie in movies:
            self._upsert_movie(movie)
        self.connection.commit()

    def _serialize_json(self, value) -> str:
        return json.dumps(value or [], ensure_ascii=False)

    def _row_to_movie(self, row: sqlite3.Row) -> dict:
        movie = dict(row)
        movie["genres"] = json.loads(movie.pop("genres_json", "[]") or "[]")
        movie["actors"] = json.loads(movie.pop("actors_json", "[]") or "[]")
        if movie.get("source_chat_id") is not None:
            try:
                movie["source_chat_id"] = int(movie["source_chat_id"])
            except (TypeError, ValueError):
                pass
        return movie

    def _movie_to_record(self, movie: dict) -> dict:
        return {
            "code": str(movie.get("code", "")).strip(),
            "title": movie.get("title", ""),
            "country": movie.get("country", ""),
            "language": movie.get("language", ""),
            "genres_json": self._serialize_json(movie.get("genres", [])),
            "quality": movie.get("quality", ""),
            "year": str(movie.get("year", "")),
            "views": int(movie.get("views", 0) or 0),
            "rating": str(movie.get("rating", "")),
            "description": movie.get("description", ""),
            "actors_json": self._serialize_json(movie.get("actors", [])),
            "media_type": movie.get("media_type", ""),
            "media_file_id": movie.get("media_file_id", ""),
            "poster": movie.get("poster", ""),
            "video": movie.get("video", ""),
            "poster_url": movie.get("poster_url", ""),
            "trailer_url": movie.get("trailer_url", ""),
            "source_chat_id": str(movie.get("source_chat_id")) if movie.get("source_chat_id") is not None else None,
            "source_message_id": movie.get("source_message_id"),
            "plot": movie.get("plot", ""),
            "runtime": movie.get("runtime", ""),
            "director": movie.get("director", ""),
            "writer": movie.get("writer", ""),
            "awards": movie.get("awards", ""),
            "imdb_votes": movie.get("imdb_votes", ""),
            "imdb_id": movie.get("imdb_id", ""),
        }

    def _upsert_movie(self, movie: dict) -> None:
        record = self._movie_to_record(movie)
        self.connection.execute(
            """
            INSERT INTO movies (
                code, title, country, language, genres_json, quality, year, views, rating, description,
                actors_json, media_type, media_file_id, poster, video, poster_url, trailer_url,
                source_chat_id, source_message_id, plot, runtime, director, writer, awards, imdb_votes, imdb_id
            ) VALUES (
                :code, :title, :country, :language, :genres_json, :quality, :year, :views, :rating, :description,
                :actors_json, :media_type, :media_file_id, :poster, :video, :poster_url, :trailer_url,
                :source_chat_id, :source_message_id, :plot, :runtime, :director, :writer, :awards, :imdb_votes, :imdb_id
            )
            ON CONFLICT(code) DO UPDATE SET
                title = excluded.title,
                country = excluded.country,
                language = excluded.language,
                genres_json = excluded.genres_json,
                quality = excluded.quality,
                year = excluded.year,
                views = excluded.views,
                rating = excluded.rating,
                description = excluded.description,
                actors_json = excluded.actors_json,
                media_type = excluded.media_type,
                media_file_id = excluded.media_file_id,
                poster = excluded.poster,
                video = excluded.video,
                poster_url = excluded.poster_url,
                trailer_url = excluded.trailer_url,
                source_chat_id = excluded.source_chat_id,
                source_message_id = excluded.source_message_id,
                plot = excluded.plot,
                runtime = excluded.runtime,
                director = excluded.director,
                writer = excluded.writer,
                awards = excluded.awards,
                imdb_votes = excluded.imdb_votes,
                imdb_id = excluded.imdb_id
            """,
            record,
        )

    def all(self) -> list[dict]:
        rows = self.connection.execute("SELECT * FROM movies").fetchall()
        return [self._row_to_movie(row) for row in rows]

    def get(self, code: str) -> dict | None:
        row = self.connection.execute("SELECT * FROM movies WHERE code = ?", (str(code),)).fetchone()
        return self._row_to_movie(row) if row else None

    def add(self, movie: dict) -> None:
        self._upsert_movie(movie)
        self.connection.commit()

    def update(self, code: str, updates: dict) -> dict | None:
        movie = self.get(code)
        if not movie:
            return None
        movie.update(updates)
        self._upsert_movie(movie)
        if str(movie.get("code")) != str(code):
            self.connection.execute("DELETE FROM movies WHERE code = ?", (str(code),))
        self.connection.commit()
        return self.get(movie["code"])

    def delete(self, code: str) -> dict | None:
        movie = self.get(code)
        if not movie:
            return None
        self.connection.execute("DELETE FROM movies WHERE code = ?", (str(code),))
        self.connection.commit()
        return movie

    def increment_views(self, code: str) -> dict | None:
        cursor = self.connection.execute(
            "UPDATE movies SET views = views + 1 WHERE code = ?",
            (str(code),),
        )
        self.connection.commit()
        if cursor.rowcount <= 0:
            return None
        return self.get(code)
