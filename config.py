import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Admin Telegram ID (buyurtmalar shu yerga keladi)
