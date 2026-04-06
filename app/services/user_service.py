from datetime import datetime, timedelta, timezone

from app.data.user_repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_user(self, telegram_user) -> dict | None:
        if not telegram_user:
            return None
        return self.repository.upsert(
            {
                "user_id": telegram_user.id,
                "username": telegram_user.username or "",
                "full_name": telegram_user.full_name or "",
            }
        )

    def track_message(self, telegram_user) -> None:
        user = self.register_user(telegram_user)
        if user:
            self.repository.increment_message_count(user["user_id"])

    def track_movie_request(self, telegram_user, code: str) -> None:
        user = self.register_user(telegram_user)
        if user:
            self.repository.add_requested_movie(user["user_id"], code)

    def all_users(self) -> list[dict]:
        return self.repository.all()

    def get_user(self, user_id: int | str | None) -> dict | None:
        if user_id is None:
            return None
        return self.repository.get(user_id)

    def saved_movie_codes(self, user_id: int | str | None) -> list[str]:
        user = self.get_user(user_id)
        if not user:
            return []
        return [str(code) for code in user.get("saved_movie_codes", [])]

    def is_movie_saved(self, user_id: int | str | None, code: str) -> bool:
        return str(code) in self.saved_movie_codes(user_id)

    def toggle_saved_movie(self, user_id: int | str | None, code: str) -> bool:
        if user_id is None:
            return False
        if not self.repository.get(user_id):
            self.repository.upsert({"user_id": int(user_id), "username": "", "full_name": ""})
        _, is_saved = self.repository.toggle_saved_movie(user_id, str(code))
        return is_saved

    def summary(self) -> dict:
        users = self.repository.all()
        total = len(users)
        now = datetime.now(timezone.utc)
        active_24h = 0
        for user in users:
            last_seen_raw = user.get("last_seen_at")
            if not last_seen_raw:
                continue
            try:
                last_seen = datetime.fromisoformat(last_seen_raw)
            except ValueError:
                continue
            if last_seen >= now - timedelta(hours=24):
                active_24h += 1

        recent_users = sorted(
            users,
            key=lambda item: item.get("last_seen_at", ""),
            reverse=True,
        )[:10]
        top_users = sorted(
            users,
            key=lambda item: int(item.get("message_count", 0)),
            reverse=True,
        )[:10]
        return {
            "total_users": total,
            "active_24h": active_24h,
            "recent_users": recent_users,
            "top_users": top_users,
        }
