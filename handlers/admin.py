from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database import Session, Restaurant, User
from texts import t
from utils.helpers import get_lang, is_admin
from utils.constants import A_LOCATION, A_NAME, A_ADDRESS, A_DISTRICT, A_OWNER, A_PHOTO
from keyboards.inline import admin_panel_keyboard, district_select_keyboard
from services import analytics_service, order_service, package_service
from services import report_service



async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(t("no_access", "ru"))
        return

    lang  = get_lang(uid)
    stats = analytics_service.get_stats()
    text  = t("admin_stats", lang,
              rests=stats["restaurants"], pkgs=stats["packages"],
              orders=stats["orders"],    done=stats["done"],
              users=stats["users"], commission=stats["commission"])

    await update.message.reply_text(
        text + "\n\n⚙️ *Панель администратора*",
        parse_mode="Markdown",
        reply_markup=admin_panel_keyboard(),
    )


async def admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid  = query.from_user.id
    lang = get_lang(uid)
    data = query.data

    if not is_admin(uid):
        await query.edit_message_text(t("no_access", lang))
        return

    if data == "admin_list_rests":
        with Session() as s:
            rows = s.query(Restaurant).all()
        if not rows:
            await query.edit_message_text("Заведений нет.")
            return
        text = "🏪 *Заведения:*\n\n"
        for r in rows:
            text += f"{'✅' if r.active else '❌'} *{r.name}* | {r.district}\n📍 {r.address}\n\n"
        await query.edit_message_text(text[:4000], parse_mode="Markdown")

    elif data == "admin_list_pkgs":
        rows = package_service.get_all_active()
        if not rows:
            await query.edit_message_text("Активных пакетов нет.")
            return
        text = "📦 *Активные пакеты:*\n\n"
        for pkg, rest in rows:
            text += f"🛍 *{pkg.name}* | {rest.name} | {pkg.price:,} сум | {pkg.quantity} шт. | {pkg.pickup_from}–{pkg.pickup_to}\n"
        await query.edit_message_text(text[:4000], parse_mode="Markdown")

    elif data == "admin_list_orders":
        rows = order_service.get_last_orders(20)
        if not rows:
            await query.edit_message_text("Заказов нет.")
            return
        text  = "🧾 *Последние заказы:*\n\n"
        icons = {"reserved": "⏳", "active": "✅", "used": "🎉", "cancelled": "❌", "expired": "👻"}
        for o, pkg, rest in rows:
            icon  = icons.get(o.status, "❓")
            text += f"{icon} `{o.code}` @{o.username} | {rest.name} | {pkg.price:,} сум\n"
        await query.edit_message_text(text[:4000], parse_mode="Markdown")

    elif data == "admin_analytics":
        today_count = analytics_service.count_today_orders()
        total_count = order_service.count_all()
        districts   = analytics_service.get_district_stats()
        text = (
            f"📊 *Аналитика:*\n\n"
            f"Заказов сегодня: {today_count}\n"
            f"Всего заказов: {total_count}\n\n"
            f"*Популярные районы:*\n"
        )
        for district, cnt in districts:
            text += f"  📍 {district}: {cnt} просмотров\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif data == "admin_add_rest":
        ctx.user_data["new_rest"] = {}
        await query.edit_message_text(t("admin_add_rest_name", lang))
        return A_NAME
    elif data == "admin_reports":
        rests = report_service.get_all_restaurants()
        if not rests:
            await query.edit_message_text("Заведений нет.")
            return
        buttons = [
            [InlineKeyboardButton(
                f"🏪 {r['name']} · {r['district']}",
                callback_data=f"admin_report_{r['id']}"
            )]
            for r in rests
        ]
        await query.edit_message_text(
            t("choose_rest_report", lang),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("admin_report_"):
        rest_id = int(data.replace("admin_report_", ""))
        report  = report_service.get_restaurant_report(rest_id)
        if not report:
            await query.edit_message_text("Заведение не найдено.")
            return
        text = t("weekly_report", lang,
                 rest          = report["rest_name"],
                 orders        = report["orders"],
                 done          = report["done"],
                 cancelled     = report["cancelled"],
                 no_show       = report["no_show"],
                 revenue       = report["revenue"],
                 rating        = report["rating"],
                 total         = report["total"],
                 total_revenue = report["total_revenue"])
        keyboard = [[InlineKeyboardButton(
            "⬅️ Назад" if lang == "ru" else "⬅️ Orqaga",
            callback_data="admin_reports"
        )]]
        await query.edit_message_text(
            text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
async def a_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    lang = get_lang(update.effective_user.id)

    photo_file_id = None
    if update.message.photo:
        photo_file_id = update.message.photo[-1].file_id
    ctx.user_data["new_rest"]["photo_file_id"] = photo_file_id

    await _save_restaurant(update, ctx, lang)
    return ConversationHandler.END


async def skip_rest_photo_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = get_lang(query.from_user.id)
    ctx.user_data["new_rest"]["photo_file_id"] = None
    await query.edit_message_text(
        t("ask_rest_location", lang),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(t("btn_skip_location", lang), callback_data="skip_rest_location")
        ]])
    )
    return A_LOCATION


