from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

def get_button_texts(language: str):
    """
    Возвращает переводы текстов кнопок
    """
    button_texts = {
        'ru': {
            'get_id': 'Получить 🆔',
            'reviews': 'Отзывы🥇',
            'prev_page': '⬅',
            'next_page': '➡',
            'leave_review': 'Оставить отзыв🗣',
            'deals_done': 'Сделок проведено🔄',
            'support': 'Поддержка🧑‍💻',
            'yes': 'Да',
            'no': 'Нет',
            'transferred': 'Передал',
            'confirm_deal': 'Подтвердить сделку',
            'back': '<<Назад',
            'faq': 'FAQ📃',
            'about_us': 'О нас👨‍👩‍👦',
            'personal_account': 'Личный кабинет👤',
            'seller': 'Я продавец🙋‍♂️',
            'buyer': 'Я покупатель💁‍♂',
            'cancel': 'Отменить',
            'history': 'Просмотреть историю💾',
            'change_prefs': 'Изменить язык/валюту🔧',
            'menu': 'Меню',
            'top_up_balance': 'Пополнить баланс💰',
            'stars': 'Звезды✨',
            'withdraw_funds': 'Вывод средств💸',
            'withdraw_cryptobot': 'CryptoBot 🤖',
            'terms': 'Пользовательское соглашение 📜',
            'withdraw_eth': 'ETH ⛓'
        },
        'en': {
            'get_id': 'Get 🆔',
            'reviews': 'Reviews🥇',
            'leave_review': 'Leave a review🗣',
            'deals_done': 'Deals completed🔄',
            'prev_page': '⬅',
            'next_page': '➡',
            'support': 'Support🧑‍💻',
            'yes': 'Yes',
            'no': 'No',
            'transferred': 'Transferred',
            'confirm_deal': 'Confirm deal',
            'back': '<<Back',
            'faq': 'FAQ📃',
            'about_us': 'About us👨‍👩‍👦',
            'personal_account': 'Personal account👤',
            'seller': 'I am a seller🙋‍♂️',
            'buyer': 'I am a buyer💁‍♂',
            'cancel': 'Cancel',
            'history': 'View history💾',
            'change_prefs': 'Change language/currency🔧',
            'menu': 'Menu',
            'top_up_balance': 'Top up balance💰',
            'stars': 'Stars✨',
            'withdraw_funds': 'Withdraw funds💸',
            'withdraw_cryptobot': 'CryptoBot 🤖',
            'terms': 'Terms of Service 📜',
            'withdraw_eth': 'ETH ⛓'
        },
        'uk': {
            'get_id': 'Отримати 🆔',
            'reviews': 'Відгуки🥇',
            'leave_review': 'Залишити відгук🗣',
            'deals_done': 'Завершено угод🔄',
            'support': 'Підтримка🧑‍💻',
            'yes': 'Так',
            'no': 'Ні',
            'transferred': 'Передав',
            'confirm_deal': 'Підтвердити угоду',
            'prev_page': '⬅',
            'next_page': '➡',
            'back': '<<Назад',
            'faq': 'FAQ📃',
            'about_us': 'Про нас👨‍👩‍👦',
            'personal_account': 'Особистий кабінет👤',
            'seller': 'Я продавець🙋‍♂️',
            'buyer': 'Я покупець💁‍♂',
            'cancel': 'Скасувати',
            'history': 'Переглянути історію💾',
            'change_prefs': 'Змінити мову/валюту🔧',
            'menu': 'Меню',
            'top_up_balance': 'Поповнити баланс💰',
            'stars': 'Зірки✨',
            'withdraw_funds': 'Вивести кошти💸',
            'withdraw_cryptobot': 'CryptoBot 🤖',
            'terms': 'Угода користувача 📜',
            'withdraw_eth': 'ETH ⛓'
        }
    }
    return button_texts.get(language, button_texts['ru'])

def create_inline_button(text: str, callback_data: str):
    """Создает инлайн-кнопку"""
    return InlineKeyboardButton(text, callback_data=callback_data)

