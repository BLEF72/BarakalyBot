from telegram import ReplyKeyboardMarkup, KeyboardButton
from texts import t


def main_keyboard(lang: str) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(t("btn_packages", lang)), KeyboardButton(t("btn_myorders", lang))],
        [KeyboardButton(t("btn_favorites", lang)), KeyboardButton(t("btn_my_subscriptions", lang))],
        [KeyboardButton(t("btn_search", lang)), KeyboardButton(t("btn_top", lang))],
        [KeyboardButton(t("btn_support", lang)), KeyboardButton(t("btn_help", lang))],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)