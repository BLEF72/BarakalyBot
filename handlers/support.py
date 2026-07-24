from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    Обрабатывает сообщение поддержки.
    Вызывается из handle_text когда action == 'support'.
    Возвращает True если обработал.
    """
    uid      = update.effective_user.id
    lang     = get_lang(uid)
    username = update.effective_user.username or update.effective_user.first_name
    text     = update.message.text

    # Отправляем админам
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "↩️ Ответить" if True else "↩️ Javob berish",
            callback_data=f"support_reply_{uid}"
        )
    ]])

    for admin_id in ADMIN_IDS:
        try:
            await ctx.bot.send_message(
                admin_id,
                t("support_msg_to_admin", "ru",
                  username=username, uid=uid, text=text),
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
    """Админ нажал 'Ответить'"""
    query   = update.callback_query
    await query.answer()
    uid     = query.from_user.id
    user_id = int(query.data.replace("support_reply_", ""))

    ctx.user_data["action"]          = "support_reply"
    ctx.user_data["support_user_id"] = user_id

    await ctx.bot.send_message(
        uid,
        f"✏️ Напиши ответ пользователю (ID: {user_id}):"
    )


async def handle_support_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Обрабатывает ответ админа.
    Вызывается из handle_text когда action == 'support_reply'.
    """
    uid     = update.effective_user.id
    lang    = get_lang(uid)
    text    = update.message.text
    user_id = ctx.user_data.get("support_user_id")

    if not user_id:
        return False

    try:
        user_lang = get_lang(user_id)
        await ctx.bot.send_message(
            user_id,
            t("support_reply_to_user", user_lang, text=text),
            parse_mode="Markdown"
        )
        await update.message.reply_text(t("support_reply_sent", lang))
    except Exception:
        await update.message.reply_text("❌ Не удалось отправить ответ.")

    ctx.user_data.pop("action", None)
    ctx.user_data.pop("support_user_id", None)
    return True