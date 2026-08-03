import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = [int(x) for x in os.environ["ADMIN_IDS"].split(",") if x.strip()]
if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS must be set in .env")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@BarakalyGroup")

# ── Бизнес-логика ────────────────────────────────────────────────────────────
RESERVE_MINUTES = 60 # сколько минут держится бронь
CLEANUP_HOUR    = 3     # час ночной очистки (UTC)
COMMISSION_RATE  = 0.25  # доля платформы с каждой продажи (25%)

# ── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)