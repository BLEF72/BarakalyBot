from turtle import update
from keyboards.main import main_keyboard
from telegram import InlineKeyboardButton, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from texts import t
from utils.constants import O_NAME, O_PHOTO, O_PRICE, O_QTY, O_TIME
from utils.helpers import get_lang, get_pickup_status, log_event
from keyboards.inline import district_keyboard, reserve_keyboard, favorite_keyboard
from services import package_service, order_service, favorite_service, review_service, subscription_service


async def show_districts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    await update.message.reply_text(
        t("choose_district", lang),
        reply_markup=district_keyboard(lang),
    )

async def district_selected(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    uid      = query.from_user.id
    lang     = get_lang(uid)
    district = query.data.replace("district_", "")

    rows = package_service.get_available(district)

    if not rows:
        await query.edit_message_text(t("no_packages", lang))
        return

    await query.delete_message()


    for pkg, rest in rows:
        rating  = review_service.get_rating(rest.id)
        reviews = review_service.get_review_count(rest.id)
        status  = get_pickup_status(pkg.pickup_from, pkg.pickup_to, lang)

        text = t("package_card", lang,
             rest=rest.name, address=rest.address, district=rest.district,
             rating=rating, reviews=reviews,
             name=pkg.name, price=pkg.price, qty=pkg.quantity,
             from_=pkg.pickup_from, to=pkg.pickup_to, status=status)

        is_fav     = favorite_service.is_favorite(uid, rest.id)
        is_sub_rest = subscription_service.is_subscribed_restaurant(uid, rest.id)
        is_sub_dist = subscription_service.is_subscribed_district(uid, rest.district)

        fav_label = "❤️ В избранном" if is_fav else "🤍 В избранное"

        buttons = [
            [InlineKeyboardButton(t("btn_reserve", lang, price=pkg.price),
                                  callback_data=f"reserve_{pkg.id}")],
            [InlineKeyboardButton(
                "❤️ В избранном" if is_fav else "🤍 В избранное",
                callback_data=f"fav_{rest.id}"
            ),
            InlineKeyboardButton(
                "🔕" if is_sub_rest else "🔔",
                callback_data=f"sub_rest_{rest.id}"
            )],
        ]

        # Кнопка карты если есть локация
        if rest.latitude and rest.longitude:
            map_url = f"https://maps.google.com/?q={rest.latitude},{rest.longitude}"
            buttons.append([InlineKeyboardButton(t("btn_open_map", lang), url=map_url)])

        kb = InlineKeyboardMarkup(buttons)

        photo = pkg.photo_file_id or rest.photo_file_id
        if photo:
            await ctx.bot.send_photo(uid, photo, caption=text,
                                     parse_mode="Markdown", reply_markup=kb)
        else:
            await ctx.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)


