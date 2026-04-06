def movie_caption(movie: dict, bot_username: str | None = None) -> str:
    genres = " ".join(f"#{genre}" for genre in movie.get("genres", []))
    bot_label = f"@{bot_username}" if bot_username else "Bot"
    lines = [
        f"🎬 <b>{movie['title']}</b>",
        "➖ ➖ ➖ ➖ ➖ ➖",
        "",
        f"🌐 <b>Davlat:</b> {movie.get('country') or 'Kiritilmagan'}",
        f"🚩 <b>Til:</b> {movie.get('language') or 'Kiritilmagan'}",
        f"🎭 <b>Janr:</b> {genres or 'Kiritilmagan'}",
    ]
    quality = (movie.get("quality") or "").strip()
    if quality:
        lines.append(f"📀 <b>Sifat:</b> {quality}")
    lines.append(f"📅 <b>Yil:</b> {movie.get('year') or 'Kiritilmagan'}")
    lines.extend(
        [
            "",
            f"🔢 <b>Kod:</b> {movie['code']}",
            f"👁 <b>Ko'rishlar:</b> {movie.get('views', 0)}",
        ]
    )
    rating = (movie.get("rating") or "").strip()
    if rating:
        lines.extend(["", f"⭐ <b>Reyting:</b> {rating}{_votes_suffix(movie)}"])
    description = (movie.get("description") or "").strip()
    if description:
        lines.extend(["", description])
    lines.extend(["", f"🤖 <b>Bot:</b> {bot_label} | Filmlarni do'stlaringizga ham ulashing"])
    return "\n".join(lines)


def movie_list_caption(movie: dict) -> str:
    quality = movie.get("quality") or "-"
    language = movie.get("language") or "Kiritilmagan"
    return (
        f"<b>{movie['title']}</b>\n"
        f"<code>{movie['code']}</code> | {quality} | 👁 {movie.get('views', 0)}\n"
        f"🚩 {language}"
    )


def movie_short_line(movie: dict) -> str:
    return f"• <b>{movie['title']}</b> | Kod: <code>{movie['code']}</code>"


def _votes_suffix(movie: dict) -> str:
    votes = str(movie.get("imdb_votes", "") or "").strip()
    if not votes:
        return ""
    return f" ({votes} ovoz)"
