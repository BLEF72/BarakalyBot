import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import Session, Package, Restaurant, User
from texts import t
from utils.helpers import get_lang, is_admin, is_owner, get_owner_restaurant, get_owner_restaurants
from utils.constants import O_NAME, O_PHOTO, O_PRICE, O_QTY, O_TIME, O_EDIT_PRICE, O_EDIT_QTY, O_TEMPLATE_QTY, O_UPDATE_PHOTO, O_EDIT_TIME
from keyboards.inline import owner_panel_keyboard
from services import order_service, package_service, template_service


# ══════════════════════════════════════════════════════════════════════════════
# ПАНЕЛЬ ВЛАДЕЛЬЦА
# ══════════════════════════════════════════════════════════════════════════════

async def owner_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)

    if not is_owner(uid) and not is_admin(uid):
        await update.message.reply_text(t("no_access", lang))
        return

    rests = get_owner_restaurants(uid)

    if not rests and is_admin(uid):
        from handlers.admin import admin_panel
        await admin_panel(update, ctx)
        return

    if not rests:
        await update.message.reply_text(t("no_access", lang))
        return

    if len(rests) == 1:
        await _show_rest_panel(update, ctx, lang, rests[0], send_func="message")
        return

    label   = "Qaysi muassasani boshqarmoqchisiz?" if lang == "uz" else "Выбери заведение:"
    buttons = [
        [InlineKeyboardButton(f"🏪 {r.name} · {r.district}", callback_data=f"owner_panel_rest_{r.id}")]
        for r in rests
    ]
    await update.message.reply_text(label, reply_markup=InlineKeyboardMarkup(buttons))


async def _show_rest_panel(update, ctx, lang, rest, send_func="message"):
    from datetime import datetime
    from database import Order
    from sqlalchemy import func

    uid = update.effective_user.id if hasattr(update, 'effective_user') and update.effective_user else update.callback_query.from_user.id

    with Session() as s:
        my_pkgs = s.query(Package).filter_by(restaurant_id=rest.id, active=True).all()

        today_count = (
            s.query(Order).join(Package, Order.package_id == Package.id)
            .filter(Package.restaurant_id == rest.id,
                    Order.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0))
            .count()
        )
        total_orders = (
            s.query(Order).join(Package, Order.package_id == Package.id)
            .filter(Package.restaurant_id == rest.id).count()
        )
        done_orders = (
            s.query(Order).join(Package, Order.package_id == Package.id)
            .filter(Package.restaurant_id == rest.id, Order.status == "used").count()
        )
        now = datetime.utcnow()
        month_orders = (
            s.query(Order).join(Package, Order.package_id == Package.id)
            .filter(Package.restaurant_id == rest.id,
                    Order.created_at >= datetime(now.year, now.month, 1))
            .count()
        )
        revenue = (
            s.query(func.sum(Package.price)).join(Order, Order.package_id == Package.id)
            .filter(Package.restaurant_id == rest.id, Order.status == "used").scalar()
        ) or 0

    currency = "so'm" if lang == "uz" else "сум"
    unit     = "ta"   if lang == "uz" else "шт."

    pkg_lines = "\n".join(
        f"  • {p.name} — {p.price:,} {currency} ({p.quantity} {unit})"
        for p in my_pkgs
    ) or ("  Yo'q" if lang == "uz" else "  Нет пакетов")

    if lang == "uz":
        stats = (
            f"📊 *Statistika:*\n"
            f"  🗓 Bugun: {today_count} ta buyurtma\n"
            f"  📅 Bu oy: {month_orders} ta buyurtma\n"
            f"  📦 Jami: {total_orders} ta buyurtma\n"
            f"  ✅ Berilgan: {done_orders} ta\n"
            f"  💰 Daromad: {revenue:,} so'm"
        )
    else:
        stats = (
            f"📊 *Статистика:*\n"
            f"  🗓 Сегодня: {today_count} заказов\n"
            f"  📅 Этот месяц: {month_orders} заказов\n"
            f"  📦 Всего: {total_orders} заказов\n"
            f"  ✅ Выдано: {done_orders}\n"
            f"  💰 Выручка: {revenue:,} {currency}"
        )

    header = (
        f"🏪 *{rest.name}*\n📍 {rest.address}\n\n"
        f"📦 {'Faol paketlar' if lang == 'uz' else 'Активные пакеты'}:\n{pkg_lines}\n\n"
        + stats
    )

    kb = owner_panel_keyboard(lang, rest.id, is_closed=rest.is_closed)

    if send_func == "message":
        await ctx.bot.send_message(uid, header, parse_mode="Markdown", reply_markup=kb)
    else:
        await update.callback_query.edit_message_text(header, parse_mode="Markdown", reply_markup=kb)


