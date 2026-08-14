# Do'kon uchun Dastavka Bot (Telegram)

Aiogram 3 asosida yozilgan to'liq dastavka boti: katalog → savat → buyurtma → to'lov usuli → admin'ga xabar.

## Imkoniyatlar
- 🛍 Kategoriyalar va mahsulotlar katalogi (SQLite bazada saqlanadi)
- 🛒 Savat (mahsulot qo'shish, umumiy summa, tozalash)
- 📋 Buyurtma jarayoni: ism → telefon (tugma orqali ham) → manzil → to'lov usuli (naqd/karta) → tasdiqlash
- 📩 Tasdiqlangan buyurtma to'liq ma'lumot bilan **admin'ga** xabar sifatida yuboriladi
- Baza avtomatik 3 ta kategoriya va 5 ta namuna mahsulot bilan to'ldiriladi (o'zingiznikiga almashtirasiz)

## O'rnatish

1. Kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

2. `.env.example` faylini `.env` deb nomlang va to'ldiring:
```
BOT_TOKEN=BotFather'dan olingan token
ADMIN_ID=sizning Telegram ID raqamingiz (masalan @userinfobot orqali bilib olasiz)
```

3. Botni ishga tushiring:
```bash
python main.py
```

## Mahsulot qo'shish

Hozircha mahsulotlar `database.py` ichidagi `seed_demo_data()` funksiyasida namuna sifatida beriladi.
O'z mahsulotlaringizni qo'shish uchun ikkita yo'l bor:

**A) Kod orqali** — `database.py` dagi `add_product(category_id, name, price, description)` funksiyasidan foydalaning.

**B) To'g'ridan-to'g'ri bazaga** — `shop.db` faylini DB Browser for SQLite kabi dastur bilan ochib, `products` va `categories` jadvallariga qo'shing.

Agar xohlasangiz, keyingi bosqichda mahsulot qo'shish uchun **admin-panel buyruqlari** (masalan `/add_product`) ni ham botga qo'shib beraman.

## Fayllar tuzilishi
```
delivery_bot/
├── main.py            # Bot handlerlar va checkout FSM
├── database.py         # SQLite: kategoriyalar, mahsulotlar
├── keyboards.py        # Inline/reply klaviaturalar
├── config.py            # Token va admin ID
├── requirements.txt
└── .env.example
```

## Keyingi qadamlar (xohlasangiz qo'shib beraman)
- Buyurtmalar tarixini bazada saqlash
- Admin uchun mahsulot qo'shish/o'chirish buyruqlari
- To'lov: Payme/Click integratsiyasi (haqiqiy onlayn to'lov)
- Yetkazib berish narxini masofaga qarab hisoblash
- Buyurtma statusini kuzatish (qabul qilindi → tayyorlanmoqda → yo'lda → yetkazildi)
