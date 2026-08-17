from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database import Session, User
from texts import t
from config import ADMIN_IDS
from utils.helpers import get_lang, is_admin, log_event
from utils.constants import LANG_SELECT
from keyboards.main import main_keyboard
from keyboards.inline import lang_keyboard


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid     = update.effective_user.id
    payload = ctx.args[0] if ctx.args else None

    with Session() as s:
        user = s.query(User).filter_by(telegram_id=uid).first()
        if user:
            lang = user.language

            if payload:

                await _handle_deep_link(payload, uid, lang, ctx)
                return ConversationHandler.END

            hint = ""
            if is_admin(uid):
                hint = "\n\n⚙️ /admin — " + ("Панель администратора" if lang == "ru" else "Administrator paneli")
            await update.message.reply_text(
                t("welcome", lang) + hint,
                reply_markup=main_keyboard(lang),
                parse_mode="Markdown",
            )
            return ConversationHandler.END

    # Новый пользователь — спрашиваем язык, диплинк обработаем после выбора
    if payload:
        ctx.user_data["pending_deep_link"] = payload
    await update.message.reply_text(
        t("choose_lang", "ru"),
        reply_markup=lang_keyboard(),
    )


async def _handle_deep_link(payload, uid, lang, ctx):
    if not payload:
        return
    if payload.startswith("pkg_"):
        from handlers.buyer import show_deep_link_package
        try:
            pkg_id = int(payload.replace("pkg_", ""))
            await show_deep_link_package(uid, pkg_id, ctx, lang)
        except ValueError:
            pass
    elif payload.startswith("claim_"):
        await _handle_claim_code(payload.replace("claim_", ""), uid, lang, ctx)


async def _handle_claim_code(code, uid, lang, ctx):
    from database import Restaurant
    with Session() as s:
        rest = s.query(Restaurant).filter_by(claim_code=code, owner_id=None).first()
        if not rest:
            await ctx.bot.send_message(uid, t("claim_invalid", lang))
            return

        rest.owner_id   = uid
        rest.claim_code = None

        u = s.query(User).filter_by(telegram_id=uid).first()
        if u and u.role == "buyer":
            u.role = "owner"
        rest_name = rest.name
        s.commit()

    try:
        from telegram import BotCommand, BotCommandScopeChat
        await ctx.bot.set_my_commands([
            BotCommand("start",    "🚀 Запустить бота / Botni ishga tushirish"),
            BotCommand("language", "🌍 Язык / Til"),
            BotCommand("mypanel",  "🏪 Панель заведения / Muassasa paneli"),
        ], scope=BotCommandScopeChat(chat_id=uid))
    except Exception:
        pass

    await ctx.bot.send_message(uid, t("claim_success", lang, rest=rest_name))


async def lang_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    lang = query.data.replace("lang_", "")

    with Session() as s:
        role     = "admin" if is_admin(uid) else "buyer"
        existing = s.query(User).filter_by(telegram_id=uid).first()
        is_new   = existing is None
        if existing:
            existing.language = lang
            existing.role     = role
        else:
            s.add(User(telegram_id=uid, language=lang, role=role))
        s.commit()

    if is_new:
        log_event("new_user", uid)
    await query.delete_message()

    if is_new:
        hint = ""
        if is_admin(uid):
            hint = "\n\n⚙️ /admin — " + ("Панель администратора" if lang == "ru" else "Administrator paneli")

        await ctx.bot.send_message(
            uid,
            t("welcome", lang) + hint,
            reply_markup=main_keyboard(lang),
            parse_mode="Markdown",
        )
        payload = ctx.user_data.pop("pending_deep_link", None)
        await _handle_deep_link(payload, uid, lang, ctx)
    else:
        await ctx.bot.send_message(
            uid,
            t("language_changed", lang),
            reply_markup=main_keyboard(lang),
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

async def language_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from keyboards.inline import lang_keyboard
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(
        t("choose_lang", lang),
        reply_markup=lang_keyboard(),
    )

async def cancel_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from utils.helpers import get_lang
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    ctx.user_data.clear()
    await query.edit_message_text(t("cancelled", lang))
    await ctx.bot.send_message(query.from_user.id, "⌨️", reply_markup=main_keyboard(lang))
    return ConversationHandler.END
