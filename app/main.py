from telegram.ext import Application, CallbackQueryHandler, CommandHandler, InlineQueryHandler, MessageHandler, filters # type: ignore

from app.config import LOGGER, get_bot_token
from app.data.repository import MovieRepository
from app.data.admin_repository import AdminRepository
from app.data.subscription_repository import SubscriptionRepository
from app.data.user_repository import UserRepository
from app.handlers.admin import AdminHandler
from app.handlers.user import UserHandler
from app.services.admin_service import AdminService
from app.services.movie_service import MovieService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService


def build_application() -> Application:
    movie_repository = MovieRepository()
    admin_repository = AdminRepository()
    user_repository = UserRepository()
    subscription_repository = SubscriptionRepository()
    movie_service = MovieService(movie_repository)
    user_service = UserService(user_repository)
    subscription_service = SubscriptionService(subscription_repository)
    admin_service = AdminService(admin_repository)
    user_handler = UserHandler(movie_service, user_service, subscription_service)
    admin_handler = AdminHandler(movie_service, user_service, subscription_service, admin_service)

    app = Application.builder().token(get_bot_token()).build()

    async def callback_router(update, context):
        query = update.callback_query
        if not query:
            return
        await query.answer()
        handled = await admin_handler.on_button(update, context)
        if not handled:
            await user_handler.on_button(update, context)

    async def message_router(update, context):
        handled = await admin_handler.handle_message(update, context)
        if not handled:
            await user_handler.handle_message(update, context)

    app.add_handler(CommandHandler("start", user_handler.start))
    app.add_handler(CommandHandler("help", user_handler.help))
    app.add_handler(CommandHandler("myid", user_handler.my_id))
    app.add_handler(CommandHandler("chatid", user_handler.chat_id))
    app.add_handler(CommandHandler("admin", admin_handler.open_panel))
    app.add_handler(CommandHandler("subscriptions", admin_handler.subscriptions_command))
    app.add_handler(CommandHandler("new_message", admin_handler.new_message_command))
    app.add_handler(CommandHandler("info_film", admin_handler.info_film_command))
    app.add_handler(CommandHandler("films", admin_handler.films_command))
    app.add_handler(CommandHandler("users_info", admin_handler.users_info_command))
    app.add_handler(CommandHandler("add_new_film", admin_handler.add_new_film_command))
    app.add_handler(InlineQueryHandler(user_handler.inline_query))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(
        MessageHandler(
            (filters.ALL & ~filters.COMMAND),
            message_router,
        )
    )
    return app


def main() -> None:
    app = build_application()
    LOGGER.info("Bot ishga tushdi.")
    app.run_polling()
