import logging
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler,)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from database import init_db

from utils.constants import LANG_SELECT, A_NAME, A_ADDRESS, A_DISTRICT,A_OWNER, A_PHOTO, A_LOCATION, O_NAME, O_PHOTO,O_PRICE, O_QTY, O_TIME, O_EDIT_PRICE,O_EDIT_QTY, O_TEMPLATE_QTY, O_UPDATE_PHOTO,O_EDIT_TIME, O_SELECT_REST

from handlers.start  import start, lang_selected, cancel
from handlers.buyer  import show_districts, district_selected, reserve_callback, my_orders, help_cmd, handle_text, handle_photo, favorite_callback, show_favorites, subscribe_rest_callback, subscribe_dist_callback, my_subscriptions,cancel_order_callback,rebook_callback,confirm_cancel_callback, keep_order_callback, show_top
from handlers.owner import o_update_rest_photo, owner_panel, owner_callback, o_name, o_photo, o_price, o_qty, o_time, o_edit_price, o_edit_qty, o_template_qty,o_edit_time, handle_pickup_time
from handlers.admin import admin_panel, admin_callback, a_name, a_address,  a_district, a_owner, a_photo, a_location, skip_rest_photo_callback, skip_rest_location_callback
from handlers.orders import done_callback, review_callback
from handlers.support import support_cancel_callback, support_reply_callback
from services.order_service import expire_old_reservations, send_pickup_reminders, check_unblocked_users
from services.package_service import nightly_cleanup, auto_open_restaurants


from services.order_service   import expire_old_reservations
from services.package_service import nightly_cleanup

log = logging.getLogger(__name__)


async def send_weekly_reports(bot):
    """Каждый понедельник в 09:00 — отправляем отчёт владельцам"""
    from services import report_service
    from services.review_service import get_rating
    from utils.helpers import get_lang
    from texts import t
    from config import ADMIN_IDS

    rests = report_service.get_all_restaurants()

    for rest in rests:
        report = report_service.get_restaurant_report(rest["id"])
        if not report:
            continue

        # Отправляем владельцу
        owner_id = rest["owner_id"]
        if owner_id:
            try:
                lang = get_lang(owner_id)
                text = t("weekly_report", lang,
                         rest          = report["rest_name"],
                         orders        = report["orders"],
                         done          = report["done"],
                         cancelled     = report["cancelled"],
                         revenue       = report["revenue"],
                         rating        = report["rating"],
                         total         = report["total"],
                         total_revenue = report["total_revenue"])
                await bot.send_message(owner_id, text, parse_mode="Markdown")
            except Exception:
                pass

    # Отправляем админу сводку по всем заведениям
    for admin_id in ADMIN_IDS:
        try:
            lang  = get_lang(admin_id)
            total_text = "📊 *Еженедельная сводка по всем заведениям:*\n\n" if lang == "ru" else "📊 *Barcha muassasalar bo'yicha haftalik xulosа:*\n\n"
            for rest in rests:
                report = report_service.get_restaurant_report(rest["id"])
                total_text += (
                    f"🏪 *{report['rest_name']}*\n"
                    f"  📦 {report['orders']} заказов | ✅ {report['done']} выдано | 💰 {report['revenue']:,} сум\n\n"
                )
            await bot.send_message(admin_id, total_text, parse_mode="Markdown")
        except Exception:
            pass