def create_keyboards(language: str):
    """
    Создает все клавиатуры с текстом на указанном языке
    """
    texts = get_button_texts(language)

    inline_button = create_inline_button(texts['get_id'], 'button1')
    inline_button_2 = create_inline_button(texts['reviews'], 'send_rev')  # Исправлено
    inline_button_3 = create_inline_button(texts['leave_review'], 'add_rev')  # Исправлено
    inline_button_4 = create_inline_button(texts['deals_done'], 'deal_count')  # Исправлено
    inline_button_5 = create_inline_button(texts['support'], 'helper_fo_users')  # Исправлено
    inline_button_6 = create_inline_button(texts['yes'], 'btn6')
    inline_button_7 = create_inline_button(texts['no'], 'btn7')
    inline_button_9 = create_inline_button(texts['transferred'], 'btn9')
    inline_button_10 = create_inline_button(texts['confirm_deal'], 'btn10')
    inline_button_13 = create_inline_button(texts['back'], 'button13')
    inline_button_16 = create_inline_button(texts['faq'], 'faq')  # Исправлено
    inline_button_17 = create_inline_button(texts['about_us'], 'about_us')
    inline_button_18 = create_inline_button(texts['personal_account'], 'personal_account')
    inline_button_19 = create_inline_button(texts['seller'], 'button17')
    inline_button_20 = create_inline_button(texts['buyer'], 'button18')
    inline_button_21 = create_inline_button(texts['back'], 'button19')
    inline_button_22 = create_inline_button(texts['cancel'], 'cancel')
    inline_button_23 = create_inline_button(texts['history'], 'transaction_history')  # Исправлено
    inline_button_24 = create_inline_button(texts['back'], 'cancel_to_personal_account')
    inline_button_25 = create_inline_button(texts['change_prefs'], 'change_preferences')  # Исправлено
    inline_button_26 = create_inline_button(texts['top_up_balance'], 'top_up_balance')
    inline_button_27 = create_inline_button(texts['stars'], 'top_up_stars')
    inline_button_29 = create_inline_button(texts['withdraw_funds'], 'withdraw_funds')
    inline_button_30 = create_inline_button(texts['withdraw_cryptobot'], 'withdraw_cryptobot')
    inline_button_31 = create_inline_button(texts['withdraw_eth'], 'withdraw_eth')
    inline_button_32 = create_inline_button(texts['terms'], 'terms')

    inline_kb1 = InlineKeyboardMarkup().add(inline_button).add(inline_button_21)
    inline_kb2 = InlineKeyboardMarkup().add(inline_button_2, inline_button_3).add(inline_button_4).add(inline_button_5, inline_button_16).add(inline_button_23, inline_button_32).add(inline_button_21)
    inline_kb3 = InlineKeyboardMarkup().insert(inline_button_6).insert(inline_button_7)
    inline_kb5 = InlineKeyboardMarkup().add(inline_button_9)
    inline_kb6 = InlineKeyboardMarkup().add(inline_button_10)
    inline_kb9 = InlineKeyboardMarkup().add(inline_button_13)
    yes_or_no_2 = InlineKeyboardMarkup().add(inline_button_19, inline_button_20).add(inline_button_18).add(inline_button_17)
    back_main_menu = InlineKeyboardMarkup().add(inline_button_23).add(inline_button_21)
    cancel_button = InlineKeyboardMarkup().add(inline_button_22)
    back_to_personal_account = InlineKeyboardMarkup().add(inline_button_24)
    personal_account_menu = InlineKeyboardMarkup().add(inline_button_23).add(inline_button_25).add(inline_button_26).add(inline_button_29).add(inline_button_21)
    top_up_methods = InlineKeyboardMarkup().add(inline_button_27).add(inline_button_24)
    withdraw_methods = InlineKeyboardMarkup().add(inline_button_30, inline_button_31).add(inline_button_24)

    return {
        'inline_kb1': inline_kb1,
        'inline_kb2': inline_kb2,
        'inline_kb3': inline_kb3,
        'inline_kb5': inline_kb5,
        'inline_kb6': inline_kb6,
        'inline_kb9': inline_kb9,
        'yes_or_no_2': yes_or_no_2,
        'back_main_menu': back_main_menu,
        'cancel_button': cancel_button,
        'back_to_personal_account': back_to_personal_account,
        'personal_account_menu': personal_account_menu,
        'top_up_methods': top_up_methods,
        'withdraw_methods': withdraw_methods
    }

def keyboard(language: str):
    """
    Создает обычную клавиатуру с кнопкой "Меню"
    """
    texts = get_button_texts(language)
    return ReplyKeyboardMarkup(resize_keyboard=True).add(texts['menu'])

def language_choice_keyboard():
    """
    Клавиатура для выбора языка
    """
    return InlineKeyboardMarkup(row_width=3).add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")
    )

def currency_choice_keyboard():
    """
    Клавиатура для выбора валюты
    """
    return InlineKeyboardMarkup(row_width=3).add(
        InlineKeyboardButton("💵 USD", callback_data="cur_usd"),
        InlineKeyboardButton("💴 RUB", callback_data="cur_rub"),
        InlineKeyboardButton("💶 UAH", callback_data="cur_uah")
    )