# ══════════════════════════════════════════════════════════════════════════════
# ГЛАВНЫЙ CALLBACK
# ══════════════════════════════════════════════════════════════════════════════

async def owner_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = query.from_user.id
    lang  = get_lang(uid)
    data  = query.data

    if not data.startswith("savetpl_"):
        await query.answer()

    if not is_owner(uid) and not is_admin(uid):
        await query.edit_message_text(t("no_access", lang))
        return

    if data.startswith("owner_add_pkg_"):
        rest_id = int(data.replace("owner_add_pkg_", ""))
        ctx.user_data["new_pkg"]        = {"restaurant_id": rest_id}
        ctx.user_data["adding_package"] = True
        ctx.user_data["pkg_state"]      = O_NAME
        await query.edit_message_text(t("ask_pkg_name", lang), parse_mode="Markdown")
        return

    elif data.startswith("owner_select_rest_"):
        rest_id = int(data.replace("owner_select_rest_", ""))
        ctx.user_data["new_pkg"]        = {"restaurant_id": rest_id}
        ctx.user_data["adding_package"] = True
        ctx.user_data["pkg_state"]      = O_NAME
        await query.edit_message_text(t("ask_pkg_name", lang), parse_mode="Markdown")
        return

    elif data.startswith("owner_today_"):
        rest_id = int(data.replace("owner_today_", ""))
        rows    = order_service.get_restaurant_orders_today(rest_id)
        if not rows:
            msg = "Bugun buyurtma yo'q." if lang == "uz" else "Сегодня заказов нет."
            await query.edit_message_text(msg)
            return
        icons = {"reserved": "⏳", "active": "✅", "used": "🎉", "cancelled": "❌"}
        text  = "Bugungi buyurtmalar:\n\n" if lang == "uz" else "Заказы сегодня:\n\n"
        for o, pkg in rows:
            icon  = icons.get(o.status, "❓")
            text += f"{icon} `{o.code}` — @{o.username} | {pkg.name}\n"
        await query.edit_message_text(text, parse_mode="Markdown")

    elif data == "owner_mark_start":
        await query.edit_message_text(t("ask_order_code", lang))
        ctx.user_data["action"] = "mark_done"

    elif data.startswith("owner_edit_pkgs_"):
        rest_id  = int(data.replace("owner_edit_pkgs_", ""))
        pkgs     = package_service.get_by_restaurant(rest_id)
        if not pkgs:
            msg = "Faol paketlar yo'q." if lang == "uz" else "Активных пакетов нет."
            await query.edit_message_text(msg)
            return
        currency = "so'm" if lang == "uz" else "сум"
        unit     = "ta"   if lang == "uz" else "шт."
        buttons  = [
            [InlineKeyboardButton(
                f"🛍 {p.name} — {p.price:,} {currency} ({p.quantity} {unit})",
                callback_data=f"editpkg_select_{p.id}"
            )]
            for p in pkgs
        ]
        await query.edit_message_text(t("edit_pkg_header", lang), reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("editpkg_select_"):
        pkg_id = int(data.replace("editpkg_select_", ""))
        from keyboards.inline import edit_pkg_keyboard
        await query.edit_message_text(t("edit_pkg_header", lang), reply_markup=edit_pkg_keyboard(lang, pkg_id))

    elif data.startswith("editpkg_price_"):
        pkg_id = int(data.replace("editpkg_price_", ""))
        ctx.user_data["edit_pkg_id"]     = pkg_id
        ctx.user_data["edit_pkg_action"] = "price"
        await query.edit_message_text(t("ask_new_price", lang), parse_mode="Markdown")
        return O_EDIT_PRICE

    elif data.startswith("editpkg_qty_"):
        pkg_id = int(data.replace("editpkg_qty_", ""))
        ctx.user_data["edit_pkg_id"]     = pkg_id
        ctx.user_data["edit_pkg_action"] = "qty"
        await query.edit_message_text(t("ask_new_qty", lang), parse_mode="Markdown")
        return O_EDIT_QTY

    elif data.startswith("editpkg_time_"):
        pkg_id = int(data.replace("editpkg_time_", ""))
        ctx.user_data["edit_pkg_id"] = pkg_id
        from keyboards.inline import pickup_time_keyboard
        await query.edit_message_text(
            t("ask_pkg_time", lang),
            parse_mode="Markdown",
            reply_markup=pickup_time_keyboard(lang, prefix="pickuptime_edit")
        )
        return O_EDIT_TIME

    elif data.startswith("editpkg_deact_"):
        pkg_id = int(data.replace("editpkg_deact_", ""))
        package_service.deactivate(pkg_id)
        await query.edit_message_text(t("pkg_deactivated", lang))

    elif data.startswith("owner_templates_"):
        rest_id   = int(data.replace("owner_templates_", ""))
        templates = template_service.get_templates(rest_id)
        if not templates:
            await query.edit_message_text(t("no_templates", lang))
            return
        currency = "so'm" if lang == "uz" else "сум"
        buttons  = [
            [InlineKeyboardButton(
                f"📋 {tpl.name} — {tpl.price:,} {currency}",
                callback_data=f"usetpl_{tpl.id}_{rest_id}"
            )]
            for tpl in templates
        ]
        await query.edit_message_text(t("choose_template", lang), reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("usetpl_"):
        parts        = data.replace("usetpl_", "").split("_")
        template_id  = int(parts[0])
        rest_id      = int(parts[1])
        ctx.user_data["use_template_id"]      = template_id
        ctx.user_data["use_template_rest_id"] = rest_id
        await query.edit_message_text(t("ask_template_qty", lang), parse_mode="Markdown")
        return O_TEMPLATE_QTY

    elif data.startswith("savetpl_"):
        pkg_id = int(data.replace("savetpl_", ""))
        with Session() as s:
            pkg = s.query(Package).filter_by(id=pkg_id).first()
            if pkg:
                template_service.create_template(
                    restaurant_id = pkg.restaurant_id,
                    name          = pkg.name,
                    photo_file_id = pkg.photo_file_id,
                    price         = pkg.price,
                    pickup_from   = pkg.pickup_from,
                    pickup_to     = pkg.pickup_to,
                )
        await ctx.bot.send_message(uid, t("template_saved", lang))

    elif data == "skip_pkg_photo":
        ctx.user_data["new_pkg"]["photo_file_id"] = None
        ctx.user_data["pkg_state"]                = O_PRICE
        await query.edit_message_text(t("ask_pkg_price", lang), parse_mode="Markdown")

    elif data.startswith("owner_panel_rest_"):
        rest_id = int(data.replace("owner_panel_rest_", ""))
        with Session() as s:
            rest = s.query(Restaurant).filter_by(id=rest_id).first()
            if rest:
                s.expunge(rest)
        if rest:
            await _show_rest_panel(update, ctx, lang, rest, send_func="edit")

    elif data.startswith("pickuptime_edit_"):
        value  = data.replace("pickuptime_edit_", "")
        pkg_id = ctx.user_data.get("edit_pkg_id")
        if value == "custom":
            await query.edit_message_text(t("ask_pkg_time_custom", lang), parse_mode="Markdown")
            return O_EDIT_TIME
        parts = value.split("-")
        package_service.update_time(pkg_id, parts[0], parts[1])
        await query.edit_message_text(t("pkg_time_updated", lang))
        ctx.user_data.pop("edit_pkg_id", None)
        return ConversationHandler.END

    elif data.startswith("owner_update_photo_"):
        rest_id = int(data.replace("owner_update_photo_", ""))
        ctx.user_data["update_photo_rest_id"] = rest_id
        await query.edit_message_text(t("ask_new_rest_photo", lang), parse_mode="Markdown")
        return O_UPDATE_PHOTO

    elif data.startswith("owner_close_rest_"):
        rest_id = int(data.replace("owner_close_rest_", ""))
        package_service.close_restaurant(rest_id)
        await query.edit_message_text(
            t("rest_closed", lang),
            parse_mode="Markdown",
            reply_markup=owner_panel_keyboard(lang, rest_id, is_closed=True)
        )

    elif data.startswith("owner_open_rest_"):
        rest_id = int(data.replace("owner_open_rest_", ""))
        package_service.open_restaurant(rest_id)
        with Session() as s:
            rest = s.query(Restaurant).filter_by(id=rest_id).first()
            if rest:
                s.expunge(rest)
        await query.edit_message_text(t("rest_opened", lang))
        await _show_rest_panel(update, ctx, lang, rest, send_func="message")


# ══════════════════════════════════════════════════════════════════════════════
# ВЫБОР ВРЕМЕНИ ПРИ ДОБАВЛЕНИИ НОВОГО ПАКЕТА
# ══════════════════════════════════════════════════════════════════════════════

async def handle_pickup_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_lang(uid)
    value = query.data.replace("pickuptime_", "")

    if value == "custom":
        await query.edit_message_text(t("ask_pkg_time_custom", lang), parse_mode="Markdown")
        ctx.user_data["pkg_state"] = O_TIME
        return

    parts = value.split("-")
    ctx.user_data["new_pkg"]["pickup_from"] = parts[0]
    ctx.user_data["new_pkg"]["pickup_to"]   = parts[1]

    await query.edit_message_text(
        f"🕒 {'Vaqt tanlandi' if lang == 'uz' else 'Время выбрано'}: *{value}*",
        parse_mode="Markdown"
    )
    await _save_package(update, ctx, lang)


# ══════════════════════════════════════════════════════════════════════════════
# ШАГИ ДОБАВЛЕНИЯ ПАКЕТА
# ══════════════════════════════════════════════════════════════════════════════

async def o_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    ctx.user_data["new_pkg"]["name"] = update.message.text.strip()
    ctx.user_data["pkg_state"]       = O_PHOTO

    skip_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_skip_photo", lang), callback_data="skip_pkg_photo")
    ]])
    await update.message.reply_text(t("ask_pkg_photo", lang), parse_mode="Markdown", reply_markup=skip_kb)
    return O_PHOTO


