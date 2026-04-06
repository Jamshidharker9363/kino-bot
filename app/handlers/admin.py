from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.config import get_movies_chat_id
from app.handlers.common import send_movie_message
from app.keyboards.admin import (
    admin_delete_confirm_keyboard,
    admin_edit_fields_keyboard,
    admin_language_keyboard,
    admin_list_keyboard,
    admin_movie_manage_keyboard,
    admin_movies_keyboard,
    admin_panel_keyboard,
    admin_subscriptions_keyboard,
    admin_subscriptions_remove_keyboard,
    admin_users_export_keyboard,
)
from app.keyboards.user import shared_movie_keyboard
from app.services.admin_service import AdminService
from app.services.movie_service import MovieService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.utils.exporters import export_users_to_pdf, export_users_to_xlsx
from app.utils.formatters import movie_caption


ADMIN_STEPS = [
    ("media", "Avval kino faylini yuboring. Video, document yoki poster rasm yuborishingiz mumkin."),
    ("code", "Yangi kino kodini yuboring."),
    ("title", "Kino nomini yuboring."),
    ("country", "Davlatni yuboring. Masalan: AQSH, Yaponiya"),
    ("genres", "Janrlarni vergul bilan yuboring. Masalan: Jangari, Drama"),
    ("year", "Yilni yuboring."),
    ("rating", "Reytingni yuboring. Agar kerak bo'lmasa <code>-</code> yuboring."),
    ("quality", "Sifatni yuboring. Agar kerak bo'lmasa <code>-</code> yuboring."),
    ("poster_url", "Poster URL yuboring. Agar yo'q bo'lsa <code>-</code> yuboring."),
    ("extra_description", "Qo'shimcha description yuboring. Agar kerak bo'lmasa <code>-</code> yuboring."),
]

EDIT_FIELD_PROMPTS = {
    "code": "Yangi kodni yuboring.",
    "title": "Yangi kino nomini yuboring.",
    "country": "Yangi davlatni yuboring.",
    "language": "Yangi tilni yuboring.",
    "genres": "Yangi janrlarni vergul bilan yuboring.",
    "quality": "Yangi sifatni yuboring. Bo'sh qilish uchun <code>-</code> yuboring.",
    "year": "Yangi yilni yuboring.",
    "rating": "Yangi reytingni yuboring. Bo'sh qilish uchun <code>-</code> yuboring.",
    "description": "Yangi description yuboring. Bo'sh qilish uchun <code>-</code> yuboring.",
    "poster_url": "Yangi poster URL yuboring. Bo'sh qilish uchun <code>-</code> yuboring.",
}


