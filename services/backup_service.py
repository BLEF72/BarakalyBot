import os
import shutil
import logging
from datetime import datetime

from config import ADMIN_IDS

log = logging.getLogger(__name__)

DB_PATH    = "foodsave.db"
BACKUP_DIR = "backups"
KEEP_LAST  = 14  # сколько последних бэкапов хранить локально


async def backup_database(bot):
    """Копирует БД в backups/ с датой в имени, чистит старые копии,
    и дублирует свежий бэкап админам в Telegram - на случай,
    если сам сервер станет недоступен."""
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not os.path.exists(DB_PATH):
        log.warning("backup_database: файл %s не найден, пропускаю", DB_PATH)
        return

    stamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
    dest  = os.path.join(BACKUP_DIR, f"foodsave_{stamp}.db")
    shutil.copy2(DB_PATH, dest)
    log.info("Backup создан: %s", dest)

    # ротация - оставляем только последние KEEP_LAST файлов
    backups = sorted(
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith("foodsave_") and f.endswith(".db")
    )
    while len(backups) > KEEP_LAST:
        old = backups.pop(0)
        os.remove(os.path.join(BACKUP_DIR, old))
        log.info("Удалён старый backup: %s", old)

    # дублируем копию вне сервера
    for aid in ADMIN_IDS:
        try:
            with open(dest, "rb") as f:
                await bot.send_document(aid, f, filename=os.path.basename(dest))
        except Exception:
            log.exception("Не удалось отправить backup админу %s", aid)