async def reserve_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from keyboards.inline import mark_done_keyboard
    from config import ADMIN_IDS

    query  = update.callback_query
    await query.answer()
    uid    = query.from_user.id
    lang   = get_lang(uid)
    pkg_id = int(query.data.replace("reserve_", ""))

    from database import Session, Package, Restaurant
    with Session() as s:
        pkg  = s.query(Package).filter_by(id=pkg_id, active=True).first()
        rest = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first() if pkg else None
        if not pkg or pkg.quantity <= 0 or not rest:
            await ctx.bot.send_message(uid, t("already_taken", lang))
            return
        rest_name = rest.name
        rest_addr = rest.address
        pfrom     = pkg.pickup_from
        pto       = pkg.pickup_to
        owner_id  = rest.owner_id
        pkg_name  = pkg.name

    try:
        username = query.from_user.username or query.from_user.first_name
        code = order_service.create_reservation(pkg_id, uid, username)
    except ValueError as e:
        err = str(e)
        if "user_blocked" in err:
            await ctx.bot.send_message(uid, t("user_blocked", lang))
        elif "user_limited" in err:
            await ctx.bot.send_message(uid, t("user_limited", lang))
        elif "max_reservations" in err:
            await ctx.bot.send_message(uid, t("max_reservations", lang))
        else:
            await ctx.bot.send_message(uid, t("already_taken", lang))
        return



    # Получаем reserved_until
    from database import Session as DBSession, Order as DBOrder
    with DBSession() as s:
        created_order = s.query(DBOrder).filter_by(code=code).first()
        until_str = created_order.reserved_until.strftime("%H:%M") if created_order else "—"

    cancel_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_cancel_order", lang), callback_data=f"cancel_order_{code}")
    ]])

    await ctx.bot.send_message(
        uid,
        t("reserve_confirm", lang, code=code, rest=rest_name,
          address=rest_addr, from_=pfrom, to=pto, until=until_str),
        parse_mode="Markdown",
        reply_markup=cancel_kb,
    )

    notif   = (
        f"🆕 *Новая бронь!*\n"
        f"Код: `{code}`\n"
        f"👤 @{query.from_user.username or query.from_user.first_name}\n"
        f"🛍 {pkg_name} — {rest_name}"
    )
    mark_kb = mark_done_keyboard(code)

    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(aid, notif, parse_mode="Markdown", reply_markup=mark_kb)
        except Exception:
            pass

    if owner_id and owner_id not in ADMIN_IDS:
        try:
            owner_lang  = get_lang(owner_id)
            notif_owner = (
                f"🆕 {'Yangi bron' if owner_lang == 'uz' else 'Новая бронь'}!\n"
                f"Kod: `{code}`\n"
                f"🛍 {pkg_name}"
            )
            await ctx.bot.send_message(owner_id, notif_owner, parse_mode="Markdown",
                                       reply_markup=mark_kb)
        except Exception:
            pass



async def my_orders(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    rows = order_service.get_user_orders(uid)

    if not rows:
        await update.message.reply_text(t("my_orders_empty", lang), parse_mode="Markdown")
        return

    icons = {"reserved": "⏳", "active": "✅", "used": "🎉", "cancelled": "❌"}

    for order, pkg, rest in rows:
        icon = icons.get(order.status, "❓")
        text = f"{icon} `{order.code}`\n🏪 {rest.name} / {pkg.name}\n"

        if order.status == "reserved":
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    t("btn_cancel_order", lang),
                    callback_data=f"cancel_order_{order.code}"
                )
            ]])
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

        elif order.status == "used":
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    t("btn_rebook", lang),
                    callback_data=f"rebook_{pkg.id}"
                )
            ]])
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)

        else:
            await update.message.reply_text(text, parse_mode="Markdown")


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(update.effective_user.id)
    await update.message.reply_text(t("help", lang), parse_mode="Markdown")


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    from handlers.orders  import mark_done_by_text
    from handlers.owner   import o_name, o_photo, o_price, o_qty, o_time
    from handlers.support import handle_support_message, handle_support_reply, support_start

    uid  = update.effective_user.id
    lang = get_lang(uid)
    text = update.message.text

    # ── ReplyKeyboard кнопки ──────────────────────────────────────────────────
    if text == t("btn_packages", lang):
        await show_districts(update, ctx); return
    if text == t("btn_favorites", lang):
        await show_favorites(update, ctx); return
    if text == t("btn_myorders", lang):
        await my_orders(update, ctx); return
    if text == t("btn_help", lang):
        await help_cmd(update, ctx); return
    if text == t("btn_my_subscriptions", lang):
        await my_subscriptions(update, ctx); return
    if text == t("btn_support", lang):
        await support_start(update, ctx); return
    if text == t("btn_top", lang):
        await show_top(update, ctx); return
    if text == t("btn_search", lang):
        await search_start(update, ctx); return

    # ── Добавление пакета ─────────────────────────────────────────────────────
    if ctx.user_data.get("adding_package"):
        state = ctx.user_data.get("pkg_state", O_NAME)
        if state == O_NAME:
            await o_name(update, ctx)
        elif state == O_PHOTO:
            await o_photo(update, ctx)
        elif state == O_PRICE:
            await o_price(update, ctx)
        elif state == O_QTY:
            await o_qty(update, ctx)
        elif state == O_TIME:
            await o_time(update, ctx)
        return

    # ── Поддержка ─────────────────────────────────────────────────────────────
    if ctx.user_data.get("action") == "support":
        await handle_support_message(update, ctx); return

    if ctx.user_data.get("action") == "support_reply":
        await handle_support_reply(update, ctx); return
    
    if ctx.user_data.get("action") == "search":
        await handle_search(update, ctx); return

    # ── Ввод кода заказа ──────────────────────────────────────────────────────
    if ctx.user_data.get("action") == "mark_done":
        await mark_done_by_text(update, ctx); return

    from utils.helpers import is_admin, is_owner
    hint = "/start — " + ("перезапустить" if lang == "ru" else "qayta boshlash")
    if is_admin(uid) or is_owner(uid):
        hint += "\n/mypanel — " + ("панель заведения" if lang == "ru" else "muassasa paneli")
    if is_admin(uid):
        hint += "\n/admin — " + ("панель администратора" if lang == "ru" else "administrator paneli")
    await update.message.reply_text(hint, reply_markup=main_keyboard(lang))