class AdminHandler:
    def __init__(
        self,
        movie_service: MovieService,
        user_service: UserService,
        subscription_service: SubscriptionService,
        admin_service: AdminService,
    ):
        self.movie_service = movie_service
        self.user_service = user_service
        self.subscription_service = subscription_service
        self.admin_service = admin_service
        self.movies_chat_id = get_movies_chat_id()

    def is_admin(self, user_id: int | None) -> bool:
        return self.admin_service.is_admin(user_id)

    def is_super_admin(self, user_id: int | None) -> bool:
        return self.admin_service.is_super_admin(user_id)

    async def open_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        target = update.message or (update.callback_query.message if update.callback_query else None)
        user_id = update.effective_user.id if update.effective_user else None
        if not target:
            return
        if not self.is_admin(user_id):
            await target.reply_text("Siz admin emassiz.")
            return
        await target.reply_text(
            "⚙️ <b>Admin panel</b>\nKerakli bo'limni tanlang.",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_panel_keyboard(self.is_super_admin(user_id)),
        )

    async def subscriptions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and self.is_admin(update.effective_user.id if update.effective_user else None):
            await self.send_subscription_panel(update.message)

    async def new_message_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not self.is_admin(update.effective_user.id if update.effective_user else None):
            return
        context.user_data["admin_state"] = {"mode": "broadcast"}
        await update.message.reply_text("Userlarga yuboriladigan xabar yoki media yuboring.")

    async def info_film_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and self.is_admin(update.effective_user.id if update.effective_user else None):
            await self.send_movie_summary(update.message)

    async def films_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and self.is_admin(update.effective_user.id if update.effective_user else None):
            await self.send_movie_list(update.message, page=0)

    async def users_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and self.is_admin(update.effective_user.id if update.effective_user else None):
            await self.send_user_summary(update.message)

    async def add_new_film_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not self.is_admin(update.effective_user.id if update.effective_user else None):
            return
        context.user_data["admin_state"] = {"mode": "add_movie", "step_index": 0, "movie": {}, "selected_languages": []}
        await update.message.reply_text(ADMIN_STEPS[0][1], parse_mode=ParseMode.HTML)

    async def on_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        query = update.callback_query
        if not query or not query.data or not query.data.startswith("admin:"):
            return False

        user_id = update.effective_user.id if update.effective_user else None
        if not self.is_admin(user_id):
            await query.message.reply_text("Siz admin emassiz.")
            return True

        parts = query.data.split(":")
        action = parts[1]

        if action == "add":
            context.user_data["admin_state"] = {"mode": "add_movie", "step_index": 0, "movie": {}, "selected_languages": []}
            await query.message.reply_text(ADMIN_STEPS[0][1], parse_mode=ParseMode.HTML)
            return True
        if action == "list":
            page = int(parts[2]) if len(parts) > 2 else 0
            await self.send_movie_list(query.message, page=page)
            return True
        if action == "back":
            await self.open_panel(update, context)
            return True
        if action == "users":
            await self.send_user_summary(query.message)
            return True
        if action == "users_export":
            await self.send_users_export(query.message, parts[2])
            return True
        if action == "movie_stats":
            await self.send_movie_summary(query.message)
            return True
        if action == "broadcast":
            context.user_data["admin_state"] = {"mode": "broadcast"}
            await query.message.reply_text("Userlarga yuboriladigan xabar yoki media yuboring.")
            return True
        if action == "announce":
            movie = self.movie_service.get_movie(parts[2])
            if movie:
                await self.announce_movie(query.message, context, movie)
            else:
                await query.message.reply_text("Kino topilmadi.")
            return True
        if action == "subs":
            await self.send_subscription_panel(query.message)
            return True
        if action == "subs_add":
            context.user_data["admin_state"] = {"mode": "subs_add_chat_id"}
            await query.message.reply_text("Majburiy obuna uchun kanal yoki guruh chat ID sini yuboring.")
            return True
        if action == "subs_add_auto":
            context.user_data["admin_state"] = {"mode": "subs_add_auto"}
            await query.message.reply_text("Kanal yoki guruhdan biror postni forward qiling.")
            return True
        if action == "subs_remove":
            await query.message.reply_text("O'chiriladigan kanalni tanlang.", reply_markup=admin_subscriptions_remove_keyboard(self.subscription_service.channels()))
            return True
        if action == "subs_toggle":
            self.subscription_service.set_enabled(not self.subscription_service.enabled())
            await self.send_subscription_panel(query.message)
            return True
        if action == "subs_delete":
            self.subscription_service.remove_channel(parts[2])
            await self.send_subscription_panel(query.message)
            return True
        if action == "admins":
            if not self.is_super_admin(user_id):
                await query.message.reply_text("Bu bo'lim faqat super admin uchun.")
            else:
                await self.send_admins_panel(query.message)
            return True
        if action == "add_admin":
            if not self.is_super_admin(user_id):
                await query.message.reply_text("Bu bo'lim faqat super admin uchun.")
            else:
                context.user_data["admin_state"] = {"mode": "add_admin"}
                await query.message.reply_text("Yangi adminning Telegram ID sini yuboring.")
            return True
        if action == "remove_admin":
            if not self.is_super_admin(user_id):
                await query.message.reply_text("Bu bo'lim faqat super admin uchun.")
            else:
                removed = self.admin_service.remove_admin(int(parts[2]))
                await query.message.reply_text("Admin o'chirildi." if removed else "Adminni o'chirib bo'lmadi.")
            return True
        if action == "lang_toggle":
            state = context.user_data.get("admin_state", {})
            if state.get("mode") != "language_select":
                return True
            language = parts[2]
            selected = list(state.get("selected_languages", []))
            if language in selected:
                selected.remove(language)
            else:
                selected.append(language)
            state["selected_languages"] = selected
            context.user_data["admin_state"] = state
            await query.edit_message_reply_markup(reply_markup=admin_language_keyboard(selected))
            return True
        if action == "lang_done":
            state = context.user_data.get("admin_state", {})
            selected = list(state.get("selected_languages", []))
            if state.get("mode") != "language_select":
                return True
            if not selected:
                await query.answer("Kamida bitta til tanlang.", show_alert=True)
                return True
            state["movie"]["language"] = ", ".join(selected)
            state["mode"] = "add_movie"
            state["step_index"] = 5
            context.user_data["admin_state"] = state
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(ADMIN_STEPS[state["step_index"]][1], parse_mode=ParseMode.HTML)
            return True
        if action == "manage":
            await self.send_movie_manage(query.message, parts[2])
            return True
        if action == "view":
            movie = self.movie_service.get_movie(parts[2])
            if movie:
                await send_movie_message(query.message, movie)
            else:
                await query.message.reply_text("Kino topilmadi.")
            return True
        if action == "edit":
            movie = self.movie_service.get_movie(parts[2])
            if not movie:
                await query.message.reply_text("Kino topilmadi.")
            else:
                await query.message.reply_text(f"✏️ <b>{movie['title']}</b> uchun maydon tanlang.", parse_mode=ParseMode.HTML, reply_markup=admin_edit_fields_keyboard(parts[2]))
            return True
        if action == "editfield":
            code = parts[2]
            field = parts[3]
            if not self.movie_service.get_movie(code):
                await query.message.reply_text("Kino topilmadi.")
            else:
                context.user_data["admin_state"] = {"mode": "edit_movie", "code": code, "field": field}
                await query.message.reply_text(EDIT_FIELD_PROMPTS[field], parse_mode=ParseMode.HTML)
            return True
        if action == "delete":
            movie = self.movie_service.get_movie(parts[2])
            if not movie:
                await query.message.reply_text("Kino topilmadi.")
            else:
                await query.message.reply_text(f"🗑 <b>{movie['title']}</b> kinoni o'chirishni tasdiqlaysizmi?", parse_mode=ParseMode.HTML, reply_markup=admin_delete_confirm_keyboard(parts[2]))
            return True
        if action == "confirm_delete":
            movie = self.movie_service.get_movie(parts[2])
            if movie:
                await self.delete_storage_post(context.bot, movie)
            deleted = self.movie_service.delete_movie(parts[2])
            if deleted:
                await query.message.reply_text(f"O'chirildi: <b>{deleted['title']}</b> (<code>{deleted['code']}</code>)", parse_mode=ParseMode.HTML)
            else:
                await query.message.reply_text("Kino topilmadi.")
            return True
        if action == "cancel":
            context.user_data.pop("admin_state", None)
            await query.message.reply_text("Admin amal bekor qilindi.")
            return True
        return False

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        if not update.message or not self.is_admin(update.effective_user.id if update.effective_user else None):
            return False

        state = context.user_data.get("admin_state")
        if not state:
            return False

        if state.get("mode") == "broadcast":
            await self.broadcast_message(update, context)
            return True

        if state.get("mode") == "subs_add_auto":
            auto_channel = await self.extract_subscription_channel(update, context)
            if not auto_channel:
                await update.message.reply_text("Forward qilingan kanal yoki guruh postini yuboring.")
                return True
            self.subscription_service.add_channel(auto_channel)
            context.user_data.pop("admin_state", None)
            await update.message.reply_text(f"Majburiy obuna kanali qo'shildi: <b>{auto_channel['title']}</b>", parse_mode=ParseMode.HTML)
            return True

        if not update.message.text and state.get("mode") not in {"broadcast", "add_movie"}:
            return False

        if state.get("mode") == "subs_add_chat_id":
            context.user_data["admin_state"] = {"mode": "subs_add_link", "chat_id": update.message.text.strip()}
            await update.message.reply_text("Endi kanal linkini yuboring. Masalan: https://t.me/kanal")
            return True

        if state.get("mode") == "subs_add_link":
            chat_id = state["chat_id"]
            link = update.message.text.strip()
            try:
                chat = await context.bot.get_chat(chat_id)
                title = chat.title or chat.username or str(chat_id)
            except Exception:
                title = str(chat_id)
            self.subscription_service.add_channel({"chat_id": chat_id, "title": title, "url": link})
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("Majburiy obuna kanali qo'shildi.")
            return True

        if state.get("mode") == "add_admin":
            try:
                new_admin_id = int(update.message.text.strip())
            except (TypeError, ValueError):
                await update.message.reply_text("To'g'ri Telegram ID yuboring.")
                return True
            self.admin_service.add_admin(new_admin_id, update.effective_user.id if update.effective_user else None)
            context.user_data.pop("admin_state", None)
            await update.message.reply_text(f"Yangi admin qo'shildi: <code>{new_admin_id}</code>", parse_mode=ParseMode.HTML)
            return True

        if state.get("mode") == "edit_movie":
            await self.edit_movie_field(update, context, update.message.text.strip())
            return True

        if state.get("mode") == "language_select":
            await update.message.reply_text("Tillarni pastdagi tugmalar orqali tanlang.")
            return True

        if state.get("mode") != "add_movie":
            return False

        field, _ = ADMIN_STEPS[state["step_index"]]
        if field == "media":
            media = self.extract_media(update)
            if not media:
                await update.message.reply_text("Kino qo'shish uchun video, document yoki rasm yuboring.")
                return True
            state["movie"].update(media)
            state["step_index"] = 1
            context.user_data["admin_state"] = state
            await update.message.reply_text(ADMIN_STEPS[1][1], parse_mode=ParseMode.HTML)
            return True

        if not update.message.text:
            await update.message.reply_text("Matn ko'rinishida javob yuboring.")
            return True

        value = update.message.text.strip()
        normalized = "" if value == "-" else value
        if field == "code" and self.movie_service.get_movie(normalized):
            await update.message.reply_text("Bu kod allaqachon mavjud. Boshqa kod yuboring.")
            return True

        if field in {"rating", "quality", "poster_url", "extra_description"}:
            state["movie"][field] = normalized
        elif field == "genres":
            state["movie"][field] = [item.strip() for item in normalized.split(",") if item.strip()]
        else:
            state["movie"][field] = normalized

        if field == "genres":
            state["mode"] = "language_select"
            state["selected_languages"] = []
            context.user_data["admin_state"] = state
            await update.message.reply_text("Endi kino uchun mavjud tillarni tanlang.", reply_markup=admin_language_keyboard([]))
            return True

        state["step_index"] += 1
        context.user_data["admin_state"] = state
        if state["step_index"] >= len(ADMIN_STEPS):
            movie = {
                "media_type": state["movie"]["media_type"],
                "media_file_id": state["movie"]["media_file_id"],
                "code": state["movie"]["code"],
                "title": state["movie"].get("title", ""),
                "country": state["movie"].get("country", ""),
                "language": state["movie"].get("language", ""),
                "genres": state["movie"].get("genres", []),
                "quality": state["movie"].get("quality", ""),
                "year": state["movie"].get("year", ""),
                "views": 0,
                "rating": state["movie"].get("rating", ""),
                "description": state["movie"].get("extra_description", ""),
                "actors": [],
                "plot": "",
                "runtime": "",
                "director": "",
                "writer": "",
                "awards": "",
                "imdb_votes": "",
                "imdb_id": "",
                "poster": "",
                "video": "",
                "poster_url": state["movie"].get("poster_url", ""),
                "trailer_url": "",
                "source_chat_id": None,
                "source_message_id": None,
            }
            published = await self.publish_movie_to_storage_chat(update, movie)
            if not published:
                return True
            self.movie_service.add_movie(movie)
            context.user_data.pop("admin_state", None)
            await update.message.reply_text(
                f"Kino qo'shildi.\nKod: <code>{movie['code']}</code>\nNomi: <b>{movie['title']}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📣 Reklama yuborish", callback_data=f"admin:announce:{movie['code']}"), InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="admin:back")]]),
            )
            return True

        await update.message.reply_text(ADMIN_STEPS[state["step_index"]][1], parse_mode=ParseMode.HTML)
        return True

    async def send_movie_list(self, message, page: int = 0) -> None:
        movies = self.movie_service.all_movies()
        if not movies:
            await message.reply_text("Kinolar hozircha yo'q.")
            return
        await message.reply_text("📋 <b>Barcha kinolar</b>\nKerakli kinoni tanlang.", parse_mode=ParseMode.HTML, reply_markup=admin_movies_keyboard(movies, page=page))

    async def send_movie_manage(self, message, code: str) -> None:
        movie = self.movie_service.get_movie(code)
        if not movie:
            await message.reply_text("Kino topilmadi.")
            return
        await message.reply_text(f"🎬 <b>{movie['title']}</b>\nKod: <code>{movie['code']}</code>", parse_mode=ParseMode.HTML, reply_markup=admin_movie_manage_keyboard(code))

    async def send_user_summary(self, message) -> None:
        summary = self.user_service.summary()
        lines = ["👥 <b>Foydalanuvchilar statistikasi</b>", "", f"Jami userlar: <b>{summary['total_users']}</b>", f"So'nggi 24 soatda faol: <b>{summary['active_24h']}</b>", "", "<b>Eng faol userlar:</b>"]
        if summary["top_users"]:
            for user in summary["top_users"][:5]:
                name = user.get("full_name") or user.get("username") or str(user["user_id"])
                lines.append(f"• {name} | xabarlar: {user.get('message_count', 0)}")
        else:
            lines.append("• Hozircha userlar yo'q")
        await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=admin_users_export_keyboard())

    async def send_users_export(self, message, export_type: str) -> None:
        users = self.user_service.all_users()
        path = export_users_to_xlsx(users) if export_type == "xlsx" else export_users_to_pdf(users)
        with open(path, "rb") as file:
            await message.reply_document(document=file, filename=path.split("\\")[-1])

    async def send_subscription_panel(self, message) -> None:
        channels = self.subscription_service.channels()
        enabled = self.subscription_service.enabled()
        status_text = "Yoqilgan" if enabled else "O'chirilgan"
        text = f"🔐 <b>Majburiy obuna</b>\n\nHolat: <b>{status_text}</b>\nKanallar soni: <b>{len(channels)}</b>"
        await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=admin_subscriptions_keyboard(enabled, channels))

    async def send_admins_panel(self, message) -> None:
        await message.reply_text("🛡 <b>Adminlar ro'yxati</b>\nKerak bo'lsa adminni o'chiring yoki yangi admin qo'shing.", parse_mode=ParseMode.HTML, reply_markup=admin_list_keyboard(self.admin_service.manageable_admin_ids()))

    async def send_movie_summary(self, message) -> None:
        movies = self.movie_service.all_movies()
        lines = ["📈 <b>Kinolar statistikasi</b>", "", f"Jami kinolar: <b>{len(movies)}</b>", "", "<b>Eng ko'p ko'rilganlar:</b>"]
        top_movies = self.movie_service.top_movies(limit=5)
        if top_movies:
            for movie in top_movies:
                lines.append(f"• {movie['title']} | kod: <code>{movie['code']}</code> | 👁 {movie['views']}")
        else:
            lines.append("• Hozircha kinolar yo'q")
        await message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    def extract_media(self, update: Update) -> dict | None:
        message = update.message
        if message.video:
            return {"media_type": "video", "media_file_id": message.video.file_id}
        if message.document:
            return {"media_type": "document", "media_file_id": message.document.file_id}
        if message.photo:
            return {"media_type": "photo", "media_file_id": message.photo[-1].file_id}
        return None

    async def extract_subscription_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict | None:
        message = update.message
        candidate_chat = getattr(message, "forward_from_chat", None)
        if not candidate_chat and getattr(message, "forward_origin", None):
            origin = message.forward_origin
            candidate_chat = getattr(origin, "chat", None) or getattr(origin, "sender_chat", None)
        if not candidate_chat and getattr(message, "sender_chat", None):
            candidate_chat = message.sender_chat
        if not candidate_chat:
            return None
        title = candidate_chat.title or candidate_chat.username or str(candidate_chat.id)
        username = getattr(candidate_chat, "username", None)
        url = f"https://t.me/{username}" if username else ""
        if not url:
            try:
                chat = await context.bot.get_chat(candidate_chat.id)
                if chat.username:
                    url = f"https://t.me/{chat.username}"
            except Exception:
                pass
        return {"chat_id": candidate_chat.id, "title": title, "url": url or "https://t.me"}

    async def publish_movie_to_storage_chat(self, update: Update, movie: dict) -> bool:
        if not self.movies_chat_id:
            await update.message.reply_text("MOVIES_CHAT_ID sozlanmagan. .env ichiga kanal yoki guruh id sini yozing.")
            return False
        bot = update.get_bot()
        bot_username = bot.username or (await bot.get_me()).username
        caption = movie_caption(movie, bot_username)
        shared_markup = shared_movie_keyboard(movie, bot_username)
        try:
            if movie["media_type"] == "video":
                sent = await bot.send_video(chat_id=self.movies_chat_id, video=movie["media_file_id"], caption=caption, parse_mode=ParseMode.HTML, reply_markup=shared_markup)
            elif movie["media_type"] == "document":
                sent = await bot.send_document(chat_id=self.movies_chat_id, document=movie["media_file_id"], caption=caption, parse_mode=ParseMode.HTML, reply_markup=shared_markup)
            else:
                sent = await bot.send_photo(chat_id=self.movies_chat_id, photo=movie["media_file_id"], caption=caption, parse_mode=ParseMode.HTML, reply_markup=shared_markup)
        except Exception as error:
            await update.message.reply_text(f"Kanal/guruhga yuborishda xato chiqdi: {error}")
            return False
        movie["source_chat_id"] = sent.chat_id
        movie["source_message_id"] = sent.message_id
        return True

    async def sync_storage_post(self, bot, movie: dict) -> None:
        source_chat_id = movie.get("source_chat_id")
        source_message_id = movie.get("source_message_id")
        if not source_chat_id or not source_message_id:
            return
        bot_username = bot.username or (await bot.get_me()).username
        caption = movie_caption(movie, bot_username)
        reply_markup = shared_movie_keyboard(movie, bot_username)
        try:
            await bot.edit_message_caption(chat_id=source_chat_id, message_id=source_message_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        except Exception:
            try:
                await bot.edit_message_reply_markup(chat_id=source_chat_id, message_id=source_message_id, reply_markup=reply_markup)
            except Exception:
                pass

    async def delete_storage_post(self, bot, movie: dict) -> None:
        source_chat_id = movie.get("source_chat_id")
        source_message_id = movie.get("source_message_id")
        if not source_chat_id or not source_message_id:
            return
        try:
            await bot.delete_message(chat_id=source_chat_id, message_id=source_message_id)
        except Exception:
            pass

    async def edit_movie_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE, value: str) -> None:
        state = context.user_data.get("admin_state", {})
        code = state.get("code")
        field = state.get("field")
        movie = self.movie_service.get_movie(code)
        if not movie or not field:
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("Tahrirlash uchun kino topilmadi.")
            return
        normalized = "" if value == "-" else value
        if field == "code" and normalized != code and self.movie_service.get_movie(normalized):
            await update.message.reply_text("Bu kod allaqachon mavjud. Boshqa kod yuboring.")
            return
        updates = {field: [item.strip() for item in normalized.split(",") if item.strip()] if field == "genres" else normalized}
        updated = self.movie_service.update_movie(code, updates)
        context.user_data.pop("admin_state", None)
        if not updated:
            await update.message.reply_text("Kino yangilanmadi.")
            return
        await self.sync_storage_post(context.bot, updated)
        await update.message.reply_text(f"Yangilandi.\n<b>{updated['title']}</b>\nMaydon: <code>{field}</code>", parse_mode=ParseMode.HTML)

    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        context.user_data.pop("admin_state", None)
        users = self.user_service.all_users()
        sent_count = 0
        failed_count = 0
        source_message = update.message
        for user in users:
            try:
                await context.bot.copy_message(chat_id=user["user_id"], from_chat_id=source_message.chat_id, message_id=source_message.message_id)
                sent_count += 1
            except Exception:
                failed_count += 1
        await update.message.reply_text(f"Xabar yuborildi.\nYetib bordi: <b>{sent_count}</b>\nYuborilmadi: <b>{failed_count}</b>", parse_mode=ParseMode.HTML)

    async def announce_movie(self, message, context: ContextTypes.DEFAULT_TYPE, movie: dict) -> None:
        users = self.user_service.all_users()
        sent_count = 0
        failed_count = 0
        bot = context.bot
        bot_username = bot.username or (await bot.get_me()).username
        reply_markup = shared_movie_keyboard(movie, bot_username)
        caption = movie_caption(movie, bot_username)
        poster_url = (movie.get("poster_url") or "").strip()
        for user in users:
            try:
                if poster_url:
                    await bot.send_photo(chat_id=int(user["user_id"]), photo=poster_url, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                elif movie.get("media_type") == "photo" and movie.get("media_file_id"):
                    await bot.send_photo(chat_id=int(user["user_id"]), photo=movie["media_file_id"], caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                else:
                    await bot.send_message(chat_id=int(user["user_id"]), text=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                sent_count += 1
            except Exception:
                failed_count += 1
        await message.reply_text(f"Reklama yuborildi.\nYetib bordi: <b>{sent_count}</b>\nYuborilmadi: <b>{failed_count}</b>", parse_mode=ParseMode.HTML)