async def o_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    ctx.user_data["new_pkg"]["photo_file_id"] = (
        update.message.photo[-1].file_id if update.message.photo else None
    )
    ctx.user_data["pkg_state"] = O_PRICE
    await update.message.reply_text(t("ask_pkg_price", lang), parse_mode="Markdown")
    return O_PRICE


async def o_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        ctx.user_data["new_pkg"]["price"] = price
        ctx.user_data["pkg_state"]        = O_QTY
        await update.message.reply_text(t("ask_pkg_qty", lang), parse_mode="Markdown")
        return O_QTY
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return O_PRICE


async def o_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        ctx.user_data["new_pkg"]["quantity"] = int(update.message.text.strip())
        ctx.user_data["pkg_state"]           = O_TIME
        from keyboards.inline import pickup_time_keyboard
        await update.message.reply_text(
            t("ask_pkg_time", lang),
            parse_mode="Markdown",
            reply_markup=pickup_time_keyboard(lang)
        )
        return O_TIME
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return O_QTY


async def o_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang  = get_lang(update.effective_user.id)
    raw   = update.message.text.strip()
    match = re.match(r"(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})", raw)
    if not match:
        await update.message.reply_text(t("invalid_time", lang))
        return O_TIME

    ctx.user_data["new_pkg"]["pickup_from"] = match.group(1).replace(".", ":")
    ctx.user_data["new_pkg"]["pickup_to"]   = match.group(2).replace(".", ":")
    await _save_package(update, ctx, lang)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# СОХРАНЕНИЕ ПАКЕТА
