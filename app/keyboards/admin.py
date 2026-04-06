from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def admin_panel_keyboard(is_super_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("➕ Kino qo'shish", callback_data="admin:add"),
            InlineKeyboardButton("📋 Kinolar", callback_data="admin:list:0"),
        ],
        [
            InlineKeyboardButton("👥 Userlar", callback_data="admin:users"),
            InlineKeyboardButton("📈 Kino info", callback_data="admin:movie_stats"),
        ],
        [
            InlineKeyboardButton("📣 Xabar yuborish", callback_data="admin:broadcast"),
            InlineKeyboardButton("🔐 Obuna", callback_data="admin:subs"),
        ],
    ]
    if is_super_admin:
        rows.append([InlineKeyboardButton("🛡 Adminlar", callback_data="admin:admins")])
    rows.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="admin:cancel")])
    return InlineKeyboardMarkup(rows)


def admin_movies_keyboard(movies: list[dict], page: int = 0, page_size: int = 15) -> InlineKeyboardMarkup:
    sorted_movies = sorted(movies, key=lambda item: item["title"].lower())
    start = max(page, 0) * page_size
    end = start + page_size
    rows = [
        [InlineKeyboardButton(f"{movie['title']} ({movie['code']})", callback_data=f"admin:manage:{movie['code']}")]
        for movie in sorted_movies[start:end]
    ]
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin:list:{page - 1}"))
    if end < len(sorted_movies):
        nav_row.append(InlineKeyboardButton("➡️ Keyingi", callback_data=f"admin:list:{page + 1}"))
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:back")])
    return InlineKeyboardMarkup(rows)


def admin_movie_manage_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👁 Ko'rish", callback_data=f"admin:view:{code}"),
                InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"admin:edit:{code}"),
            ],
            [InlineKeyboardButton("📣 Reklama yuborish", callback_data=f"admin:announce:{code}")],
            [InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin:delete:{code}")],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:list:0")],
        ]
    )


def admin_edit_fields_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Kod", callback_data=f"admin:editfield:{code}:code"),
                InlineKeyboardButton("Nomi", callback_data=f"admin:editfield:{code}:title"),
            ],
            [
                InlineKeyboardButton("Davlat", callback_data=f"admin:editfield:{code}:country"),
                InlineKeyboardButton("Til", callback_data=f"admin:editfield:{code}:language"),
            ],
            [
                InlineKeyboardButton("Janr", callback_data=f"admin:editfield:{code}:genres"),
                InlineKeyboardButton("Sifat", callback_data=f"admin:editfield:{code}:quality"),
            ],
            [
                InlineKeyboardButton("Yil", callback_data=f"admin:editfield:{code}:year"),
                InlineKeyboardButton("Reyting", callback_data=f"admin:editfield:{code}:rating"),
            ],
            [
                InlineKeyboardButton("Description", callback_data=f"admin:editfield:{code}:description"),
                InlineKeyboardButton("Poster URL", callback_data=f"admin:editfield:{code}:poster_url"),
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data=f"admin:manage:{code}")],
        ]
    )


def admin_delete_confirm_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"admin:confirm_delete:{code}"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"admin:manage:{code}"),
        ]]
    )


def admin_subscriptions_keyboard(enabled: bool, channels: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("➕ Kanal qo'shish", callback_data="admin:subs_add"),
            InlineKeyboardButton("🎯 Forward orqali", callback_data="admin:subs_add_auto"),
        ],
        [
            InlineKeyboardButton("➖ Kanal o'chirish", callback_data="admin:subs_remove"),
            InlineKeyboardButton("⏸ O'chirish" if enabled else "▶️ Yoqish", callback_data="admin:subs_toggle"),
        ],
    ]
    for channel in channels[:10]:
        rows.append([InlineKeyboardButton(channel.get("title", str(channel["chat_id"])), url=channel.get("url", "https://t.me"))])
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:back")])
    return InlineKeyboardMarkup(rows)


def admin_subscriptions_remove_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(channel.get("title", str(channel["chat_id"])), callback_data=f"admin:subs_delete:{channel['chat_id']}")]
        for channel in channels[:20]
    ]
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:subs")])
    return InlineKeyboardMarkup(rows)


def admin_users_export_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 PDF", callback_data="admin:users_export:pdf"),
                InlineKeyboardButton("📊 Excel", callback_data="admin:users_export:xlsx"),
            ],
            [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:back")],
        ]
    )


def admin_list_keyboard(admin_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"Admin {admin_id}", callback_data=f"admin:remove_admin:{admin_id}")] for admin_id in admin_ids]
    rows.append([InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin:add_admin")])
    rows.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin:back")])
    return InlineKeyboardMarkup(rows)


def admin_language_keyboard(selected_languages: list[str]) -> InlineKeyboardMarkup:
    options = ["O'zbek", "Rus", "Ingliz"]
    rows = []
    for option in options:
        mark = "✅ " if option in selected_languages else ""
        rows.append([InlineKeyboardButton(f"{mark}{option}", callback_data=f"admin:lang_toggle:{option}")])
    rows.append([InlineKeyboardButton("➡️ Tasdiqlash", callback_data="admin:lang_done")])
    return InlineKeyboardMarkup(rows)