def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    # ── /start — выбор языка ─────────────────────────────────────────────────
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_SELECT: [CallbackQueryHandler(lang_selected, pattern="^lang_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ── Админ: добавление заведения ──────────────────────────────────────────
    rest_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback, pattern="^admin_add_rest$")],
        states={
            A_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, a_name)],
            A_ADDRESS:  [MessageHandler(filters.TEXT & ~filters.COMMAND, a_address)],
            A_LOCATION: [
                MessageHandler(filters.LOCATION, a_location),
                CallbackQueryHandler(skip_rest_location_callback, pattern="^skip_rest_location$"),
            ],
            A_DISTRICT: [CallbackQueryHandler(a_district, pattern="^adistrict_")],
            A_OWNER:    [MessageHandler(filters.TEXT & ~filters.COMMAND, a_owner)],
            A_PHOTO:    [
                MessageHandler(filters.PHOTO, a_photo),
                CallbackQueryHandler(skip_rest_photo_callback, pattern="^skip_rest_photo$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    pkg_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(owner_callback, pattern="^owner_add_pkg_")],
        states={
            O_NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, o_name)],
            O_PHOTO: [
                MessageHandler(filters.PHOTO, o_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, o_photo),
            ],
            O_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, o_price)],
            O_QTY:   [MessageHandler(filters.TEXT & ~filters.COMMAND, o_qty)],
            O_TIME:  [
                MessageHandler(filters.TEXT & ~filters.COMMAND, o_time),
                CallbackQueryHandler(owner_callback, pattern="^pickuptime_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
    )
    
    edit_pkg_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(owner_callback, pattern="^editpkg_price_"),
            CallbackQueryHandler(owner_callback, pattern="^editpkg_qty_"),
            CallbackQueryHandler(owner_callback, pattern="^editpkg_time_"),
        ],
        states={
            O_EDIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, o_edit_price)],
            O_EDIT_QTY:   [MessageHandler(filters.TEXT & ~filters.COMMAND, o_edit_qty)],
            O_EDIT_TIME:  [
                MessageHandler(filters.TEXT & ~filters.COMMAND, o_edit_time),
                CallbackQueryHandler(owner_callback, pattern="^pickuptime_edit_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
    )
    template_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(owner_callback, pattern="^usetpl_")],
        states={
            O_TEMPLATE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, o_template_qty)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
    )
    
    update_photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(owner_callback, pattern="^owner_update_photo_")],
        states={
            O_UPDATE_PHOTO: [MessageHandler(filters.PHOTO, o_update_rest_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
        per_chat=True,
    )

    # ── Регистрируем хендлеры ────────────────────────────────────────────────
    app.add_handler(start_conv)
    app.add_handler(rest_conv)
    app.add_handler(edit_pkg_conv)
    app.add_handler(template_conv)
    app.add_handler(pkg_conv)
    app.add_handler(update_photo_conv)
    

    app.add_handler(CommandHandler("mypanel", owner_panel))
    app.add_handler(CommandHandler("admin",   admin_panel))
    app.add_handler(CommandHandler("cancel",  cancel))
    app.add_handler(CallbackQueryHandler(admin_callback,    pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^skip_pkg_photo$"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^editpkg_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^owner_"))
    app.add_handler(CallbackQueryHandler(district_selected, pattern="^district_"))
    app.add_handler(CallbackQueryHandler(handle_pickup_time, pattern="^pickuptime_(?!edit_)"))
    app.add_handler(CallbackQueryHandler(reserve_callback,  pattern="^reserve_"))
    app.add_handler(CallbackQueryHandler(confirm_cancel_callback, pattern="^confirm_cancel_"))
    app.add_handler(CallbackQueryHandler(keep_order_callback,     pattern="^keep_order_"))
    app.add_handler(CallbackQueryHandler(done_callback,     pattern="^done_"))
    app.add_handler(CallbackQueryHandler(favorite_callback, pattern="^fav_"))
    app.add_handler(CallbackQueryHandler(subscribe_rest_callback, pattern="^sub_rest_"))
    app.add_handler(CallbackQueryHandler(subscribe_dist_callback, pattern="^sub_dist_"))
    app.add_handler(CallbackQueryHandler(cancel_order_callback, pattern="^cancel_order_"))
    app.add_handler(CallbackQueryHandler(review_callback, pattern="^review_"))
    app.add_handler(CallbackQueryHandler(rebook_callback, pattern="^rebook_"))
    app.add_handler(CallbackQueryHandler(lambda u, c: show_favorites(u, c), pattern="^show_favorites$"))
    app.add_handler(CallbackQueryHandler(support_cancel_callback, pattern="^support_cancel$"))
    app.add_handler(CallbackQueryHandler(support_reply_callback,  pattern="^support_reply_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^savetpl_"))
   
    

    # Фото обрабатывается отдельно (для добавления пакета)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # ── Планировщик ──────────────────────────────────────────────────────────
    async def on_startup(application: Application): 
        scheduler = AsyncIOScheduler()
        scheduler.add_job(expire_old_reservations, "interval", minutes=5,
                          args=[application.bot])
        scheduler.add_job(send_pickup_reminders, "interval", minutes=5,
                          args=[application.bot])
        scheduler.add_job(nightly_cleanup, "cron", hour=3, minute=0,
                          args=[application.bot])
        scheduler.add_job(send_weekly_reports, "cron",
                          day_of_week="mon", hour=9, minute=0,
                          args=[application.bot])
        scheduler.add_job(check_unblocked_users, "interval", hours=1,
                  args=[application.bot])
        scheduler.add_job(auto_open_restaurants, "cron", hour=6, minute=0,
                  args=[application.bot])
        scheduler.start()
        log.info("✅ Scheduler запущен")

    app.post_init = on_startup
    return app


def main():
    init_db()
    app = build_app()
    log.info("Barakly запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()