# ══════════════════════════════════════════════════════════════════════════════

async def _save_package(update, ctx, lang):
    data        = ctx.user_data["new_pkg"]
    pickup_from = data.get("pickup_from", "")
    pickup_to   = data.get("pickup_to", "")
    uid = (update.effective_user.id if update.effective_user
           else update.callback_query.from_user.id)
    bot = (update.get_bot() if hasattr(update, 'get_bot')
           else update.callback_query.get_bot())

    with Session() as s:
        rest          = s.query(Restaurant).filter_by(id=data["restaurant_id"]).first()
        rest_name     = rest.name     if rest else ""
        rest_address  = rest.address  if rest else ""
        rest_district = rest.district if rest else ""
        s.add(Package(
            restaurant_id = data["restaurant_id"],
            name          = data["name"],
            photo_file_id = data.get("photo_file_id"),
            price         = data["price"],
            quantity      = data["quantity"],
            pickup_from   = pickup_from,
            pickup_to     = pickup_to,
            active        = True,
        ))
        s.commit()

    await bot.send_message(uid, t("pkg_added", lang))

    with Session() as s:
        new_pkg = s.query(Package).filter_by(
            restaurant_id=data["restaurant_id"], name=data["name"]
        ).order_by(Package.id.desc()).first()
        new_pkg_id = new_pkg.id if new_pkg else None
        if new_pkg:
            s.expunge(new_pkg)

    if new_pkg_id:
        save_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(t("btn_save_template", lang), callback_data=f"savetpl_{new_pkg_id}")
        ]])
        await bot.send_message(
            uid,
            "💾 " + ("Хотите сохранить как шаблон?" if lang == "ru" else "Shablon sifatida saqlaysizmi?"),
            reply_markup=save_kb
        )

    from services.package_service import post_to_channel
    from services.review_service import get_rating
    from database import Session as DS, Package as Pkg, Restaurant as Rest

    with DS() as s:
        pkg_obj  = s.query(Pkg).filter_by(id=new_pkg_id).first()
        rest_obj = s.query(Rest).filter_by(id=data["restaurant_id"]).first()
        if pkg_obj and rest_obj:
            s.expunge(pkg_obj)
            s.expunge(rest_obj)

    if new_pkg_id and pkg_obj and rest_obj:
        rating = get_rating(data["restaurant_id"])
        await post_to_channel(bot, pkg_obj, rest_obj, rating)

    from services import subscription_service
    subscribers = set(
        subscription_service.get_subscribers_for_restaurant(data["restaurant_id"]) +
        subscription_service.get_subscribers_for_district(rest_district)
    )
    for user_id in subscribers:
        try:
            user_lang = get_lang(user_id)
            msg = t("new_pkg_notify", user_lang,
                    rest=rest_name, name=data["name"],
                    price=data["price"], qty=data["quantity"],
                    from_=pickup_from, to=pickup_to, address=rest_address)
            await bot.send_message(user_id, msg, parse_mode="Markdown")
        except Exception:
            pass

    ctx.user_data.clear()


