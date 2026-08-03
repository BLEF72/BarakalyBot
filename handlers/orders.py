import logging
from telegram import Update
from telegram.ext import ContextTypes

from texts import t
from utils.helpers import get_lang
from services import order_service

log = logging.getLogger(__name__)



async def done_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    lang = get_lang(uid)
    code = query.data.replace("done_", "")

    result = order_service.mark_done(code, actor_id=uid)
    await query.edit_message_reply_markup(reply_markup=None)

    if result == "ok":
        await _notify_buyer(ctx, code)
        await ctx.bot.send_message(
            uid, t("order_marked_done", lang, code=code, username="—")
        )
    elif result == "already":
        await ctx.bot.send_message(uid, t("order_already_done", lang))
    elif result == "cancelled":
        await ctx.bot.send_message(uid, t("order_was_cancelled", lang))
    elif result == "expired":
        await ctx.bot.send_message(uid, t("order_expired_no_show", lang))
    elif result == "not_yours":
        await ctx.bot.send_message(uid, t("order_not_yours", lang))
    else:
        await ctx.bot.send_message(uid, t("order_not_found", lang))


async def mark_done_by_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    code = update.message.text.strip().upper()

    result = order_service.mark_done(code, actor_id=uid)

    if result == "ok":
        await _notify_buyer(ctx, code)
        await update.message.reply_text(
            t("order_marked_done", lang, code=code, username="—"),
            parse_mode="Markdown",
        )
    elif result == "already":
        await update.message.reply_text(t("order_already_done", lang))
    elif result == "cancelled":
        await update.message.reply_text(t("order_was_cancelled", lang))
    elif result == "expired":
        await ctx.bot.send_message(uid, t("order_expired_no_show", lang))
    elif result == "not_yours":
        await ctx.bot.send_message(uid, t("order_not_yours", lang))
    else:
        await update.message.reply_text(t("order_not_found", lang))

    ctx.user_data.pop("action", None)
    
async def review_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_lang(uid)

    parts      = query.data.replace("review_", "").rsplit("_", 1)
    order_code = parts[0]
    rating     = int(parts[1])

    from services import review_service
    from database import Session, Order, Package

    with Session() as s:
        order = s.query(Order).filter_by(code=order_code).first()
        if not order:
            await query.answer(t("order_not_found", lang), show_alert=True)
            return
        restaurant_id = s.query(Package).filter_by(
            id=order.package_id
        ).first().restaurant_id

    added = review_service.add_review(uid, restaurant_id, order_code, rating)

    if added:
        stars = "⭐" * rating
        await query.edit_message_text(
            f"{stars}\n\n{t('review_thanks', lang)}",
            parse_mode="Markdown",
        )
    else:
        await query.answer(t("review_already", lang), show_alert=True)
    
async def _notify_buyer(ctx, code: str):
    log.debug("_notify_buyer вызван, code=%s", code)
    from services.order_service import get_buyer_id
    from services import review_service
    from database import Session, Order, Package, Restaurant

    buyer_id = get_buyer_id(code)
    if not buyer_id:
        return

    try:
        lang = get_lang(buyer_id)
        await ctx.bot.send_message(
            buyer_id,
            t("order_done_buyer", lang, code=code),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    # Получаем данные заведения
    with Session() as s:
        order = s.query(Order).filter_by(code=code).first()
        if not order:
            return
        pkg  = s.query(Package).filter_by(id=order.package_id).first()
        rest = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first() if pkg else None
        if not rest:
            return
        rest_name = rest.name

    # Отправляем запрос оценки через job_queue
    async def send_review(context):
        log.debug("send_review вызван, code=%s, buyer_id=%s", code, buyer_id)
        if review_service.already_reviewed(code):
            log.debug("уже оценил, code=%s", code)
            return
        try:
            from keyboards.inline import review_keyboard
            user_lang = get_lang(buyer_id)
            await context.bot.send_message(
                buyer_id,
                t("review_request", user_lang, rest=rest_name),
                parse_mode="Markdown",
                reply_markup=review_keyboard(code),
            )
        except Exception:
            pass

    ctx.application.job_queue.run_once(
        send_review,
        when=10,  # 10 секунд после выдачи заказа
    )