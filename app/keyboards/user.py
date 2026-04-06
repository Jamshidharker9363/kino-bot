from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def _save_button(movie: dict, is_saved: bool = False) -> InlineKeyboardButton:
    label = "🗑 O'chirish" if is_saved else "⭐ Saqlash"
    return InlineKeyboardButton(label, callback_data=f"save_toggle:{movie['code']}")


def shared_movie_keyboard(movie: dict, bot_username: str | None = None, is_saved: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("🎬 Ko'rish", url=f"https://t.me/{bot_username}?start=code_{movie['code']}") if bot_username else InlineKeyboardButton("🎬 Ko'rish", callback_data=f"open:{movie['code']}"),
            InlineKeyboardButton("↪️ Ulashish", switch_inline_query=str(movie["code"])),
        ],
        [InlineKeyboardButton("🔎 Qidirish", switch_inline_query_current_chat="")],
    ]
    return InlineKeyboardMarkup(rows)


def direct_movie_keyboard(movie: dict, is_saved: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("↪️ Ulashish", switch_inline_query=str(movie["code"])),
                _save_button(movie, is_saved),
            ],
            [InlineKeyboardButton("🔎 Qidirish", switch_inline_query_current_chat="")],
        ]
    )


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📊 Top Filmlar", switch_inline_query_current_chat="top_films"),
                InlineKeyboardButton("📂 Filter", callback_data="menu:filter"),
            ],
            [
                InlineKeyboardButton("⭐ Saqlangan", switch_inline_query_current_chat="saved_films"),
                InlineKeyboardButton("🔎 Film qidirish", switch_inline_query_current_chat=""),
            ],
        ]
    )


def filter_menu_keyboard(selected_filters: dict[str, str]) -> InlineKeyboardMarkup:
    country_suffix = f" • {selected_filters.get('country')}" if selected_filters.get("country") else ""
    genre_suffix = f" • {selected_filters.get('genre')}" if selected_filters.get("genre") else ""
    year_suffix = f" • {selected_filters.get('year')}" if selected_filters.get("year") else ""
    language_suffix = f" • {selected_filters.get('language')}" if selected_filters.get("language") else ""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"🌍 Davlat{country_suffix}", callback_data="filter_field:country"),
                InlineKeyboardButton(f"🎭 Janr{genre_suffix}", callback_data="filter_field:genre"),
            ],
            [
                InlineKeyboardButton(f"📅 Yil{year_suffix}", callback_data="filter_field:year"),
                InlineKeyboardButton(f"🚩 Til{language_suffix}", callback_data="filter_field:language"),
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:home")],
        ]
    )


def filter_options_keyboard(field: str, options: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for index in range(0, len(options), 3):
        chunk = options[index:index + 3]
        rows.append([InlineKeyboardButton(option, switch_inline_query_current_chat=f"{field}:{option}") for option in chunk])
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="menu:filter")])
    return InlineKeyboardMarkup(rows)


def movie_open_keyboard(movie: dict, bot_username: str | None = None) -> InlineKeyboardMarkup:
    if bot_username:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Ko'rish", url=f"https://t.me/{bot_username}?start=code_{movie['code']}")]])
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Ko'rish", callback_data=f"open:{movie['code']}")]])
