from telegram.constants import ChatMemberStatus

from app.data.subscription_repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, repository: SubscriptionRepository):
        self.repository = repository

    def state(self) -> dict:
        return self.repository.get_state()

    def enabled(self) -> bool:
        return bool(self.repository.get_state().get("enabled"))

    def channels(self) -> list[dict]:
        return list(self.repository.get_state().get("channels", []))

    def set_enabled(self, enabled: bool) -> None:
        self.repository.set_enabled(enabled)

    def add_channel(self, channel: dict) -> None:
        self.repository.add_channel(channel)

    def remove_channel(self, chat_id: str | int) -> bool:
        return self.repository.remove_channel(chat_id)

    async def is_user_allowed(self, bot, user_id: int | None) -> bool:
        if not self.enabled() or not user_id:
            return True

        for channel in self.channels():
            try:
                member = await bot.get_chat_member(channel["chat_id"], user_id)
            except Exception:
                return False

            if member.status not in {
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            }:
                return False

        return True
