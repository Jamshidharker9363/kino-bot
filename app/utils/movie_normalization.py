COUNTRY_ALIASES = {
    "aqsh": "AQSH",
    "aqsh.": "AQSH",
    "aqshsh": "AQSH",
    "aqshh": "AQSH",
    "aqsh ": "AQSH",
    "aqsh,": "AQSH",
    "aqsh/usa": "AQSH",
    "usa": "AQSH",
    "us": "AQSH",
    "united states": "AQSH",
    "united states of america": "AQSH",
    "amerika": "AQSH",
    "france": "Fransiya",
    "fransiya": "Fransiya",
    "canada": "Kanada",
    "kanada": "Kanada",
    "china": "Xitoy",
    "xitoy": "Xitoy",
    "japan": "Yaponiya",
    "yaponiya": "Yaponiya",
    "turkey": "Turkiya",
    "turkiya": "Turkiya",
    "russia": "Rossiya",
    "rossiya": "Rossiya",
    "russian federation": "Rossiya",
    "united kingdom": "Buyuk Britaniya",
    "uk": "Buyuk Britaniya",
    "buyuk britaniya": "Buyuk Britaniya",
    "great britain": "Buyuk Britaniya",
    "england": "Buyuk Britaniya",
    "south korea": "Janubiy Koreya",
    "janubiy koreya": "Janubiy Koreya",
    "korea, south": "Janubiy Koreya",
    "uzbekistan": "O'zbekiston",
    "o'zbekiston": "O'zbekiston",
    "ozbekiston": "O'zbekiston",
}

LANGUAGE_ALIASES = {
    "english": "Ingliz",
    "eng": "Ingliz",
    "ingliz": "Ingliz",
    "inglish": "Ingliz",
    "russian": "Rus",
    "rus": "Rus",
    "russkiy": "Rus",
    "uzbek": "O'zbek",
    "uzbekcha": "O'zbek",
    "ozbek": "O'zbek",
    "o'zbek": "O'zbek",
    "o‘zbek": "O'zbek",
    "spanish": "Ispan",
    "ispan": "Ispan",
    "turkish": "Turk",
    "turk": "Turk",
}

GENRE_ALIASES = {
    "action": "Jangari",
    "boyevik": "Jangari",
    "jangari": "Jangari",
    "adventure": "Sarguzasht",
    "sarguzasht": "Sarguzasht",
    "animation": "Animatsiya",
    "animatsiya": "Animatsiya",
    "adult": "Kattalar uchun",
    "biography": "Biografiya",
    "biografiya": "Biografiya",
    "comedy": "Komediya",
    "komediya": "Komediya",
    "crime": "Kriminal",
    "kriminal": "Kriminal",
    "documentary": "Hujjatli",
    "hujjatli": "Hujjatli",
    "drama": "Drama",
    "family": "Oilaviy",
    "oilaviy": "Oilaviy",
    "fantasy": "Fantastika",
    "fantastika": "Fantastika",
    "history": "Tarixiy",
    "tarixiy": "Tarixiy",
    "horror": "Ujas",
    "ujas": "Ujas",
    "music": "Musiqiy",
    "musiqiy": "Musiqiy",
    "musical": "Muzikal",
    "muzikal": "Muzikal",
    "mystery": "Sirli",
    "sirli": "Sirli",
    "romance": "Romantik",
    "romantik": "Romantik",
    "sci-fi": "Fantastika",
    "science fiction": "Fantastika",
    "sport": "Sport",
    "thriller": "Triller",
    "triller": "Triller",
    "war": "Harbiy",
    "harbiy": "Harbiy",
    "western": "Vestern",
    "vestern": "Vestern",
}


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").replace("’", "'").replace("`", "'").split()).strip()


def normalize_key(value: str) -> str:
    return normalize_text(value).lower()


def split_multi_value(value) -> list[str]:
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(split_multi_value(item))
        return items
    text = normalize_text(str(value or ""))
    if not text:
        return []
    text = text.replace("/", ",").replace(";", ",")
    text = text.replace("#", ",")
    return [part.strip(" ,") for part in text.split(",") if part.strip(" ,")]


def dedupe_keep_order(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = normalize_key(value)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def normalize_country_item(value: str) -> str:
    clean = normalize_text(value)
    if not clean:
        return ""
    return COUNTRY_ALIASES.get(normalize_key(clean), clean.title())


def normalize_language_item(value: str) -> str:
    clean = normalize_text(value)
    if not clean:
        return ""
    return LANGUAGE_ALIASES.get(normalize_key(clean), clean.title())


def normalize_genre_item(value: str) -> str:
    clean = normalize_text(value).lstrip("#")
    if not clean:
        return ""
    return GENRE_ALIASES.get(normalize_key(clean), clean.title())


def normalize_country_values(value) -> list[str]:
    return dedupe_keep_order([item for item in (normalize_country_item(part) for part in split_multi_value(value)) if item])


def normalize_language_values(value) -> list[str]:
    return dedupe_keep_order([item for item in (normalize_language_item(part) for part in split_multi_value(value)) if item])


def normalize_genre_values(value) -> list[str]:
    return dedupe_keep_order([item for item in (normalize_genre_item(part) for part in split_multi_value(value)) if item])

