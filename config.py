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
NO_SHOW_WINDOW_DAYS       = 30  # окно, за которое считаем неявки
NO_SHOW_CAP_THRESHOLD     = 2   # с этого количества - лимит 1 бронь одновременно
NO_SHOW_BLOCK_THRESHOLD   = 3   # с этого - блокировка на NO_SHOW_BLOCK_DAYS дней
NO_SHOW_BLOCK_DAYS        = 7
NO_SHOW_REVIEW_THRESHOLD  = 5   # с этого - блокировка подольше + алерт админу
NO_SHOW_REVIEW_BLOCK_DAYS = 30

# ── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)