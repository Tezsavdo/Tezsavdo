import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")

# Bir nechta admin qo'llab-quvvatlanadi: ADMIN_IDS="123456789,987654321"
# Eski ADMIN_ID (bitta qiymat) ham hali ishlaydi, orqaga moslik uchun.
_admin_ids_raw = os.getenv("ADMIN_IDS", "") or os.getenv("ADMIN_ID", "0")
ADMIN_IDS = {
    int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().lstrip("-").isdigit()
}
# Buyurtma xabari yuboriladigan asosiy admin (birinchi ID)
ADMIN_ID = next(iter(ADMIN_IDS), 0)
