from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import Session, User
from texts import t
from config import ADMIN_IDS
from utils.helpers import is_admin, log_event
from utils.constants import LANG_SELECT
from keyboards.main import main_keyboard
from keyboards.inline import lang_keyboard


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    with Session() as s:
        user = s.query(User).filter_by(telegram_id=uid).first()
        if user:
            lang = user.language
            hint = ""
            if is_admin(uid):
                hint = "\n\n⚙️ /admin — " + ("Панель администратора" if lang == "ru" else "Administrator paneli")
            await update.message.reply_text(
                t("welcome", lang) + hint,
                reply_markup=main_keyboard(lang),
                parse_mode="Markdown",
            )
            return ConversationHandler.END

    # Новый пользователь — спрашиваем язык
    await update.message.reply_text(
        t("choose_lang", "ru"),
        reply_markup=lang_keyboard(),
    )
    return LANG_SELECT


async def lang_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    lang = query.data.replace("lang_", "")

    with Session() as s:
        role = "admin" if is_admin(uid) else "buyer"
        s.add(User(telegram_id=uid, language=lang, role=role))
        s.commit()

    log_event("new_user", uid)
    await query.delete_message()

    hint = ""
    if is_admin(uid):
        hint = "\n\n⚙️ /admin — " + ("Панель администратора" if lang == "ru" else "Administrator paneli")

    await ctx.bot.send_message(
        uid,
        t("welcome", lang) + hint,
        reply_markup=main_keyboard(lang),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from utils.helpers import get_lang
    lang = get_lang(update.effective_user.id)
    ctx.user_data.clear()
    await update.message.reply_text(
        t("cancelled", lang),
        reply_markup=main_keyboard(lang),
    )
    return ConversationHandler.END

async def cancel_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from utils.helpers import get_lang
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    ctx.user_data.clear()
    await query.edit_message_text(t("cancelled", lang))
    await ctx.bot.send_message(query.from_user.id, "⌨️", reply_markup=main_keyboard(lang))
    return ConversationHandler.END
