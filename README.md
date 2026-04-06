# Kino Bot

Bu bot kino kodi, qidiruv, top filmlar, filter va admin panel bilan ishlaydi.

## O'rnatish

```powershell
pip install -r requirements.txt
```

`.env.example` dan `.env` yarating:

```env
BOT_TOKEN=123456:ABC_TOKEN
ADMIN_IDS=123456789
MOVIES_CHAT_ID=-1001234567890
OMDB_API_KEY=your_omdb_api_key
```

`ADMIN_IDS` ichiga admin Telegram user id yoziladi. Bir nechta admin bo'lsa vergul bilan ajrating.
`MOVIES_CHAT_ID` ichiga kinolar saqlanadigan kanal yoki guruh id yoziladi.
`OMDB_API_KEY` avtomatik metadata olish uchun kerak.

## Ishga tushirish

```powershell
python bot.py
```

## Loyiha tuzilmasi

- `app/config.py` : umumiy sozlamalar
- `app/data/repository.py` : `movies.json` bilan ishlash
- `app/services/movie_service.py` : top, qidiruv, filter logikasi
- `app/keyboards/user.py` : foydalanuvchi tugmalari
- `app/keyboards/admin.py` : admin panel tugmalari
- `app/handlers/user.py` : foydalanuvchi komandalar va callbacklar
- `app/handlers/admin.py` : admin panel va kino qo'shish oqimi
- `app/handlers/common.py` : kino va aktyor kartochkalarini yuborish
- `app/main.py` : botni yig'ish va handlerlarni ulash

## Admin panel

`/admin` komandasi admin panelni ochadi.

Hozircha admin panel imkoniyatlari:

- yangi kino qo'shish
- barcha kinolar ro'yxatini ko'rish
- kinoni ko'rish, tahrirlash va o'chirish
- foydalanuvchilar statistikasi
- kinolar statistikasi
- userlarga ommaviy xabar yuborish
- majburiy obuna kanallarini boshqarish
- admin amalini bekor qilish

Admin yangi kino qo'shganda `year`, `country`, `language`, `genre` avtomatik filterga qo'shiladi. Chunki filter variantlari doim `data/movies.json` ichidagi real ma'lumotdan yig'iladi.

Foydalanuvchilar ma'lumotlari `data/users.json` ichida saqlanadi.
Majburiy obuna sozlamalari `data/subscriptions.json` ichida saqlanadi.

## Avtomatik metadata

Admin kino nomini yuborgandan keyin bot OMDb orqali:

- davlat
- til
- janr
- yil
- reyting
- aktyorlar
- poster
- treyler qidiruv linki

ma'lumotlarini topishga urinadi va admindan tasdiq so'raydi.

## Kanal yoki guruh orqali ishlash

Botni kino saqlanadigan kanal yoki guruhga admin qilib qo'shing.

Admin yangi kino qo'shganda:

- avval media yuboradi
- keyin kod, nom, davlat, til, janr, yil va boshqa ma'lumotlarni kiritadi
- bot kinoni `MOVIES_CHAT_ID` dagi kanal/guruhga joylaydi
- so'ng `source_chat_id` va `source_message_id` ni saqlab qo'yadi

Foydalanuvchi kino kodini yuborganda bot o'sha kanal/guruhdagi kinoni userga yuboradi.
