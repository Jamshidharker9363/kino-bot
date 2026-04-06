from telegram import InputFile
from telegram.constants import ParseMode

from app.config import BASE_DIR
from app.keyboards.user import direct_movie_keyboard, movie_open_keyboard
from app.utils.formatters import movie_caption, movie_list_caption


async def send_movie_message(message, movie: dict, is_saved: bool = False) -> None:
    await send_movie_to_chat(message.get_bot(), message.chat_id, movie, reply_to_message=message, is_saved=is_saved)


async def send_movie_to_chat(bot, chat_id: int, movie: dict, reply_to_message=None, is_saved: bool = False) -> None:
    direct_markup = direct_movie_keyboard(movie, is_saved=is_saved)
    bot_username = bot.username or (await bot.get_me()).username
    caption = movie_caption(movie, bot_username)
    media_type = movie.get("media_type")
    media_file_id = movie.get("media_file_id")

    try:
        if media_type == "video" and media_file_id:
            await bot.send_video(chat_id=chat_id, video=media_file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
            return
        if media_type == "document" and media_file_id:
            await bot.send_document(chat_id=chat_id, document=media_file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
            return
        if media_type == "photo" and media_file_id:
            await bot.send_photo(chat_id=chat_id, photo=media_file_id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
            return
    except Exception:
        pass

    video_path = BASE_DIR / movie.get("video", "")
    poster_path = BASE_DIR / movie.get("poster", "")
    poster_url = movie.get("poster_url")

    try:
        if movie.get("video") and video_path.exists():
            with video_path.open("rb") as file:
                await bot.send_video(chat_id=chat_id, video=InputFile(file, filename=video_path.name), caption=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
            return
        if movie.get("poster") and poster_path.exists():
            with poster_path.open("rb") as file:
                await bot.send_photo(chat_id=chat_id, photo=InputFile(file, filename=poster_path.name), caption=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
            return
        if poster_url:
            await bot.send_photo(chat_id=chat_id, photo=poster_url, caption=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
            return
        await bot.send_message(chat_id=chat_id, text=caption, parse_mode=ParseMode.HTML, reply_markup=direct_markup)
    except Exception as error:
        if reply_to_message:
            await reply_to_message.reply_text(f"Kino yuborishda xato chiqdi: {error}")
        else:
            raise


async def send_movie_list_card(message, movie: dict) -> None:
    caption = movie_list_caption(movie)
    bot = message.get_bot()
    bot_username = bot.username or (await bot.get_me()).username
    reply_markup = movie_open_keyboard(movie, bot_username)
    poster_path = BASE_DIR / movie.get("poster", "")
    poster_url = movie.get("poster_url")

    if movie.get("poster") and poster_path.exists():
        with poster_path.open("rb") as file:
            await message.reply_photo(photo=InputFile(file, filename=poster_path.name), caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        return
    if poster_url:
        await message.reply_photo(photo=poster_url, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        return
    await message.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
