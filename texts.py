DISTRICTS = {
    "uz": ["Chilonzor", "Yunusobod", "Mirzo Ulugbek",
           "Shayxontokhur", "Yakkasaroy", "Olmazor",
           "Uchtepa", "Sergeli", "Bektemir", "Mirobod", "Xamza"],

    "ru": ["Чиланзар", "Юнусабад", "Мирзо Улугбек",
           "Шайхантахур", "Яккасарай", "Алмазар",
           "Учтепа", "Сергели", "Бектемир", "Мирабад", "Хамза"]
}


# ── Всё тексты бота ─────────────────────────────────────────────────────────
TX = {

    # Старт / язык
    "choose_lang": {
        "ru": "Здравствуйте! 👋\nВыберите язык / Tilni tanlang:",
        "uz": "Assalomu alekom! 👋\nTilni tanlang / Выберите язык:"
    },
    "welcome": {
        "ru": (
            "Добро пожаловать в Barakaly! 🍱\n\n"
            "Покупайте свежую еду со скидкой 50–70%.\n"
            "Кафе и пекарни продают остатки дня — дёшево и вкусно!\n\n"
            "Используйте кнопки ниже 👇"
        ),
        "uz": (
            "Barakaly ga xush kelibsiz! 🍱\n\n"
            "Mahsulotlarni 50–70% chegirma bilan sotib oling.\n"
            "Kafe va nonvoyxonalarning kunlik qoldiqlari sotiladi!\n\n"
            "Quyidagi tugmalardan foydalaning 👇"
        )
    },

    # Главное меню (ReplyKeyboard)
    "btn_packages":  {"ru": "🛍 Пакеты",       "uz": "🛍 Paketlar"},
    "btn_myorders":  {"ru": "📋 Мои заказы",   "uz": "📋 Buyurtmalarim"},
    "btn_help":      {"ru": "ℹ️ Помощь",        "uz": "ℹ️ Yordam"},

    # Выбор района
    "choose_district": {
        "ru": "📍 Выберите район Ташкента:",
        "uz": "📍 Toshkent tumanini tanlang:"
    },
    "all_districts": {"ru": "🗺 Все районы", "uz": "🗺 Barcha tumanlar"},

    # Пакеты
    "no_packages": {
        "ru": "😔 В этом районе сейчас нет пакетов.\n\nЗагляните позже или выберите другой район!",
        "uz": "😔 Bu tumanda hozir paketlar yo'q.\n\nKeyinroq qarab ko'ring yoki boshqa tumanni tanlang!"
    },
    "package_card": {
    "ru": "🏪 *{rest}*\n📍 {address} · {district}\n⭐ {rating} ({reviews} отзывов)\n\n🛍 *{name}*\n💰 *{price:,} сум*\n📦 Осталось: {qty} шт.\n🕒 Забрать: {from_} – {to}\n{status}",
    "uz": "🏪 *{rest}*\n📍 {address} · {district}\n⭐ {rating} ({reviews} ta sharh)\n\n🛍 *{name}*\n💰 *{price:,} so'm*\n📦 Qoldi: {qty} ta\n🕒 Olish vaqti: {from_} – {to}\n{status}"
},
    "btn_reserve": {
        "ru": "✅ Забронировать за {price:,} сум",
        "uz": "✅ {price:,} so'mga bron qilish"
    },

    # Бронирование
    "already_taken": {
        "ru": "😔 Этот пакет только что закончился!",
        "uz": "😔 Bu paket hozirgina tugadi!"
    },
"reserve_confirm": {
    "ru": (
        "🎉 *Забронировано!*\n\n"
        "🔑 Ваш код: `{code}`\n"
        "🏪 {rest}\n"
        "📍 {address}\n"
        "🕒 Забрать: {from_} – {to}\n"
        "💵 Оплата: *наличными при получении*\n\n"
        "⏳ Бронь действует до *{until}*.\n"
        "Если не придёте во время,бронь снимается автоматически."
    ),
    "uz": (
        "🎉 *Bron qilindi!*\n\n"
        "🔑 Sizning kodingiz: `{code}`\n"
        "🏪 {rest}\n"
        "📍 {address}\n"
        "🕒 Olish vaqti: {from_} – {to}\n"
        "💵 To'lov: *kelganda naqd*\n\n"
        "⏳ Bron *{until}* gacha amal qiladi.\n"
        "Vaqtida Kelmasangiz, bron avtomatik tarzda bekor qilinadi."
    )
},
    "reservation_expired": {
        "ru": "⏰ Бронь `{code}` истекла и отменена. Пакет снова доступен.",
        "uz": "⏰ `{code}` broni muddati o'tdi va bekor qilindi."
    },
"pickup_closed": {
    "ru": "😔 Окно выдачи уже закрылось.",
    "uz": "😔 Yetkazib berish oynasi allaqachon yopilgan."
},

    # Мои заказы
    "my_orders_empty": {
        "ru": "У вас пока нет заказов 🛍\nНажмите *Пакеты* чтобы найти что-нибудь вкусное!",
        "uz": "Hali sizning buyurtmalaringiz yo'q 🛍\n*Paketlar* tugmasini bosing!"
    },
    "my_orders_header": {
        "ru": "📋 *Ваши последние заказы:*\n\n",
        "uz": "📋 *Sizning oxirgi buyurtmalaringiz:*\n\n"
    },
    "order_status": {
        "reserved":  {"ru": "⏳ Забронировано", "uz": "⏳ Bron qilingan"},
        "active":    {"ru": "✅ Подтверждён",   "uz": "✅ Tasdiqlangan"},
        "used":      {"ru": "🎉 Выдан",          "uz": "🎉 Berilgan"},
        "cancelled": {"ru": "❌ Отменён",        "uz": "❌ Bekor qilingan"},
    },

    # Помощь
    "help": {
        "ru": (
            "ℹ️ *Как это работает:*\n\n"
            "1️⃣ Выберите район\n"
            "2️⃣ Посмотрите доступные пакеты\n"
            "3️⃣ Забронируйте (бронь 1 час)\n"
            "4️⃣ Приходите и покажите код\n"
            "5️⃣ Заплатите наличными и заберите еду 🎉\n\n"
            "📌 Пакеты забираются в день заказа!\n"
            "📌 Бронь автоматически снимается если не прийти вовремя."
        ),
        "uz": (
            "ℹ️ *Qanday ishlaydi:*\n\n"
            "1️⃣ Tumanni tanlang\n"
            "2️⃣ Mavjud paketlardan birini tanlang\n"
            "3️⃣ Bron qiling (1 soat)\n"
            "4️⃣ Kelib, kodni ko'rsating\n"
            "5️⃣ To'lov qiling va paketingizni oling 🎉\n\n"
            "📌 Paketlar buyurtma kuni olinadi!\n"
            "📌 O'z vaqtida kelmasa bron avtomatik bekor qilinadi."
        )
    },

    # Панель владельца
    "owner_welcome": {
        "ru": "🏪 *Панель владельца*\n\nЧто хочешь сделать?",
        "uz": "🏪 *Egasi paneli*\n\nNima qilmoqchisiz?"
    },
    "btn_add_pkg":    {"ru": "➕ Добавить пакет",     "uz": "➕ Paket qo'shish"},
    "btn_my_pkgs":    {"ru": "📦 Мои пакеты",         "uz": "📦 Mening paketlarim"},
    "btn_orders_today": {"ru": "🧾 Заказы сегодня",   "uz": "🧾 Bugungi buyurtmalar"},
    "btn_mark_done":  {"ru": "✅ Отметить выданным",  "uz": "✅ Berildi deb belgilash"},

    # Добавление пакета
    "ask_pkg_name": {
        "ru": "📝 Шаг 1/4: Название пакета\n_(например: Выпечка дня, Сюрприз-пакет)_",
        "uz": "📝 1/4-qadam: Paket nomi\n_(masalan: Kunlik non, Surpriz-paket)_"
    },
    "ask_pkg_photo": {
        "ru": "📸 Шаг 2/4: Отправьте фото пакета\n_(Фото сильно увеличивают продажи!)_",
        "uz": "📸 2/4-qadam: Paket rasmini yuboring\n_(Rasm sotuvni oshiradi!)_"
    },
    "ask_pkg_price": {
        "ru": "💰 Шаг 3/4: Цена в сумах\n_(только цифры, например: 15000)_",
        "uz": "💰 3/4-qadam: Narx so'mda\n_(faqat raqam, masalan: 15000)_"
    },
    "ask_pkg_qty": {
        "ru": "📦 Шаг 4/5: Количество пакетов\n_(только цифры, например: 5)_",
        "uz": "📦 4/5-qadam: Paketlar soni\n_(faqat raqam, masalan: 5)_"
    },
    "ask_pkg_time": {
        "ru": "🕒 Шаг 5/5: Выберите время выдачи",
        "uz": "🕒 5/5-qadam: Olish vaqtini tanlang"
    },
    "pkg_added": {
        "ru": "✅ Пакет опубликован в боте! Покупатели уже видят его 🎉",
        "uz": "✅ Paket botga joylandi! Xaridorlar uni ko'radi 🎉"
    },
    "invalid_time": {
        "ru": "❌ Неверный формат. Напиши например: 18:00-19:00",
        "uz": "❌ Noto'g'ri format. Masalan: 18:00-19:00"
    },
    "invalid_number": {
        "ru": "❌ Введи только цифры.",
        "uz": "❌ Faqat raqam kiriting."
    },

    # Отметить выданным
    "ask_order_code": {
        "ru": "Введи код заказа (например: UZ-ABC123):",
        "uz": "Buyurtma kodini kiriting (masalan: UZ-ABC123):"
    },
    "order_marked_done": {
        "ru": "✅ Заказ `{code}` выдан! (@{username})",
        "uz": "✅ `{code}` buyurtmasi berildi! (@{username})"
    },
    "order_already_done": {
        "ru": "ℹ️ Этот заказ уже выдан.",
        "uz": "ℹ️ Bu buyurtma allaqachon berilgan."
    },
    "order_not_found": {
        "ru": "❌ Заказ не найден.",
        "uz": "❌ Buyurtma topilmadi."
    },
    "order_done_buyer": {
        "ru": "✅ Ваш заказ `{code}` выдан. Приятного аппетита! 🎉",
        "uz": "✅ Sizning `{code}` buyurtmangiz berildi. Yoqimli ishtaha! 🎉"
    },

    # Ошибки
    "no_access": {"ru": "⛔ Нет доступа.", "uz": "⛔ Ruxsat yo'q."},
    "cancelled":  {"ru": "❌ Отменено.",   "uz": "❌ Bekor qilindi."},

    # Админ
"admin_stats": {
    "ru": (
        "📊 *Статистика Barakly*\n\n"
        "🏪 Заведений: {rests}\n"
        "📦 Активных пакетов: {pkgs}\n"
        "🛍 Заказов всего: {orders}\n"
        "✅ Выдано: {done}\n"
        "👥 Пользователей: {users}\n"
        "💰 Комиссия платформы: {commission:,} сум"
    ),
        "uz": (
            "📊 *Statistika:*\n"
            "🏪 Muassasalar: {rests}\n"
            "📦 Paketlar (faol): {pkgs}\n"
            "🧾 Jami buyurtmalar: {orders}\n"
            "✅ Berilgan: {done}\n"
            "👥 Foydalanuvchilar: {users}\n"
            "💰 Komissiya: {commission:,}som"
        )
    },
    "admin_add_rest_name":    {"ru": "🏪 Шаг 1/6: Название заведения:",            "uz": "🏪 1/6-qadam: Muassasa nomi:"},
"admin_add_rest_address": {"ru": "📍 Шаг 2/6: Адрес:",                         "uz": "📍 2/6-qadam: Manzil:"},
"ask_rest_location":      {"ru": "📍 Шаг 3/6: Отправь геолокацию заведения\n_(Нажми скрепку → Location)_", "uz": "📍 3/6-qadam: Muassasa joylashuvini yuboring\n_(Qisqich tugmasini bosing → Location)_"},
"admin_add_rest_district":{"ru": "🗺 Шаг 4/6: Выбери район:",                  "uz": "🗺 4/6-qadam: Tumanni tanlang:"},
"admin_add_rest_owner":   {"ru": "👤 Шаг 5/6: Telegram ID владельца\n(или 0 если владелец — ты):", "uz": "👤 5/6-qadam: Egasining Telegram ID\n(yoki 0 agar siz bo'lsangiz):"},
"ask_rest_photo":         {"ru": "📸 Шаг 6/6: Отправь фото заведения:\n_(Показывается если у пакета нет своего фото)_", "uz": "📸 6/6-qadam: Muassasa rasmini yuboring:\n_(Paketda o'z rasmi bo'lmasa ko'rinadi)_"},
    "rest_added": {
        "ru": "✅ Заведение *{name}* добавлено!\nВладелец (ID {owner}) может использовать /mypanel",
        "uz": "✅ *{name}* muassasasi qo'shildi!\nEgasi (ID {owner}) /mypanel dan foydalanishi mumkin"
    },
    
    #Избранное
    "btn_favorites":{
        "ru": "⭐ Избранное",
        "uz": "⭐ Sevimlilar"
    },
    "favorites_empty":{
        "ru": "⭐ У вас пока нет избранного.\nНажмите на ❤️ в карточках пакетов, чтобы добавить!",
        "uz": "⭐ Hali sevimlilaringiz yo'q.\nPaket kartalarındaki ❤️ tugmasini bosing!"
    },
    "favorites_header":{
        "ru": "⭐ *Ваши избранные заведения:*\n\n",
        "uz": "⭐ *Sizning sevimli muassasalarınız:*\n\n"
    },
    "added_to_favorites":{
        "ru": "✅ Заведение добавлено в избранное",
        "uz": "✅ Muassasa sevimlilarga qo'shildi"
    },
    "removed_from_favorites": {
    "ru": "🤍 Убрано из избранного.",
    "uz": "🤍 Sevimlilardan olib tashlandi."
},
    
"btn_subscribe_rest": {
    "ru": "🔔 Подписаться на заведение",
    "uz": "🔔 Muassasaga obuna bo'lish"
},
"btn_unsubscribe_rest": {
    "ru": "🔕 Отписаться от заведения",
    "uz": "🔕 Muassasadan obunani bekor qilish"
},
"btn_subscribe_district": {
    "ru": "🔔 Подписаться на район",
    "uz": "🔔 Tumanga obuna bo'lish"
},
"btn_unsubscribe_district": {
    "ru": "🔕 Отписаться от района",
    "uz": "🔕 Tumandan obunani bekor qilish"
},
"btn_my_subscriptions": {
    "ru": "🔔 Мои подписки",
    "uz": "🔔 Obunalarim"
},
"subscribed_rest": {
    "ru": "🔔 Вы подписались на *{name}*!\nПришлём уведомление когда появятся новые пакеты.",
    "uz": "🔔 *{name}* ga obuna bo'ldingiz!\nYangi paketlar paydo bo'lganda xabar beramiz."
},
"unsubscribed_rest": {
    "ru": "🔕 Вы отписались от *{name}*.",
    "uz": "🔕 *{name}* dan obunangiz bekor qilindi."
},
"subscribed_district": {
    "ru": "🔔 Вы подписались на район *{district}*!\nПришлём уведомление когда появятся новые пакеты.",
    "uz": "🔔 *{district}* tumaniga obuna bo'ldingiz!\nYangi paketlar paydo bo'lganda xabar beramiz."
},
"unsubscribed_district": {
    "ru": "🔕 Вы отписались от района *{district}*.",
    "uz": "🔕 *{district}* tumanidan obunangiz bekor qilindi."
},
"my_subscriptions_empty": {
    "ru": "У вас пока нет подписок.\n\nПодпишитесь на район или заведение чтобы получать уведомления о новых пакетах!",
    "uz": "Hozircha obunalaringiz yo'q.\n\nYangi paketlar haqida xabar olish uchun tuman yoki muassasaga obuna bo'ling!"
},
"my_subscriptions_header": {
    "ru": "🔔 *Ваши подписки:*\n\n",
    "uz": "🔔 *Obunalaringiz:*\n\n"
},
"my_subs_restaurants_header": {
    "ru": "🏪 *Заведения*",
    "uz": "🏪 *Muassasalar*"
},
"my_subs_districts_header": {
    "ru": "📍 *Районы*",
    "uz": "📍 *Tumanlar*"
},
"subs_has_packages": {
    "ru": "🟢 Сейчас есть пакетов: {count}",
    "uz": "🟢 Hozir paketlar bor: {count}"
},
"subs_no_packages": {
    "ru": "⚪️ Сейчас нет доступных пакетов",
    "uz": "⚪️ Hozir paket yo'q"
},
"btn_view_packages": {
    "ru": "👀 Смотреть",
    "uz": "👀 Ko'rish"
},
"btn_unsubscribe": {
    "ru": "🔕 Отписаться",
    "uz": "🔕 Obunani bekor qilish"
},
"new_pkg_notify": {
    "ru": "🆕 *Новый пакет в {rest}!*\n\n🛍 {name}\n💰 {price:,} сум\n📦 Осталось: {qty} шт.\n🕒 Забрать: {from_} – {to}\n\n📍 {address}",
    "uz": "🆕 *{rest} da yangi paket!*\n\n🛍 {name}\n💰 {price:,} so'm\n📦 Qoldi: {qty} ta\n🕒 Olish vaqti: {from_} – {to}\n\n📍 {address}"
},
"btn_cancel_order": {
    "ru": "❌ Отменить бронь",
    "uz": "❌ Bronni bekor qilish"
},
"order_cancelled_buyer": {
    "ru": "❌ Бронь `{code}` отменена.",
    "uz": "❌ `{code}` broni bekor qilindi."
},
"order_cancelled_owner": {
    "ru": "❌ Покупатель отменил бронь `{code}`\n🛍 {pkg_name}",
    "uz": "❌ Xaridor `{code}` bronini bekor qildi\n🛍 {pkg_name}"
},
"order_was_cancelled": {
    "ru": "❌ Этот заказ был отменён покупателем.",
    "uz": "❌ Bu buyurtma xaridor tomonidan bekor qilingan."
},
"order_cancel_too_late": {
    "ru": "⚠️ Нельзя отменить — заказ уже выдан.",
    "uz": "⚠️ Bekor qilib bo'lmaydi — buyurtma allaqachon berilgan."
},
"review_request": {
    "ru": "⭐ Как вам заказ в *{rest}*?\nОцените пожалуйста:",
    "uz": "⭐ *{rest}* dagi buyurtmangizni qanday baholaysiz?\nIltimos baholang:"
},
"review_thanks": {
    "ru": "🙏 Спасибо за оценку! Ваш отзыв помогает другим покупателям",
    "uz": "🙏 Baholaginiz uchun rahmat! Sizning bahoyingiz boshqa xaridorlarga yordam beradi."
},
"review_already": {
    "ru": "Вы уже оценили этот заказ.",
    "uz": "Siz bu buyurtmani allaqachon baholagansiz."
},
"btn_rebook": {
    "ru": "🔄 Забронировать снова",
    "uz": "🔄 Qayta bron qilish"
},
"rebook_unavailable": {
    "ru": "😔 К сожалению этот пакет сейчас недоступен.",
    "uz": "😔 Afsuski bu paket hozir mavjud emas."
},
"btn_edit_pkgs": {
    "ru": "✏️ Управление пакетами",
    "uz": "✏️ Paketlarni boshqarish"
},
"edit_pkg_header": {
    "ru": "Выбери пакет для редактирования:",
    "uz": "O'zgartirish uchun paketni tanlang:"
},
"btn_edit_price": {
    "ru": "💰 Изменить цену",
    "uz": "💰 Narxni o'zgartirish"
},
"btn_edit_qty": {
    "ru": "📦 Изменить количество",
    "uz": "📦 Miqdorni o'zgartirish"
},
"btn_deactivate": {
    "ru": "🚫 Снять с бота",
    "uz": "🚫 Botdan o'chirish"
},
"ask_new_price": {
    "ru": "💰 Новая цена в сумах (только цифры):",
    "uz": "💰 Yangi narx so'mda (faqat raqam):"
},
"ask_new_qty": {
    "ru": "📦 Новое количество (только цифры):",
    "uz": "📦 Yangi miqdor (faqat raqam):"
},
"pkg_updated": {
    "ru": "✅ Пакет обновлён!",
    "uz": "✅ Paket yangilandi!"
},
"pkg_deactivated": {
    "ru": "🚫 Пакет снят с бота.",
    "uz": "🚫 Paket botdan o'chirildi."
},
"weekly_report": {
    "ru": (
        "📊 *Еженедельный отчёт — {rest}*\n\n"
        "🗓 За прошлую неделю:\n"
        "  📦 Заказов: {orders}\n"
        "  ✅ Выдано: {done}\n"
        "  ❌ Отменено: {cancelled}\n"
        "  👻 Не пришли: {no_show}\n"
        "  💰 Выручка: {revenue:,} сум\n"
        "  ⭐ Рейтинг: {rating}\n\n"
        "📈 За всё время:\n"
        "  📦 Всего заказов: {total}\n"
        "  💰 Общая выручка: {total_revenue:,} сум"
    ),
    "uz": (
        "📊 *Haftalik hisobot — {rest}*\n\n"
        "🗓 O'tgan hafta:\n"
        "  📦 Buyurtmalar: {orders}\n"
        "  ✅ Berilgan: {done}\n"
        "  ❌ Bekor qilingan: {cancelled}\n"
        "  👻 Kelmadi: {no_show}\n"
        "  💰 Daromad: {revenue:,} so'm\n"
        "  ⭐ Reyting: {rating}\n\n"
        "📈 Jami:\n"    
        "  📦 Jami buyurtmalar: {total}\n"
        "  💰 Umumiy daromad: {total_revenue:,} so'm"
    ),
},
"btn_reports": {
    "ru": "📊 Отчёты по заведениям",
    "uz": "📊 Muassasalar bo'yicha hisobotlar"
},
"choose_rest_report": {
    "ru": "Выберите заведение для отчёта:",
    "uz": "Hisobot uchun muassasani tanlang:"
},
"btn_support": {
    "ru": "💬 Поддержка",
    "uz": "💬 Qo'llab-quvvatlash"
},
"support_ask": {
    "ru": "💬 Напишите своё сообщение — мы ответим в ближайшее время:",
    "uz": "💬 Xabaringizni yozing — tez orada javob beramiz:"
},
"support_sent": {
    "ru": "✅ Сообщение отправлено! Мы ответим вам в ближайшее время.",
    "uz": "✅ Xabar yuborildi! Tez orada javob beramiz."
},
"support_msg_to_admin": {
    "ru": "💬 *Сообщение от пользователя:*\n\n👤 @{username} (ID: {uid})\n\n{text}",
    "uz": "💬 *Foydalanuvchidan xabar:*\n\n👤 @{username} (ID: {uid})\n\n{text}"
},
"support_reply_sent": {
    "ru": "✅ Ответ отправлен пользователю.",
    "uz": "✅ Foydalanuvchiga javob yuborildi."
},
"support_reply_to_user": {
    "ru": "💬 *Ответ от поддержки:*\n\n{text}",
    "uz": "💬 *Qo'llab-quvvatlashdan javob:*\n\n{text}"
},
"support_cancel": {
    "ru": "❌ Отменить",
    "uz": "❌ Bekor qilish"
},
"pickup_reminder": {
    "ru": "⏰ Напоминание!\n\nВаша бронь `{code}` в *{rest}* истекает в *{until}*.\n📍 {address}\n\nНе забудьте забрать заказ!",
    "uz": "⏰ Eslatma!\n\n`{code}` Sizning bronizingiz *{rest}* da *{until}* da tugaydi.\n📍 {address}\n\nBuyurtmangizni olishni unutmang!"
},
"btn_save_template": {
    "ru": "💾 Сохранить как шаблон",
    "uz": "💾 Shablon sifatida saqlash"
},
"btn_use_template": {
    "ru": "📋 Использовать шаблон",
    "uz": "📋 Shablondan foydalanish"
},
"template_saved": {
    "ru": "✅ Шаблон сохранён! Теперь можете использовать его при добавлении новых пакетов.",
    "uz": "✅ Shablon saqlandi! Endi yangi paketlar qo'shishda undan foydalanishingiz mumkin."
},
"choose_template": {
    "ru": "📋 Выберите шаблон:",
    "uz": "📋 Shablonni tanlang:"
},
"no_templates": {
    "ru": "У вас пока нет шаблонов. Сохраните пакет как шаблон!",
    "uz": "Hali shablonlaringiz yo'q. Paketni shablon sifatida qo'shing!"
},
"ask_template_qty": {
    "ru": "📦 Сколько пакетов добавить? (только цифры)",
    "uz": "📦 Nechta paket qo'shamiz? (faqat raqam)"
},
"template_pkg_added": {
    "ru": "✅ Пакет добавлен из шаблона!",
    "uz": "✅ Shablondan paket qo'shildi!"
},
"max_reservations": {
    "ru": "⚠️ У вас уже 2 активные брони. Заберите их прежде чем бронировать новый пакет.",
    "uz": "⚠️ Sizda allaqachon 2 ta faol bron bor. Yangi paket bron qilishdan oldin ularni olishingiz kerak."
},
"user_limited": {
    "ru": "⚠️ У вас высокий процент отмен. Вам доступна только 1 активная бронь.",
    "uz": "⚠️ Sizda bekor qilishlar foizi yuqori. Sizga faqat 1 ta faol bron ruxsat etiladi."
},
"user_blocked": {
    "ru": "🚫 Вы временно заблокированы из-за неявок за забронированными заказами. Осталось дней: {days}.",
    "uz": "🚫 Bron qilingan buyurtmalarga kelmaganingiz sababli vaqtincha bloklangansiz. Qolgan kunlar: {days}."
},
"cancel_warning": {
    "ru": (
        "⚠️ *Внимание!*\n\n"
        "Частые отмены влияют на ваш рейтинг:\n"
        "• Если отмените более 50% брони, некторое время будет очраничен количество брони.\n"
        "• Если отмените более 80% брони, временная блокировка на 24 часа\n\n"
        "Вы уверены что хотите отменить бронь `{code}`?"
    ),
    "uz": (
        "⚠️ *Diqqat!*\n\n"
        "Ketma-ket bekor qilish reytingingizga ta'sir qiladi:\n"
        "• Agar 50% dan ortiq bronlarni bekor qilsangiz, biroz vaqtga bron qilish imkoniyati cheklanadi.\n"
        "• Agar 80% dan ortiq bronlarni bekor qilsangiz, 24 soatlik vaqtinchalik bloklanasiz\n\n"
        "`{code}` bronini bekor qilishni xohlaysizmi?"
    ),
},
"btn_confirm_cancel": {
    "ru": "✅ Да, отменить",
    "uz": "✅ Ha, bekor qilish"
},
"btn_keep_order": {
    "ru": "❌ Нет, оставить",
    "uz": "❌ Yo'q, qoldirish"
},
"user_limited_warning": {
    "ru": "⚠️ *Внимание!*\n\nВаш процент отмен превысил 50%.\nТеперь вам доступна только *1 активная бронь* одновременно.\n\nПостарайтесь приходить за забронированными пакетами!",
    "uz": "⚠️ *Diqqat!*\n\nBekor qilishlar foizingiz 50% dan oshdi.\nEndi sizga faqat *1 ta faol bron* ruxsat etiladi.\n\nBron qilgan paketlaringizni olishga harakat qiling!"
},
"user_blocked_warning": {
    "ru": "🚫 *Внимание!*\n\nВаш процент отмен превысил 80%.\nВы *заблокированы на 24 часа*.\n\nПосле блокировки старайтесь не отменять брони без причины.",
    "uz": "🚫 *Diqqat!*\n\nBekor qilishlar foizingiz 80% dan oshdi.\nSiz *24 soatga bloklangansiz*.\n\nBlokdan keyin sababsiz bronlarni bekor qilmang."
},
"user_unblocked": {
    "ru": "✅ Ваша блокировка снята! Теперь вы снова можете бронировать пакеты.",
    "uz": "✅ Blokingiz olib tashlandi! Endi yana paketlarni bron qilishingiz mumkin."
},
"btn_skip_photo": {
    "ru": "⏭ Пропустить (использовать фото заведения)",
    "uz": "⏭ O'tkazish (muassasa rasmini ishlatish)"
},
"ask_rest_photo": {
    "ru": "📸 Отправьте фото заведения:\n_(Показывается если у пакета нет своего фото)_",
    "uz": "📸 Muassasa rasmini yuboring:\n_(Paketning o'z rasmi bo'lmasa)_"
},
"btn_skip_rest_photo": {
    "ru": "⏭ Пропустить",
    "uz": "⏭ O'tkazish"
},
"rest_photo_saved": {
    "ru": "✅ Фото заведения сохранено!",
    "uz": "✅ Muassasa rasmi saqlandi!"
},
"channel_post": {
    "ru": (
        "🆕 *Новый пакет!*\n\n"
        "🏪 {rest}\n"
        "📍 {address} · {district}\n"
        "⭐ {rating}\n\n"
        "🛍 *{name}*\n"
        "💰 *{price:,} сум*\n"
        "📦 Осталось: {qty} шт.\n"
        "🕒 Забрать: {from_} – {to}\n\n"
        "👉 @Baraka77bot — забронируй прямо сейчас!"
    ),
    "uz": (
        "🆕 *Yangi paket!*\n\n"
        "🏪 {rest}\n"
        "📍 {address} · {district}\n"
        "⭐ {rating}\n\n"
        "🛍 *{name}*\n"
        "💰 *{price:,} so'm*\n"
        "📦 Qoldi: {qty} ta\n"
        "🕒 Olish vaqti: {from_} – {to}\n\n"
        "👉 @Baraka77bot — hoziroq bron qiling!"
    ),
},
"btn_top": {
    "ru": "🏆 Топ заведений",
    "uz": "🏆 Top muassasalar"
},
"top_header": {
    "ru": "🏆 *Топ заведений Barakly:*\n\n",
    "uz": "🏆 *Barakly top muassasalari:*\n\n"
},
"top_item": {
    "ru": "{pos}. 🏪 *{name}* · {district}\n    {rating} · 📦 {orders} заказов\n\n",
    "uz": "{pos}. 🏪 *{name}* · {district}\n    {rating} · 📦 {orders} ta buyurtma\n\n"
},
"top_empty": {
    "ru": "Пока нет данных для рейтинга.",
    "uz": "Hali reyting uchun ma'lumot yo'q."
},
"ask_rest_location": {
    "ru": "📍 Шаг 3/6: Отправь геолокацию заведения\n_(Нажми скрепку → Location)_",
    "uz": "📍 3/6-qadam: Muassasa joylashuvini yuboring\n_(Qisqich tugmasini bosing → Location)_"
},
"btn_skip_location": {
    "ru": "⏭ Пропустить",
    "uz": "⏭ O'tkazish"
},
"btn_open_map": {
    "ru": "📍 Открыть на карте",
    "uz": "📍 Xaritada ochish"
},
"ask_pkg_time_custom": {
    "ru": "✏️ Напишите время в формате: 18:00-21:00",
    "uz": "✏️ Vaqtni shu formatda yozing: 18:00-21:00"
},
"time_opens_in": {
    "ru": "⏳ Откроется через {hours}ч {mins}мин",
    "uz": "⏳ {hours}s {mins}d dan keyin ochiladi"
},
"time_open_now": {
    "ru": "🟢 Сейчас можно забирать! До {to}",
    "uz": "🟢 Hozir olib ketish mumkin! {to} gacha"
},
"time_opens_soon": {
    "ru": "🔜 Откроется через {mins} мин",
    "uz": "🔜 {mins} daqiqada ochiladi"
},
"btn_update_photo": {
    "ru": "📸 Обновить фото заведения",
    "uz": "📸 Muassasa rasmini yangilash"
},
"ask_new_rest_photo": {
    "ru": "📸 Отправьте новое фото заведения:",
    "uz": "📸 Muassasaning yangi rasmini yuboring:"
},
"rest_photo_updated": {
    "ru": "✅ Фото заведения обновлено!",
    "uz": "✅ Muassasa rasmi yangilandi!"
},
"btn_search": {
    "ru": "🔍 Поиск",
    "uz": "🔍 Qidiruv"
},
"search_ask": {
    "ru": "🔍 Введи название пакета или заведения:",
    "uz": "🔍 Paket yoki muassasa nomini kiriting:"
},
"search_empty": {
    "ru": "😔 Ничего не найдено по запросу *{query}*",
    "uz": "😔 *{query}* bo'yicha hech narsa topilmadi"
},
"search_header": {
    "ru": "🔍 Результаты по запросу *{query}*:\n\n",
    "uz": "🔍 *{query}* bo'yicha natijalar:\n\n"
},
"btn_edit_time": {
    "ru": "🕒 Изменить время выдачи",
    "uz": "🕒 Olish vaqtini o'zgartirish"
},
"pkg_time_updated": {
    "ru": "✅ Время выдачи обновлено!",
    "uz": "✅ Olish vaqti yangilandi!"
},
"btn_close_rest": {
    "ru": "🔴 Закрыть заведение на сегодня",
    "uz": "🔴 Muassasani bugunga yopish"
},
"btn_open_rest": {
    "ru": "🟢 Открыть заведение",
    "uz": "🟢 Muassasani ochish"
},
"rest_closed": {
    "ru": "🔴 Заведение закрыто до завтра. Все пакеты деактивированы.",
    "uz": "🔴 Muassasa ertaga ochiladi. Barcha paketlar deaktiv qilindi."
},
"rest_opened": {
    "ru": "🟢 Заведение открыто! Пакеты снова доступны.",
    "uz": "🟢 Muassasa ochildi! Paketlar yana mavjud."
},
"order_not_yours": {
    "ru": "❌ Этот заказ принадлежит другому заведению.",
    "uz": "❌ Bu buyurtma boshqa muassasaga tegishli."
},
"order_expired_no_show": {
    "ru": "⌛ Время брони истекло, покупатель не пришёл вовремя, отметить выданным нельзя.",
    "uz": "⌛ Bu bron muddati tugagan, xaridor o'z vaqtida kelmadi, 'Berildi' deb belgilab bo'lmaydi."
},
"btn_flow_cancel": {
    "ru": "❌ Отмена",
    "uz": "❌ Bekor qilish"
},
"must_be_positive": {
    "ru": "❌ Число должно быть больше нуля.",
    "uz": "❌ Raqam noldan katta bo'lishi kerak."
},
"confirm_deactivate": {
    "ru": "⚠️ Деактивировать этот пакет? Пакет нельзя будет включить обратно вручную",
    "uz": "⚠️ Bu paketni faolsizlantirasizmi? Paketni qayta yoqib bo'lmaydi"
},
"btn_confirm_deactivate": {
    "ru": "✅ Да, деактивировать",
    "uz": "✅ Ha, faolsizlantirish"
},
}


def md_escape(text) -> str:
    """Экранирует спецсимволы старого Markdown в данных из БД
    (названия заведений, адреса и т.п.), чтобы они не ломали parse_mode=Markdown"""
    if text is None:
        return ""
    text = str(text)
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


def t(key: str, lang: str, **kwargs) -> str:
    """Получить текст по ключу и языку"""
    entry = TX.get(key, {})
    text  = entry.get(lang) or entry.get("ru") or "???"
    if kwargs:
        safe_kwargs = {
            k: md_escape(v) if isinstance(v, str) else v
            for k, v in kwargs.items()
        }
        return text.format(**safe_kwargs)
    return text


def status_label(status: str, lang: str) -> str:
    return TX["order_status"].get(status, {}).get(lang, status)
