from app.data.repository import MovieRepository
from app.utils.movie_normalization import (
    normalize_country_values,
    normalize_genre_values,
    normalize_key,
    normalize_language_values,
    normalize_text,
)


class MovieService:
    def __init__(self, repository: MovieRepository):
        self.repository = repository
        self._refresh_indexes()

    def _refresh_indexes(self) -> None:
        raw_movies = self.repository.all()
        sanitized_movies = []
        for movie in raw_movies:
            sanitized = self.sanitize_movie(movie)
            sanitized_movies.append(sanitized)
            if self._movie_changed(movie, sanitized):
                self.repository.add(sanitized)
        self._movies = sanitized_movies
        self._movie_by_code = {str(movie["code"]): movie for movie in self._movies}

    def get_movie(self, code: str) -> dict | None:
        return self._movie_by_code.get(str(code))

    def increment_views(self, code: str) -> dict | None:
        movie = self.repository.increment_views(code)
        if movie:
            self._refresh_indexes()
        return movie

    def all_movies(self) -> list[dict]:
        return list(self._movies)

    def top_movies(self, limit: int = 10) -> list[dict]:
        return sorted(self._movies, key=lambda item: int(item.get("views", 0)), reverse=True)[:limit]

    def search_movies(self, query: str) -> list[dict]:
        lowered = self.normalize_value(query)
        results = []
        for movie in self._movies:
            actor_hit = any(lowered in self.normalize_value(actor.get("name", "")) for actor in movie.get("actors", []))
            searchable_parts = [
                movie.get("title", ""),
                movie.get("plot", ""),
                str(movie.get("code", "")),
                movie.get("country", ""),
                movie.get("language", ""),
            ]
            genre_hit = any(lowered in self.normalize_value(genre) for genre in movie.get("genres", []))
            if actor_hit or genre_hit or any(lowered in self.normalize_value(part) for part in searchable_parts):
                results.append(movie)
        return sorted(results, key=lambda item: int(item.get("views", 0)), reverse=True)

    def search_inline_movies(self, query: str, limit: int = 20) -> list[dict]:
        raw = (query or "").strip()
        normalized = self.normalize_value(raw)
        if not normalized:
            return sorted(self._movies, key=lambda item: item["title"].lower())[:limit]

        if normalized == "top_films":
            return self.top_movies(limit=limit)

        if ":" in raw:
            field_name, raw_value = raw.split(":", maxsplit=1)
            field = field_name.strip().lower()
            value = raw_value.strip()
            field_map = {
                "country": "country",
                "genre": "genre",
                "language": "language",
                "year": "year",
                "actor": "actors",
            }
            mapped_field = field_map.get(field)
            if mapped_field and value:
                movies = self.filter_movies({mapped_field: value})
                return sorted(movies, key=lambda item: int(item.get("views", 0)), reverse=True)[:limit]

        return self.search_movies(raw)[:limit]

    def actor_movies(self, actor_name: str, limit: int = 20) -> list[dict]:
        needle = self.normalize_value(actor_name)
        results = []
        for movie in self._movies:
            if any(needle == self.normalize_value(actor.get("name", "")) for actor in movie.get("actors", [])):
                results.append(movie)
        return sorted(results, key=lambda item: int(item.get("views", 0)), reverse=True)[:limit]

    def add_movie(self, movie: dict) -> None:
        self.repository.add(self.sanitize_movie(movie))
        self._refresh_indexes()

    def update_movie(self, code: str, updates: dict) -> dict | None:
        current = self.repository.get(code)
        if not current:
            return None
        current.update(updates)
        movie = self.repository.update(code, self.sanitize_movie(current))
        if movie:
            self._refresh_indexes()
        return movie

    def delete_movie(self, code: str) -> dict | None:
        movie = self.repository.delete(code)
        if movie:
            self._refresh_indexes()
        return movie

    def filter_options(self, field: str) -> list[str]:
        options = set()
        for movie in self._movies:
            options.update(self.get_movie_value_list(movie, field))
        return sorted(options)

    def filter_movies(self, selected_filters: dict[str, str]) -> list[dict]:
        results = []
        normalized_filters = {
            field: self.normalize_value(value)
            for field, value in selected_filters.items()
            if str(value).strip()
        }
        for movie in self._movies:
            matched = True
            for field, expected in normalized_filters.items():
                values = [self.normalize_value(item) for item in self.get_movie_value_list(movie, field)]
                if expected not in values:
                    matched = False
                    break
            if matched:
                results.append(movie)
        return results

    @staticmethod
    def get_movie_value_list(movie: dict, field: str) -> list[str]:
        if field == "genre":
            return normalize_genre_values(movie.get("genres", []))
        if field == "actors":
            return [actor.get("name", "") for actor in movie.get("actors", [])]
        if field == "country":
            return normalize_country_values(movie.get("country", ""))
        if field == "language":
            return normalize_language_values(movie.get("language", ""))
        raw = movie.get(field, "")
        return [item.strip() for item in str(raw).split(",") if item.strip()]

    @staticmethod
    def normalize_value(value: str) -> str:
        return normalize_key(value)

    def sanitize_movie(self, movie: dict) -> dict:
        sanitized = dict(movie)
        sanitized["country"] = ", ".join(normalize_country_values(movie.get("country", "")))
        sanitized["language"] = ", ".join(normalize_language_values(movie.get("language", "")))
        sanitized["genres"] = normalize_genre_values(movie.get("genres", []))
        sanitized["title"] = normalize_text(movie.get("title", ""))
        sanitized["quality"] = normalize_text(movie.get("quality", ""))
        sanitized["year"] = normalize_text(movie.get("year", ""))
        return sanitized

    @staticmethod
    def _movie_changed(original: dict, sanitized: dict) -> bool:
        return (
            original.get("country", "") != sanitized.get("country", "")
            or original.get("language", "") != sanitized.get("language", "")
            or list(original.get("genres", [])) != list(sanitized.get("genres", []))
            or original.get("title", "") != sanitized.get("title", "")
            or original.get("quality", "") != sanitized.get("quality", "")
            or str(original.get("year", "")) != str(sanitized.get("year", ""))
        )