async def favorite_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query         = update.callback_query
    await query.answer()
    uid           = query.from_user.id
    lang          = get_lang(uid)
    restaurant_id = int(query.data.replace("fav_", ""))

    added = favorite_service.toggle(uid, restaurant_id)
    msg   = t("added_to_favorites", lang) if added else t("removed_from_favorites", lang)
    await ctx.bot.send_message(uid, msg)


async def show_favorites(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    rows = favorite_service.get_user_favorites(uid)

    if not rows:
        await update.message.reply_text(t("favorites_empty", lang))
        return

    await update.message.reply_text(t("favorites_header", lang), parse_mode="Markdown")

    for rest, pkgs in rows:
        if not pkgs:
            text = f"🏪 *{rest.name}*\n📍 {rest.address}\n\n😔 " + (
                "Сейчас нет доступных пакетов" if lang == "ru" else "Hozir paket yo'q"
            )
            await ctx.bot.send_message(uid, text, parse_mode="Markdown")
            continue

        for pkg in pkgs:
            status  = get_pickup_status(pkg.pickup_from, pkg.pickup_to, lang)
            rating  = review_service.get_rating(rest.id)
            reviews = review_service.get_review_count(rest.id)
            is_fav  = favorite_service.is_favorite(uid, rest.id)

            text = t("package_card", lang,
                     rest=rest.name, address=rest.address, district=rest.district,
                     name=pkg.name, price=pkg.price, qty=pkg.quantity,
                     rating=rating, reviews=reviews,
                     from_=pkg.pickup_from, to=pkg.pickup_to, status=status)

            buttons = [
                [InlineKeyboardButton(t("btn_reserve", lang, price=pkg.price),
                                      callback_data=f"reserve_{pkg.id}")],
                [InlineKeyboardButton("❤️ В избранном" if is_fav else "🤍 В избранное",
                                      callback_data=f"fav_{rest.id}")],
            ]
            if rest.latitude and rest.longitude:
                map_url = f"https://maps.google.com/?q={rest.latitude},{rest.longitude}"
                buttons.append([InlineKeyboardButton(t("btn_open_map", lang), url=map_url)])

            kb    = InlineKeyboardMarkup(buttons)
            photo = pkg.photo_file_id or rest.photo_file_id

            if photo:
                await ctx.bot.send_photo(uid, photo, caption=text,
                                         parse_mode="Markdown", reply_markup=kb)
            else:
                await ctx.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)
