from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def subscription_keyboard(channels: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for channel in channels:
        url = channel.get("url")
        if url:
            rows.append([InlineKeyboardButton(f"🎬 {channel.get('title', 'Kanal')}", url=url)])
    rows.append([InlineKeyboardButton("✅ Tekshirish", callback_data="sub:check")])
    return InlineKeyboardMarkup(rows)
