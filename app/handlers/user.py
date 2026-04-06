from telegram import InlineQueryResultArticle, InlineQueryResultCachedPhoto, InlineQueryResultPhoto, InputTextMessageContent, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.handlers.common import send_movie_list_card, send_movie_message
from app.keyboards.subscription import subscription_keyboard
from app.keyboards.user import direct_movie_keyboard, filter_menu_keyboard, filter_options_keyboard, shared_movie_keyboard, start_keyboard
from app.services.movie_service import MovieService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.utils.formatters import movie_caption, movie_list_caption


class UserHandler:
    def __init__(self, movie_service: MovieService, user_service: UserService, subscription_service: SubscriptionService):
        self.movie_service = movie_service
        self.user_service = user_service
        self.subscription_service = subscription_service

    async def ensure_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        if await self.subscription_service.is_user_allowed(context.bot, update.effective_user.id if update.effective_user else None):
            return True
        text = (
            "😊 <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling</b>\n\n"
            "Obuna bo'lgach <b>✅ Tekshirish</b> tugmasini bosing."
        )
        keyboard = subscription_keyboard(self.subscription_service.channels())
        target = update.message or update.callback_query.message or update.effective_message
        if target:
            await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return False

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        self.user_service.register_user(update.effective_user)
        if not await self.ensure_subscription(update, context):
            return
        if context.args:
            raw_arg = context.args[0].strip()
            code = raw_arg.removeprefix("code_")
            movie = self.movie_service.increment_views(code)
            if update.message and movie:
                self.user_service.track_movie_request(update.effective_user, code)
                await send_movie_message(
                    update.message,
                    movie,
                    is_saved=self.user_service.is_movie_saved(update.effective_user.id if update.effective_user else None, code),
                )
                return
        text = (
            "👋 <b>Assalomu alaykum</b>, botimizga xush kelibsiz\n\n"
            "🎥 <i>Bot orqali siz sevimli filmlarni sifatli formatda ko'rishingiz mumkin</i>\n\n"
            "🚀 <b>Shunchaki</b>\n"
            "— Kino kodini yuboring\n"
            "— Pastdagi bo'limlardan birini tanlang va zavqlaning 😊"
        )
        target = update.message or (update.callback_query.message if update.callback_query else None)
        if target:
            await target.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=start_keyboard())

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            await update.message.reply_text("Kino kodini yuboring. Misol: 1262", parse_mode=ParseMode.HTML)

    async def my_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and update.effective_user:
            await update.message.reply_text(f"Sizning Telegram ID: <code>{update.effective_user.id}</code>", parse_mode=ParseMode.HTML)

    async def chat_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message and update.effective_chat:
            await update.message.reply_text(f"Ushbu chat ID: <code>{update.effective_chat.id}</code>", parse_mode=ParseMode.HTML)

    async def inline_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.inline_query
        if not query:
            return
        self.user_service.register_user(update.effective_user)
        if not await self.subscription_service.is_user_allowed(context.bot, update.effective_user.id if update.effective_user else None):
            await query.answer(results=[], cache_time=0, is_personal=True, switch_pm_text="Avval obuna bo'ling", switch_pm_parameter="subscribe")
            return

        bot_username = context.bot.username or (await context.bot.get_me()).username
        text = (query.query or "").strip()
        user_id = update.effective_user.id if update.effective_user else None
        if text.strip().lower() == "saved_films":
            movies = []
            for code in self.user_service.saved_movie_codes(user_id):
                movie = self.movie_service.get_movie(code)
                if movie:
                    movies.append(movie)
        else:
            movies = self.movie_service.search_inline_movies(text, limit=30)
        results = []
        for movie in movies:
            keyboard = shared_movie_keyboard(movie, bot_username)
            preview_text = movie_list_caption(movie).replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
            poster_url = (movie.get("poster_url") or "").strip()
            media_type = movie.get("media_type")
            media_file_id = movie.get("media_file_id")
            if media_type == "photo" and media_file_id:
                results.append(
                    InlineQueryResultCachedPhoto(
                        id=f"photo-{movie['code']}",
                        photo_file_id=media_file_id,
                        caption=movie_caption(movie, bot_username),
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
                    )
                )
                continue
            if poster_url:
                results.append(
                    InlineQueryResultPhoto(
                        id=f"poster-{movie['code']}",
                        photo_url=poster_url,
                        thumbnail_url=poster_url,
                        title=movie["title"],
                        caption=movie_caption(movie, bot_username),
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
                        description=preview_text,
                    )
                )
                continue
            results.append(
                InlineQueryResultArticle(
                    id=f"article-{movie['code']}",
                    title=movie["title"],
                    description=preview_text,
                    input_message_content=InputTextMessageContent(message_text=movie_caption(movie, bot_username), parse_mode=ParseMode.HTML),
                    reply_markup=keyboard,
                )
            )
        await query.answer(results=results, cache_time=0, is_personal=True)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        if update.message.via_bot and update.message.via_bot.id == context.bot.id:
            return
        text = update.message.text.strip()
        self.user_service.track_message(update.effective_user)
        if context.user_data.get("admin_state"):
            return
        if not await self.ensure_subscription(update, context):
            return
        movie = self.movie_service.increment_views(text)
        if not movie:
            await update.message.reply_text("Bunday kino kodi topilmadi. Iltimos, to'g'ri kod yuboring.")
            return
        self.user_service.track_movie_request(update.effective_user, text)
        await send_movie_message(
            update.message,
            movie,
            is_saved=self.user_service.is_movie_saved(update.effective_user.id if update.effective_user else None, text),
        )

    async def on_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        query = update.callback_query
        if not query or not query.data:
            return False
        data = query.data
        message = query.message
        user_id = update.effective_user.id if update.effective_user else None
        self.user_service.register_user(update.effective_user)
        if data == "sub:check":
            if await self.ensure_subscription(update, context):
                await message.reply_text("Obuna tasdiqlandi. Endi botdan foydalanishingiz mumkin.")
            return True
        if not await self.ensure_subscription(update, context):
            return True
        if data == "menu:home":
            await self.start(update, context)
            return True
        if data == "menu:filter":
            await self.show_filter_menu(message)
            return True
        if data == "menu:saved":
            await self.show_saved_movies(message, user_id)
            return True
        if data.startswith("filter_field:"):
            field = data.split(":", maxsplit=1)[1]
            await self.show_filter_options(message, field)
            return True
        if data.startswith("open:"):
            code = data.split(":", maxsplit=1)[1]
            movie = self.movie_service.get_movie(code)
            if not movie:
                await message.reply_text("Kino ma'lumoti topilmadi.")
                return True
            await send_movie_message(message, movie, is_saved=self.user_service.is_movie_saved(user_id, code))
            return True
        if data.startswith("save_toggle:"):
            code = data.split(":", maxsplit=1)[1]
            movie = self.movie_service.get_movie(code)
            if not movie:
                await query.answer("Kino topilmadi.", show_alert=True)
                return True
            is_saved = self.user_service.toggle_saved_movie(user_id, code)
            bot_username = context.bot.username or (await context.bot.get_me()).username
            reply_markup = shared_movie_keyboard(movie, bot_username) if getattr(message, "via_bot", None) else direct_movie_keyboard(movie, is_saved=is_saved)
            try:
                await query.edit_message_reply_markup(reply_markup=reply_markup)
            except Exception:
                pass
            await query.answer("Kino saqlandi." if is_saved else "Kino saqlanganlardan o'chirildi.")
            return True
        return False

    async def show_saved_movies(self, message, user_id: int | None) -> None:
        saved_codes = self.user_service.saved_movie_codes(user_id)
        if not saved_codes:
            await message.reply_text("Saqlangan kinolar hozircha yo'q.")
            return
        await message.reply_text("⭐ <b>Saqlangan kinolar</b>", parse_mode=ParseMode.HTML)
        for code in saved_codes:
            movie = self.movie_service.get_movie(code)
            if movie:
                await send_movie_list_card(message, movie)

    async def show_filter_menu(self, message) -> None:
        await message.reply_text("📂 <b>Inline filter</b>\nKerakli bo'limni tanlang. Variant bosilganda shu chatning o'zida inline natija chiqadi.", parse_mode=ParseMode.HTML, reply_markup=filter_menu_keyboard({}))

    async def show_filter_options(self, message, field: str) -> None:
        labels = {
            "country": "🌍 Davlatlardan keraklisini tanlang",
            "genre": "🎭 Janrlardan keraklisini tanlang",
            "year": "📅 Yillardan keraklisini tanlang",
            "language": "🚩 Tillardan keraklisini tanlang",
        }
        options = self.movie_service.filter_options(field)
        await message.reply_text(labels.get(field, field), reply_markup=filter_options_keyboard(field, options))