async def _save_restaurant(update, ctx, lang):
    data     = ctx.user_data["new_rest"]
    owner_id = data["owner_id"]
    with Session() as s:
        s.add(Restaurant(
            name          = data["name"],
            address       = data["address"],
            district      = data["district"],
            owner_id      = owner_id,
            photo_file_id = data.get("photo_file_id"),
            latitude      = data.get("latitude"),
            longitude     = data.get("longitude"),
            active        = True,
        ))
        u = s.query(User).filter_by(telegram_id=owner_id).first()
        if u and u.role == "buyer":
            u.role = "owner"
        s.commit()

    uid = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
    try:
        await ctx.bot.send_message(
            uid,
            t("rest_added", lang, name=data["name"], owner=owner_id),
            parse_mode="Markdown"
        )
    except Exception:
        pass
    ctx.user_data.clear()

# ── Диалог: добавление заведения ─────────────────────────────────────────────

async def a_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    ctx.user_data["new_rest"]["name"] = update.message.text.strip()
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(t("admin_add_rest_address", lang))
    return A_ADDRESS


async def a_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    ctx.user_data["new_rest"]["address"] = update.message.text.strip()

    skip_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_skip_location", lang), callback_data="skip_rest_location")
    ]])
    await update.message.reply_text(
        t("ask_rest_location", lang),
        parse_mode="Markdown",
        reply_markup=skip_kb
    )
    return A_LOCATION


async def a_district(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(query.from_user.id)
    ctx.user_data["new_rest"]["district"] = query.data.replace("adistrict_", "")
    await query.edit_message_text(t("admin_add_rest_owner", lang), parse_mode="Markdown")
    return A_OWNER


async def a_owner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    lang = get_lang(update.effective_user.id)
    text = update.message.text.strip()
    try:
        owner_id = int(text) if text != "0" else update.effective_user.id
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return A_OWNER

    ctx.user_data["new_rest"]["owner_id"] = owner_id

    skip_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_skip_rest_photo", lang), callback_data="skip_rest_photo")
    ]])
    await update.message.reply_text(
        t("ask_rest_photo", lang),
        parse_mode="Markdown",
        reply_markup=skip_kb
    )
    return A_PHOTO


async def a_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id): return ConversationHandler.END
    lang = get_lang(update.effective_user.id)

    if update.message.location:
        ctx.user_data["new_rest"]["latitude"]  = update.message.location.latitude
        ctx.user_data["new_rest"]["longitude"] = update.message.location.longitude
    else:
        ctx.user_data["new_rest"]["latitude"]  = None
        ctx.user_data["new_rest"]["longitude"] = None

    await update.message.reply_text(
        t("admin_add_rest_district", lang),
        reply_markup=district_select_keyboard(lang),
    )
    return A_DISTRICT


async def skip_rest_location_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = get_lang(query.from_user.id)
    ctx.user_data["new_rest"]["latitude"]  = None
    ctx.user_data["new_rest"]["longitude"] = None

    await query.edit_message_text(
        t("admin_add_rest_district", lang),
        reply_markup=district_select_keyboard(lang))
    return A_DISTRICT
