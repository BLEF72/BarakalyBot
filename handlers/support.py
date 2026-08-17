from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import ContextTypes

from texts import t
from utils.helpers import get_lang
from config import ADMIN_IDS
from keyboards.main import main_keyboard


async def support_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Пользователь нажал кнопку Поддержка"""
    uid  = update.effective_user.id
    lang = get_lang(uid)

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("support_cancel", lang), callback_data="support_cancel")
    ]])

    await update.message.reply_text(
        t("support_ask", lang),
        reply_markup=kb
    )
    ctx.user_data["action"] = "support"


async def support_cancel_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_lang(uid)
    ctx.user_data.pop("action", None)
    await query.edit_message_text(t("cancelled", lang))


async def handle_support_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Сохраняет тикет в базу и пересылает админам.
    Вызывается из handle_text когда action == 'support'.
    """
    uid      = update.effective_user.id
    lang     = get_lang(uid)
    username = update.effective_user.username or update.effective_user.first_name
    text     = update.message.text

    from database import Session, SupportTicket
    with Session() as s:
        ticket = SupportTicket(user_id=uid, username=username, message=text, status="open")
        s.add(ticket)
        s.commit()
        ticket_id = ticket.id

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            t("btn_support_reply", "ru"),
            callback_data=f"support_reply_{ticket_id}"
        )
    ]])

    for admin_id in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                admin_id,
                t("support_msg_to_admin", "ru",
                  username=username, uid=uid, text=text) + f"\n\n🎫 Тикет #{ticket_id}",
                parse_mode="Markdown",
                reply_markup=kb
            )
        except Exception:
            pass

    await update.message.reply_text(
        t("support_sent", lang),
        reply_markup=main_keyboard(lang)
    )
    ctx.user_data.pop("action", None)
    return True


async def support_reply_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Админ нажал 'Ответить' - просим написать ответ ЧЕРЕЗ Reply на это
    сообщение, чтобы Telegram сам привязал ответ к нужному тикету"""
    query     = update.callback_query
    await query.answer()
    ticket_id = int(query.data.replace("support_reply_", ""))

    from database import Session, SupportTicket
    with Session() as s:
        ticket = s.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket:
            await ctx.bot.send_message(query.from_user.id, "❌ Тикет не найден.")
            return

    await ctx.bot.send_message(
        query.from_user.id,
        f"✏️ Тикет #{ticket_id} - напиши ответ ОТВЕТОМ на это сообщение (Reply):",
        reply_markup=ForceReply(input_field_placeholder="Ваш ответ...")
    )


async def handle_support_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Определяет тикет по тому, НА КАКОЕ сообщение админ ответил (Telegram reply),
    а не по общей переменной в user_data - так два тикета подряд не перепутаются.
    Возвращает True, если это был ответ на тикет поддержки.
    """
    uid  = update.effective_user.id
    lang = get_lang(uid)

    replied = update.message.reply_to_message
    if not replied or not replied.text or "Тикет #" not in replied.text:
        return False

    import re
    match = re.search(r"Тикет #(\d+)", replied.text)
    if not match:
        return False
    ticket_id = int(match.group(1))

    from database import Session, SupportTicket
    with Session() as s:
        ticket = s.query(SupportTicket).filter_by(id=ticket_id).first()
        if not ticket:
            await update.message.reply_text("❌ Тикет не найден.")
            return True
        user_id = ticket.user_id

    text = update.message.text

    try:
        user_lang = get_lang(user_id)
        await ctx.bot.send_message(
            user_id,
            t("support_reply_to_user", user_lang, text=text),
            parse_mode="Markdown"
        )
        from utils.time_utils import get_now
        with Session() as s:
            ticket = s.query(SupportTicket).filter_by(id=ticket_id).first()
            if ticket:
                ticket.status     = "answered"
                ticket.admin_id   = uid
                ticket.reply_text = text
                ticket.replied_at = get_now()
                s.commit()
        await update.message.reply_text(t("support_reply_sent", lang))
    except Exception:
        await update.message.reply_text("❌ Не удалось отправить ответ.")

    return True