async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает фото при добавлении пакета"""
    if ctx.user_data.get("adding_package"):
        from handlers.owner import o_photo
        await o_photo(update, ctx)
        
async def subscribe_rest_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query         = update.callback_query
    await query.answer()
    uid           = query.from_user.id
    lang          = get_lang(uid)
    restaurant_id = int(query.data.replace("sub_rest_", ""))

    from database import Session, Restaurant
    with Session() as s:
        rest = s.query(Restaurant).filter_by(id=restaurant_id).first()
        name = rest.name if rest else "?"

    subscribed = subscription_service.toggle_restaurant(uid, restaurant_id)
    key = "subscribed_rest" if subscribed else "unsubscribed_rest"
    await ctx.bot.send_message(uid, t(key, lang, name=name), parse_mode="Markdown")


async def subscribe_dist_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query    = update.callback_query
    await query.answer()
    uid      = query.from_user.id
    lang     = get_lang(uid)
    district = query.data.replace("sub_dist_", "")

    subscribed = subscription_service.toggle_district(uid, district)
    key = "subscribed_district" if subscribed else "unsubscribed_district"
    await ctx.bot.send_message(uid, t(key, lang, district=district), parse_mode="Markdown")


async def my_subscriptions(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    subs = subscription_service.get_user_subscriptions(uid)

    if not subs:
        await update.message.reply_text(
            t("my_subscriptions_empty", lang),
            reply_markup=main_keyboard(lang),
        )
        return

    from database import Session, Restaurant
    text = t("my_subscriptions_header", lang)
    with Session() as s:
        for sub in subs:
            if sub["restaurant_id"]:
                rest = s.query(Restaurant).filter_by(id=sub["restaurant_id"]).first()
                if rest:
                    text += f"🏪 {rest.name} · {rest.district}\n"
            elif sub["district"]:
                text += f"📍 {sub['district']}\n"
                
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(lang),
    )

async def cancel_order_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_lang(uid)
    code  = query.data.replace("cancel_order_", "")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_confirm_cancel", lang), callback_data=f"confirm_cancel_{code}")],
        [InlineKeyboardButton(t("btn_keep_order", lang),     callback_data=f"keep_order_{code}")],
    ])
    await query.edit_message_reply_markup(reply_markup=None)
    await ctx.bot.send_message(
        uid,
        t("cancel_warning", lang, code=code),
        parse_mode="Markdown",
        reply_markup=kb
    )

async def confirm_cancel_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_lang(uid)
    code  = query.data.replace("confirm_cancel_", "")

    result = order_service.cancel_by_user(code, uid)

    if result.startswith("ok"):
        parts    = result.split("|")
        pkg_name = parts[1] if len(parts) > 1 else "?"
        owner_id = int(parts[2]) if len(parts) > 2 and parts[2] else None

        await query.edit_message_reply_markup(reply_markup=None)
        await ctx.bot.send_message(
            uid,
            t("order_cancelled_buyer", lang, code=code),
            parse_mode="Markdown"
        )

        # Уведомляем о рейтинге
        await order_service.notify_rating_change(ctx.bot, uid)

        if owner_id:
            try:
                owner_lang = get_lang(owner_id)
                await ctx.bot.send_message(
                    owner_id,
                    t("order_cancelled_owner", owner_lang, code=code, pkg_name=pkg_name),
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    elif result == "too_late":
        await query.edit_message_reply_markup(reply_markup=None)
        await ctx.bot.send_message(uid, t("order_cancel_too_late", lang))
    else:
        await ctx.bot.send_message(uid, t("order_not_found", lang))


async def keep_order_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang  = get_lang(query.from_user.id)
    await query.edit_message_reply_markup(reply_markup=None)
    await ctx.bot.send_message(
        query.from_user.id,
        "👍 " + ("Бронь сохранена!" if lang == "ru" else "Bron saqlandi!")
    )
        
async def rebook_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    await query.answer()
    uid    = query.from_user.id
    status  = get_pickup_status(pkg.pickup_from, pkg.pickup_to, lang)
    
    lang   = get_lang(uid)
    pkg_id = int(query.data.replace("rebook_", ""))

    from database import Session, Package, Restaurant
    with Session() as s:
        pkg  = s.query(Package).filter_by(id=pkg_id, active=True).first()
        rest = s.query(Restaurant).filter_by(id=pkg.restaurant_id).first() if pkg else None

        if not pkg or pkg.quantity <= 0 or not rest:
            await ctx.bot.send_message(uid, t("rebook_unavailable", lang))
            return

        rest_name   = rest.name
        rest_addr   = rest.address
        pfrom       = pkg.pickup_from
        pto         = pkg.pickup_to
        owner_id    = rest.owner_id
        pkg_name    = pkg.name

    try:
        username = query.from_user.username or query.from_user.first_name
        code = order_service.create_reservation(pkg_id, uid, username)
    except ValueError as e:
        if "max_reservations" in str(e):
            await ctx.bot.send_message(uid, t("max_reservations", lang))
        else:
            await ctx.bot.send_message(uid, t("rebook_unavailable", lang))
        return

# Получаем reserved_until
    from database import Session as DBSession, Order as DBOrder
    with DBSession() as s:
        created_order = s.query(DBOrder).filter_by(code=code).first()
        until_str = created_order.reserved_until.strftime("%H:%M") if created_order else "—"

    cancel_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_cancel_order", lang), callback_data=f"cancel_order_{code}")
    ]])

    await ctx.bot.send_message(
        uid,
        t("reserve_confirm", lang, code=code, rest=rest_name,
          address=rest_addr, from_=pfrom, to=pto, until=until_str),
        parse_mode="Markdown",
        reply_markup=cancel_kb, status=status
    )

    log_event("order", uid)

    # Уведомляем владельца и админов
    from keyboards.inline import mark_done_keyboard
    from config import ADMIN_IDS
    notif = (
        f"🆕 *Повторная бронь!*\n"
        f"Код: `{code}`\n"
        f"👤 @{query.from_user.username or query.from_user.first_name}\n"
        f"🛍 {pkg_name} — {rest_name}"
    )
    mark_kb = mark_done_keyboard(code)
    for aid in ADMIN_IDS:
        try:
            await ctx.bot.send_message(aid, notif, parse_mode="Markdown", reply_markup=mark_kb)
        except Exception:
            pass
    if owner_id and owner_id not in ADMIN_IDS:
        try:
            await ctx.bot.send_message(owner_id, notif, parse_mode="Markdown", reply_markup=mark_kb)
        except Exception:
            pass
        

async def show_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)

    from services.report_service import get_top_restaurants
    tops = get_top_restaurants()

    if not tops:
        await update.message.reply_text(t("top_empty", lang))
        return

    text = t("top_header", lang)
    for i, rest in enumerate(tops, 1):
        rating_str = f"⭐ {rest['rating']}" if rest["review_count"] >= 3 else ("⭐ Новое" if lang == "ru" else "⭐ Yangi")
        text += t("top_item", lang,
                  pos=i, name=rest["name"], district=rest["district"],
                  rating=rating_str, orders=rest["orders"])

    await update.message.reply_text(text, parse_mode="Markdown")
    
    
async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_lang(uid)
    ctx.user_data["action"] = "search"
    await update.message.reply_text(t("search_ask", lang))


async def handle_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    lang  = get_lang(uid)
    query = update.message.text.strip()

    from services.package_service import search
    rows = search(query)

    if not rows:
        await update.message.reply_text(
            t("search_empty", lang, query=query),
            parse_mode="Markdown"
        )
        ctx.user_data.pop("action", None)
        return

    await update.message.reply_text(
        t("search_header", lang, query=query),
        parse_mode="Markdown"
    )

    for pkg, rest in rows:
        from utils.helpers import get_pickup_status
        from services import review_service
        status  = get_pickup_status(pkg.pickup_from, pkg.pickup_to, lang)
        rating  = review_service.get_rating(rest.id)
        reviews = review_service.get_review_count(rest.id)
        is_fav  = favorite_service.is_favorite(uid, rest.id)

        text = t("package_card", lang,
                 rest=rest.name, address=rest.address, district=rest.district,
                 rating=rating, reviews=reviews, name=pkg.name,
                 price=pkg.price, qty=pkg.quantity, status=status,
                 from_=pkg.pickup_from, to=pkg.pickup_to)

        buttons = [
            [InlineKeyboardButton(t("btn_reserve", lang, price=pkg.price),
                                  callback_data=f"reserve_{pkg.id}")],
            [InlineKeyboardButton(
                "❤️ В избранном" if is_fav else "🤍 В избранное",
                callback_data=f"fav_{rest.id}"
            )],
        ]
        if rest.latitude and rest.longitude:
            map_url = f"https://maps.google.com/?q={rest.latitude},{rest.longitude}"
            buttons.append([InlineKeyboardButton(t("btn_open_map", lang), url=map_url)])

        kb = InlineKeyboardMarkup(buttons)
        photo = pkg.photo_file_id or rest.photo_file_id
        if photo:
            await ctx.bot.send_photo(uid, photo, caption=text,
                                     parse_mode="Markdown", reply_markup=kb)
        else:
            await ctx.bot.send_message(uid, text, parse_mode="Markdown", reply_markup=kb)

    ctx.user_data.pop("action", None)