# ══════════════════════════════════════════════════════════════════════════════
# РЕДАКТИРОВАНИЕ ПАКЕТОВ
# ══════════════════════════════════════════════════════════════════════════════

async def o_edit_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        price  = int(update.message.text.replace(" ", "").replace(",", ""))
        pkg_id = ctx.user_data.get("edit_pkg_id")
        package_service.update_price(pkg_id, price)
        await update.message.reply_text(t("pkg_updated", lang))
        ctx.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return O_EDIT_PRICE


async def o_edit_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        qty    = int(update.message.text.strip())
        pkg_id = ctx.user_data.get("edit_pkg_id")
        package_service.update_quantity(pkg_id, qty)
        await update.message.reply_text(t("pkg_updated", lang))
        ctx.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return O_EDIT_QTY


async def o_edit_time(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang  = get_lang(update.effective_user.id)
    raw   = update.message.text.strip()
    match = re.match(r"(\d{1,2}[:.]\d{2})\s*[-–]\s*(\d{1,2}[:.]\d{2})", raw)
    if not match:
        await update.message.reply_text(t("invalid_time", lang))
        return O_EDIT_TIME
    pkg_id = ctx.user_data.get("edit_pkg_id")
    package_service.update_time(
        pkg_id,
        match.group(1).replace(".", ":"),
        match.group(2).replace(".", ":")
    )
    await update.message.reply_text(t("pkg_time_updated", lang))
    ctx.user_data.pop("edit_pkg_id", None)
    return ConversationHandler.END


# ══════════════════════════════════════════════════════════════════════════════
# ШАБЛОНЫ
# ══════════════════════════════════════════════════════════════════════════════

async def o_template_qty(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    try:
        qty         = int(update.message.text.strip())
        template_id = ctx.user_data.get("use_template_id")
        rest_id     = ctx.user_data.get("use_template_rest_id")
        tpl         = template_service.get_template(template_id)

        if not tpl:
            await update.message.reply_text("❌ Шаблон не найден.")
            ctx.user_data.clear()
            return ConversationHandler.END

        with Session() as s:
            s.add(Package(
                restaurant_id = rest_id,
                name          = tpl.name,
                photo_file_id = tpl.photo_file_id,
                price         = tpl.price,
                quantity      = qty,
                pickup_from   = tpl.pickup_from,
                pickup_to     = tpl.pickup_to,
                active        = True,
            ))
            s.commit()

        await update.message.reply_text(t("template_pkg_added", lang))
        ctx.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return O_TEMPLATE_QTY


# ══════════════════════════════════════════════════════════════════════════════
# ОБНОВЛЕНИЕ ФОТО ЗАВЕДЕНИЯ
# ══════════════════════════════════════════════════════════════════════════════

async def o_update_rest_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang    = get_lang(update.effective_user.id)
    rest_id = ctx.user_data.get("update_photo_rest_id")

    if not update.message.photo:
        await update.message.reply_text(
            "❌ " + ("Отправь фото" if lang == "ru" else "Rasm yuboring")
        )
        return O_UPDATE_PHOTO

    photo_file_id = update.message.photo[-1].file_id
    with Session() as s:
        rest = s.query(Restaurant).filter_by(id=rest_id).first()
        if rest:
            rest.photo_file_id = photo_file_id
            s.commit()

    await update.message.reply_text(t("rest_photo_updated", lang))
    ctx.user_data.pop("update_photo_rest_id", None)
    return ConversationHandler.END