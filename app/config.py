import logging
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MOVIES_FILE = DATA_DIR / "movies.json"
USERS_FILE = DATA_DIR / "users.json"
SUBSCRIPTIONS_FILE = DATA_DIR / "subscriptions.json"
APP_DB_FILE = DATA_DIR / "bot.db"
EXPORTS_DIR = DATA_DIR / "exports"

load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

LOGGER = logging.getLogger(__name__)


def get_bot_token() -> str:
    token = os.getenv("BOT_TOKEN", "").strip()
    if token:
        return token
    raise RuntimeError("BOT_TOKEN topilmadi. .env fayl ichiga BOT_TOKEN=... yozing.")


def get_admin_ids() -> set[int]:
    raw = os.getenv("ADMIN_IDS", "").strip()
    if not raw:
        return set()
    return {int(item.strip()) for item in raw.split(",") if item.strip()}


def get_super_admin_ids() -> set[int]:
    raw = os.getenv("SUPER_ADMIN_IDS", "").strip()
    if raw:
        return {int(item.strip()) for item in raw.split(",") if item.strip()}
    return get_admin_ids()


def get_bot_owner_id() -> int | None:
    raw = os.getenv("BOT_OWNER_ID", "").strip()
    if raw:
        return int(raw)
    super_admins = sorted(get_super_admin_ids())
    if super_admins:
        return super_admins[0]
    admins = sorted(get_admin_ids())
    if admins:
        return admins[0]
    return None


def get_movies_chat_id() -> int | None:
    raw = os.getenv("MOVIES_CHAT_ID", "").strip()
    if not raw:
        return None
    return int(raw)


def get_omdb_api_key() -> str:
    return os.getenv("OMDB_API_KEY", "").strip()
