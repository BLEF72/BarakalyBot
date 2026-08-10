from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from texts import t, DISTRICTS


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O'zbek",  callback_data="lang_uz"),
    ]])


def district_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons, row = [], []
    display_names = DISTRICTS[lang]
    uz_names      = DISTRICTS["uz"]

    for i, d in enumerate(display_names):
        row.append(InlineKeyboardButton(d, callback_data=f"district_{uz_names[i]}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(t("all_districts", lang), callback_data="district_ALL")])
    return InlineKeyboardMarkup(buttons)

def reserve_keyboard(lang: str, pkg_id: int, price: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_reserve", lang, price=price), callback_data=f"reserve_{pkg_id}")
    ]])


def mark_done_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Выдан / Berildi", callback_data=f"done_{code}")
    ]])




def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏪 Добавить заведение",  callback_data="admin_add_rest")],
        [InlineKeyboardButton("📋 Все заведения",        callback_data="admin_list_rests")],
        [InlineKeyboardButton("📦 Все пакеты",           callback_data="admin_list_pkgs")],
        [InlineKeyboardButton("🧾 Последние заказы",     callback_data="admin_list_orders")],
        [InlineKeyboardButton("📊 Аналитика",            callback_data="admin_analytics")],
        [InlineKeyboardButton("📊 Отчёты по заведениям", callback_data="admin_reports")],
    ])


def district_select_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Для выбора района при добавлении заведения (admin)"""
    buttons, row = [], []
    display_names = DISTRICTS[lang]
    uz_names      = DISTRICTS["uz"]
    for i, d in enumerate(display_names):
        row.append(InlineKeyboardButton(d, callback_data=f"adistrict_{uz_names[i]}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def favorite_keyboard(lang: str, restaurant_id: int, is_fav: bool) -> InlineKeyboardMarkup:

    icon  = "❤️" if is_fav else "🤍"
    label = (
        ("Убрать из избранного" if is_fav else "В избранное")
        if lang == "ru" else
        ("Sevimlilardan olib tashlash" if is_fav else "Sevimlilarga qo'shish")
    )
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{icon} {label}", callback_data=f"fav_{restaurant_id}")
    ]])


def favorites_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    label = "⭐ Мои избранные" if lang == "ru" else "⭐ Sevimlilarim"
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(label, callback_data="show_favorites")
    ]])
    
def select_restaurant_keyboard(restaurants) -> InlineKeyboardMarkup:
    """Выбор заведения при добавлении пакета"""
    buttons = []
    for rest in restaurants:
        buttons.append([InlineKeyboardButton(
            f"🏪 {rest.name} · {rest.district}",
            callback_data=f"owner_select_rest_{rest.id}"
        )])
    return InlineKeyboardMarkup(buttons)

def subscribe_keyboard(lang: str, restaurant_id: int, district: str,
                       is_sub_rest: bool, is_sub_dist: bool) -> InlineKeyboardMarkup:
    rest_label = t("btn_unsubscribe_rest", lang) if is_sub_rest else t("btn_subscribe_rest", lang)
    dist_label = t("btn_unsubscribe_district", lang) if is_sub_dist else t("btn_subscribe_district", lang)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(rest_label,  callback_data=f"sub_rest_{restaurant_id}")],
        [InlineKeyboardButton(dist_label,  callback_data=f"sub_dist_{district}")],
    ])

def review_keyboard(order_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("1⭐",     callback_data=f"review_{order_code}_1"),
        InlineKeyboardButton("2⭐",   callback_data=f"review_{order_code}_2"),
        InlineKeyboardButton("3⭐", callback_data=f"review_{order_code}_3"),
        InlineKeyboardButton("4⭐",   callback_data=f"review_{order_code}_4"),
        InlineKeyboardButton("5⭐", callback_data=f"review_{order_code}_5"),
    ]])

def edit_pkg_keyboard(lang: str, pkg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_edit_price", lang), callback_data=f"editpkg_price_{pkg_id}")],
        [InlineKeyboardButton(t("btn_edit_qty",   lang), callback_data=f"editpkg_qty_{pkg_id}")],
        [InlineKeyboardButton("🕒 " + ("Изменить время" if True else ""), callback_data=f"editpkg_time_{pkg_id}")],
        [InlineKeyboardButton(t("btn_deactivate", lang), callback_data=f"editpkg_deact_ask_{pkg_id}")],
    ])

def owner_panel_keyboard(lang: str, restaurant_id: int = 0, is_closed: bool = False) -> InlineKeyboardMarkup:
    close_btn = (
        InlineKeyboardButton(t("btn_open_rest", lang),  callback_data=f"owner_open_rest_{restaurant_id}")
        if is_closed else
        InlineKeyboardButton(t("btn_close_rest", lang), callback_data=f"owner_close_rest_{restaurant_id}")
    )
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_add_pkg",      lang), callback_data=f"owner_add_pkg_{restaurant_id}")],
        [InlineKeyboardButton(t("btn_use_template", lang), callback_data=f"owner_templates_{restaurant_id}")],
        [InlineKeyboardButton(t("btn_edit_pkgs",    lang), callback_data=f"owner_edit_pkgs_{restaurant_id}")],
        [InlineKeyboardButton(t("btn_orders_today", lang), callback_data=f"owner_today_{restaurant_id}")],
        [InlineKeyboardButton(t("btn_mark_done",    lang), callback_data="owner_mark_start")],
        [InlineKeyboardButton(t("btn_update_photo", lang), callback_data=f"owner_update_photo_{restaurant_id}")],
        [close_btn],
    ])
    
def pickup_time_keyboard(lang: str, prefix: str = "pickuptime") -> InlineKeyboardMarkup:
    times = [
        "12:00-14:00", "14:00-16:00", "16:00-18:00",
        "17:00-19:00", "18:00-20:00", "18:00-21:00",
        "19:00-21:00", "19:00-22:00", "20:00-22:00", "21:00-23:00",
    ]
    custom = "✏️ Своё время" if lang == "ru" else "✏️ O'z vaqtim"
    buttons = []
    row = []
    for time in times:
        row.append(InlineKeyboardButton(time, callback_data=f"{prefix}_{time}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(custom, callback_data=f"{prefix}_custom")])
    return InlineKeyboardMarkup(buttons)


def with_cancel(lang: str, keyboard: InlineKeyboardMarkup = None) -> InlineKeyboardMarkup:
    """Добавляет кнопку отмены к существующей клавиатуре (или создаёт новую из одной кнопки)"""
    cancel_row = [InlineKeyboardButton(t("btn_flow_cancel", lang), callback_data="flow_cancel")]
    rows = list(keyboard.inline_keyboard) if keyboard else []
    rows.append(cancel_row)
    return InlineKeyboardMarkup(rows)