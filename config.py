import os
import logging

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "Telegram Bot Token")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")]
CHANNEL_ID = os.getenv("CHANNEL_ID", "@BarakalyGroup")  

# ── Бизнес-логика ────────────────────────────────────────────────────────────
RESERVE_MINUTES = 60 # сколько минут держится бронь
CLEANUP_HOUR    = 3     # час ночной очистки (UTC)

# ── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
