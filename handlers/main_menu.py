from aiogram.utils import executor
from loader import dp
from loguru import logger
import asyncio
import os
import re 
import aiohttp
from datetime import datetime
from utils import keyboards
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from utils import sqliter
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.keyboards import get_button_texts
from telegram.error import BadRequest

logger.add('logger.log', format='{time} {level} {message}', level='ERROR')

load_dotenv()
new_sql = sqliter.Sqlite(os.path.abspath(os.path.join('bot_garant.db')))
ROOT_ADMIN_ID = int(os.getenv('ROOT_ADMIN_ID'))
CRYPTOBOT_API_KEY = os.getenv('CRYPTOBOT_API_KEY')
CRYPTOBOT_TESTNET_URL = os.getenv('CRYPTOBOT_TESTNET_URL')
class UserPreferences(StatesGroup):
    waiting_for_language = State()
    waiting_for_currency = State()
    change_language = State()
    change_currency = State()

class PaySeller(StatesGroup):
    waiting_for_seller_id = State()
    waiting_for_amount = State()

class Feedback(StatesGroup):
    waite_feedback = State()
    waite_stars = State()
    view_reviews = State()

class WaiteMes(StatesGroup):
    waite_person_mes = State()

class TopUpBalance(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_payment = State()

class WithdrawFunds(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()
    waiting_for_address = State()

async def main_menu(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    new_sql.user_in_bd(person_id)
    
    user_prefs = new_sql.get_user_preferences(person_id)
    if user_prefs and user_prefs.get('language') and user_prefs.get('currency'):
        await show_main_menu(message, person_id)
    else:
        await message.answer(
            {'ru': "Пожалуйста, выберите язык:", 'en': "Please select a language:", 'uk': "Будь ласка, виберіть мову:"}.get(
                user_prefs.get('language', 'ru'), "Пожалуйста, выберите язык:"
            ),
            reply_markup=keyboards.language_choice_keyboard()
        )
        await UserPreferences.waiting_for_language.set()

async def show_main_menu(message: types.Message, person_id: str):
    user_prefs = new_sql.get_user_preferences(person_id)
    language = user_prefs.get('language', 'ru')
    
    greetings = {
        'ru': f'🛡{hbold("Привет,", message.from_user.first_name, "!")}'
              f' Я-бот, который поможет провести безопасно сделку между продавцом и покупателем \n\n'
              f'🤔{hbold("Как мною пользоваться?")}\n\n'
              f'📝Выбирай один пункт ниже на клавиатуре и следуй инструкциям бота. Если возникнут проблемы '
              f'касаемо бота, ты всегда можешь написать поддержке в разделе "О нас"\n\n'
              f'Приятного пользования!✌️',
        'en': f'🛡{hbold("Hello,", message.from_user.first_name, "!")}'
              f' I am a bot that will help to conduct a safe transaction between the seller and the buyer\n\n'
              f'🤔{hbold("How to use me?")}\n\n'
              f'📝Choose one option below on the keyboard and follow the bot’s instructions. If you have any issues '
              f'regarding the bot, you can always contact support in the "About Us" section\n\n'
              f'Enjoy using!✌️',
        'uk': f'🛡{hbold("Привіт,", message.from_user.first_name, "!")}'
              f' Я-бот, який допоможе провести безпечно угоду між продавцем та покупцем\n\n'
              f'🤔{hbold("Як мною користуватися?")}\n\n'
              f'📝Обирай один пункт нижче на клавіатурі та дотримуйся інструкцій бота. Якщо виникнуть проблеми '
              f'з ботом, ти завжди можеш звернутися до підтримки в розділі "Про нас"\n\n'
              f'Приємного користування!✌️'
    }
    
    await message.answer(greetings.get(language, greetings['ru']), reply_markup=keyboards.keyboard(language))
    await message.answer(
        {'ru': 'Главное меню⤵️', 'en': 'Main menu⤵️', 'uk': 'Головне меню⤵️'}.get(language, 'Главное меню⤵️'),
        reply_markup=keyboards.create_keyboards(language)['yes_or_no_2']
    )

async def process_language_selection(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = callback_query.data.replace('lang_', '')
    if language in ['ru', 'en', 'uk']:
        new_sql.save_user_language(person_id, language)
        language_prompts = {
            'ru': "Теперь выберите валюту:",
            'en': "Now select a currency:",
            'uk': "Тепер виберіть валюту:"
        }
        await callback_query.message.edit_text(
            language_prompts.get(language, "Теперь выберите валюту:"),
            reply_markup=keyboards.currency_choice_keyboard()
        )
        await UserPreferences.waiting_for_currency.set()
    else:
        await callback_query.message.edit_text(
            {'ru': "Неверный выбор языка. Пожалуйста, выберите язык:",
             'en': "Invalid language choice. Please select a language:",
             'uk': "Невірний вибір мови. Будь ласка, виберіть мову:"}.get(
                new_sql.get_user_preferences(person_id).get('language', 'ru'), "Неверный выбор языка. Пожалуйста, выберите язык:"
            ),
            reply_markup=keyboards.language_choice_keyboard()
        )

async def process_currency_selection(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    currency = callback_query.data.replace('cur_', '').upper()
    if currency in ['UAH', 'RUB', 'USD']:
        new_sql.save_user_currency(person_id, currency)
        language = new_sql.get_user_preferences(person_id).get('language', 'ru')
        await callback_query.message.edit_text(
            {'ru': "Настройки сохранены!", 'en': "Settings saved!", 'uk': "Налаштування збережено!"}.get(language, "Настройки сохранены!")
        )
        await show_main_menu(callback_query.message, person_id)
        await state.finish()
    else:
        await callback_query.message.edit_text(
            {'ru': "Неверный выбор валюты. Пожалуйста, выберите валюту:",
             'en': "Invalid currency choice. Please select a currency:",
             'uk': "Невірний вибір валюти. Будь ласка, виберіть валюту:"}.get(
                new_sql.get_user_preferences(person_id).get('language', 'ru'), "Неверный выбор валюты. Пожалуйста, выберите валюту:"
            ),
            reply_markup=keyboards.currency_choice_keyboard()
        )

async def change_preferences(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    await callback_query.message.edit_text(
        {'ru': "Выберите язык:", 'en': "Select a language:", 'uk': "Виберіть мову:"}.get(language, "Выберите язык:"),
        reply_markup=keyboards.language_choice_keyboard()
    )
    await UserPreferences.change_language.set()

async def process_change_language(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = callback_query.data.replace('lang_', '')
    if language in ['ru', 'en', 'uk']:
        new_sql.save_user_language(person_id, language)
        await callback_query.message.edit_text(
            {'ru': "Теперь выберите валюту:", 'en': "Now select a currency:", 'uk': "Тепер виберіть валюту:"}.get(
                language, "Теперь выберите валюту:"
            ),
            reply_markup=keyboards.currency_choice_keyboard()
        )
        await UserPreferences.change_currency.set()
    else:
        await callback_query.message.edit_text(
            {'ru': "Неверный выбор языка. Пожалуйста, выберите язык:",
             'en': "Invalid language choice. Please select a language:",
             'uk': "Невірний вибір мови. Будь ласка, виберіть мову:"}.get(
                new_sql.get_user_preferences(person_id).get('language', 'ru'), "Неверный выбор языка. Пожалуйста, выберите язык:"
            ),
            reply_markup=keyboards.language_choice_keyboard()
        )

async def process_change_currency(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    currency = callback_query.data.replace('cur_', '').upper()
    if currency in ['UAH', 'RUB', 'USD']:
        new_sql.save_user_currency(person_id, currency)
        language = new_sql.get_user_preferences(person_id).get('language', 'ru')
        await callback_query.message.edit_text(
            {'ru': "Настройки обновлены!", 'en': "Settings updated!", 'uk': "Налаштування оновлено!"}.get(language, "Настройки обновлены!")
        )
        await personal_account(callback_query)
        await state.finish()
    else:
        await callback_query.message.edit_text(
            {'ru': "Неверный выбор валюты. Пожалуйста, выберите валюту:",
             'en': "Invalid currency choice. Please select a currency:",
             'uk': "Невірний вибір валюти. Будь ласка, виберіть валюту:"}.get(
                new_sql.get_user_preferences(person_id).get('language', 'ru'), "Неверный выбор валюты. Пожалуйста, выберите валюту:"
            ),
            reply_markup=keyboards.currency_choice_keyboard()
        )

async def main_menu_message_reply(message: types.Message):
    person_id = str(message.from_user.id)
    await show_main_menu(message, person_id)

async def back_to_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    
    user_data = await state.get_data()
    invoice_message_id = user_data.get('invoice_message_id')
    
    if invoice_message_id:
        try:
            await callback_query.message.bot.delete_message(
                chat_id=person_id,
                message_id=invoice_message_id
            )
            logger.info(f"Удалено сообщение с инвойсом {invoice_message_id} для пользователя {person_id} (button19)")
        except Exception as e:
            logger.warning(f"Не удалось удалить инвойс {invoice_message_id} для {person_id}: {e}")
    
    try:
        await callback_query.message.answer(
            {'ru': 'Главное меню⤵️', 'en': 'Main menu⤵️', 'uk': 'Головне меню⤵️'}.get(
                language, 'Главное меню⤵️'
            ),
            reply_markup=kb['yes_or_no_2']
        )
        await callback_query.message.delete()
        logger.info(f"Пользователь {person_id} вернулся в главное меню (button19)")
        await state.finish()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при возврате в меню. Попробуйте снова.',
             'en': 'Error returning to menu. Try again.',
             'uk': 'Помилка при поверненні до меню. Спробуйте ще раз.'}.get(language),
            reply_markup=kb['yes_or_no_2']
        )
        await state.finish()
        await callback_query.answer()

async def personal_account(callback_query: types.CallbackQuery):
    try:
        person_id = str(callback_query.from_user.id)
        information = new_sql.get_all_information(person_id)
        user_prefs = new_sql.get_user_preferences(person_id)
        language = user_prefs.get('language', 'ru')
        currency = user_prefs.get('currency', 'USD')
        
        personal_account_texts = {
            'ru': f'{hbold("🙋Добро пожаловать в личный кабинет!")}\n'
                  f'Твой 🆔: {person_id}\n\n'
                  f'♾{hbold("Совершено сделок")}: {information[1]}\n'
                  f'🤑{hbold("Продано на")}: {information[2]:.2f} {currency}\n'
                  f'💰{hbold("Куплено на")}: {information[0]:.2f} {currency}\n'
                  f'💵{hbold("Баланс")}: {information[3]:.2f} {currency}',
            'en': f'{hbold("🙋Welcome to your personal account!")}\n'
                  f'Your 🆔: {person_id}\n\n'
                  f'♾{hbold("Completed deals")}: {information[1]}\n'
                  f'🤑{hbold("Sold for")}: {information[2]:.2f} {currency}\n'
                  f'💰{hbold("Bought for")}: {information[0]:.2f} {currency}\n'
                  f'💵{hbold("Balance")}: {information[3]:.2f} {currency}',
            'uk': f'{hbold("🙋Ласкаво просимо до особистого кабінету!")}\n'
                  f'Твій 🆔: {person_id}\n\n'
                  f'♾{hbold("Завершено угод")}: {information[1]}\n'
                  f'🤑{hbold("Продано на")}: {information[2]:.2f} {currency}\n'
                  f'💰{hbold("Куплено на")}: {information[0]:.2f} {currency}\n'
                  f'💵{hbold("Баланс")}: {information[3]:.2f} {currency}'
        }
        
        await callback_query.message.answer(
            personal_account_texts.get(language, personal_account_texts['ru']),
            reply_markup=keyboards.create_keyboards(language)['personal_account_menu']
        )
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as exc:
        logger.error(f'Ошибка в personal_account: {exc}')
        language = new_sql.get_user_preferences(str(callback_query.from_user.id)).get('language', 'ru')
        await callback_query.message.answer(
            {'ru': "Ой, возникла какая-то ошибка, мы скоро ее починим!",
             'en': "Oops, something went wrong, we'll fix it soon!",
             'uk': "Ой, виникла якась помилка, ми скоро її виправимо!"}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.answer()

async def top_up_balance_start(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    
    try:
        current_state = await state.get_state()
        logger.debug(f"Текущее состояние для {person_id}: {current_state}")
        await state.finish()  # Сбрасываем текущее состояние для надежности
        logger.debug(f"Состояние сброшено для {person_id}")
        
        await callback_query.message.answer(
            {'ru': 'Выберите способ пополнения:', 
             'en': 'Select payment method:', 
             'uk': 'Виберіть спосіб поповнення:'}.get(language),
            reply_markup=kb['top_up_methods']
        )
        logger.debug(f"Отправлена клавиатура top_up_methods для {person_id}")
        
        await asyncio.sleep(0.2)  # Задержка 200 мс перед удалением
        try:
            await callback_query.message.delete()
            logger.debug(f"Исходное сообщение удалено для {person_id}")
        except Exception as delete_error:
            logger.warning(f"Не удалось удалить сообщение для {person_id}: {delete_error}")
        
        await TopUpBalance.waiting_for_method.set()
        logger.info(f"Пользователь {person_id} перешел к выбору способа пополнения, state: TopUpBalance.waiting_for_method")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при отображении способов пополнения для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        try:
            await callback_query.message.answer(
                {'ru': f'Ошибка при выборе способа пополнения: {str(e)}. Нажмите "Назад" для возврата.',
                 'en': f'Error selecting payment method: {str(e)}. Click "Back" to return.',
                 'uk': f'Помилка при виборі способу поповнення: {str(e)}. Натисніть "Назад" для повернення.'}.get(language),
                reply_markup=error_kb
            )
        except Exception as answer_error:
            logger.error(f"Не удалось отправить сообщение об ошибке для {person_id}: {answer_error}")
        await state.finish()
        await callback_query.answer()

async def withdraw_funds_start(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
    kb = keyboards.create_keyboards(language)
    
    try:
        balance = new_sql.get_balance(person_id)
        messages = {
            'ru': f'Введите сумму для вывода (Учтите мы берем комиссию на вывод 1.5%) (в {currency}, минимум 0.01, доступно: {balance:.2f} {currency}):',
            'en': f'Enter the amount to withdraw (Please note that we charge a 1.5% withdrawal fee.) (in {currency}, minimum 0.01, available: {balance:.2f} {currency}):',
            'uk': f'Введіть суму для виведення (Враховуйте, ми беремо комісію на виведення 1.5%) (в {currency}, мінімум 0.01, доступно: {balance:.2f} {currency}):'
        }
        await callback_query.message.answer(messages.get(language, messages['ru']), reply_markup=kb['cancel_button'])
        await callback_query.message.delete()
        logger.info(f"Пользователь {person_id} перешел к вводу суммы для вывода, state: WithdrawFunds.waiting_for_amount")
        await WithdrawFunds.waiting_for_amount.set()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе суммы вывода для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await callback_query.message.answer(
            {'ru': 'Ошибка при вводе суммы вывода. Нажмите "Назад" для возврата.',
             'en': 'Error entering withdrawal amount. Click "Back" to return.',
             'uk': 'Помилка при введенні суми виведення. Натисніть "Назад" для повернення.'}.get(language),
            reply_markup=error_kb
        )
        await state.finish()
        await callback_query.answer()

async def process_withdraw_amount(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
    kb = keyboards.create_keyboards(language)
    
    if message.text.startswith('/') or message.text in ['Меню', 'Menu', 'Меню']:
        await message.answer(
            {'ru': f'Пожалуйста, введите сумму цифрами (не менее 0.01 {currency}).',
             'en': f'Please enter the amount in digits (at least 0.01 {currency}).',
             'uk': f'Будь ласка, введіть суму цифрами (не менше 0.01 {currency}).'}
            .get(language),
            reply_markup=kb['cancel_button']
        )
        return
    
    try:
        amount = float(message.text)
        if amount < 0.01:
            raise ValueError(f"Сумма должна быть не менее 0.01 {currency}")
        
        amount_usd = new_sql.convert_currency(amount, currency, 'USD')
        if not new_sql.check_balance(person_id, amount_usd):
            raise ValueError(f"Недостаточно средств! Доступно: {new_sql.get_balance(person_id):.2f} USD")
        
        await state.update_data(withdraw_amount=amount, withdraw_amount_usd=amount_usd)
        messages = {
            'ru': 'Выберите способ вывода:',
            'en': 'Select withdrawal method:',
            'uk': 'Виберіть спосіб виведення:'
        }
        await message.answer(messages.get(language, messages['ru']), reply_markup=kb['withdraw_methods'])
        await WithdrawFunds.waiting_for_method.set()
        
    except ValueError as e:
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': f'Ошибка: {str(e)}. Введите сумму цифрами, не менее 0.01 {currency}!',
             'en': f'Error: {str(e)}. Enter the amount in digits, at least 0.01 {currency}!',
             'uk': f'Помилка: {str(e)}. Введіть суму цифрами, не менше 0.01 {currency}!'}.get(language),
            reply_markup=error_kb
        )

async def process_withdraw_method(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
    texts = keyboards.get_button_texts(language)
    kb = keyboards.create_keyboards(language)
    method = callback_query.data
    
    user_data = await state.get_data()
    amount = user_data.get('withdraw_amount')  # Сумма в валюте пользователя
    amount_usd = user_data.get('withdraw_amount_usd')  # Сумма в USD
    
    try:
        if method == 'withdraw_cryptobot':
            # Проверяем баланс
            if not new_sql.check_balance(person_id, amount_usd):
                raise ValueError({
                    'ru': 'Недостаточно средств на балансе',
                    'en': 'Insufficient funds in balance',
                    'uk': 'Недостатньо коштів на балансі'
                }.get(language))
            
            # Применяем комиссию 1.5%
            commission_rate = 0.015  # 1.5%
            amount_usd_after_commission = amount_usd * (1 - commission_rate)
            
            # Предполагаем, что 1 USD = 1 USDT (для простоты)
            usdt_amount = amount_usd_after_commission
            
            if usdt_amount < 0.01:  # Минимальная сумма для USDT
                raise ValueError({
                    'ru': 'Сумма слишком мала для вывода через CryptoBot (мин. 0.01 USDT)',
                    'en': 'Amount is too small for withdrawal via CryptoBot (min. 0.01 USDT)',
                    'uk': 'Сума замала для виведення через CryptoBot (мін. 0.01 USDT)'
                }.get(language))
            
            # Списываем деньги с баланса
            new_sql.conn.execute("BEGIN TRANSACTION")
            try:
                new_sql.deduct_balance(person_id, amount_usd)
                new_balance = new_sql.get_balance(person_id)
                
                # Создаём чек в CryptoBot
                async with aiohttp.ClientSession() as session:
                    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY}
                    payload = {
                        "asset": "USDT",  # Используем USDT
                        "amount": f"{usdt_amount:.2f}",  # Сумма после комиссии
                        "description": f"Withdrawal for user {person_id} ({amount:.2f} {currency}, {usdt_amount:.2f} USDT after 1.5% commission)"
                    }
                    logger.info(f"Отправка запроса в CryptoBot: URL={CRYPTOBOT_TESTNET_URL}/createCheck, payload={payload}, headers={headers}")
                    async with session.post(f"{CRYPTOBOT_TESTNET_URL}/createCheck", json=payload, headers=headers) as response:
                        response_text = await response.text()
                        logger.info(f"Ответ от CryptoBot: status={response.status}, text={response_text}")
                        if response.status != 200:
                            logger.error(f"Ошибка API CryptoBot для {person_id}: {response_text}")
                            new_sql.conn.rollback()
                            raise Exception({
                                'ru': f'Ошибка создания чека в CryptoBot: {response_text}',
                                'en': f'Error creating CryptoBot check: {response_text}',
                                'uk': f'Помилка створення чека в CryptoBot: {response_text}'
                            }.get(language))
                        data = await response.json()
                        if not data.get("ok"):
                            logger.error(f"Ошибка API CryptoBot: {data.get('error', 'Unknown error')}")
                            new_sql.conn.rollback()
                            raise Exception({
                                'ru': f'Ошибка создания чека: {data.get("error", "Unknown error")}',
                                'en': f'Error creating check: {data.get("error", "Unknown error")}',
                                'uk': f'Помилка створення чека: {data.get("error", "Unknown error")}'
                            }.get(language))
                        
                        check_url = data["result"]["bot_check_url"]
                        check_id = data["result"]["check_id"]
                
                # Сохраняем информацию о чеке и транзакции в базе данных
                history = {
                    'ru': f"Вывод через CryptoBot: {amount:.2f} {currency} ({usdt_amount:.2f} USDT после 1.5% комиссии, чек ID: {check_id})",
                    'en': f"Withdrawal via CryptoBot: {amount:.2f} {currency} ({usdt_amount:.2f} USDT after 1.5% commission, check ID: {check_id})",
                    'uk': f"Виведення через CryptoBot: {amount:.2f} {currency} ({usdt_amount:.2f} USDT після 1.5% комісії, чек ID: {check_id})"
                }.get(language)
                new_sql.add_history(history, person_id)
                new_sql.save_pending_withdrawal(person_id, check_id, amount_usd, usdt_amount)
                new_sql.conn.commit()
                
                logger.info(f"Чек создан и баланс списан для {person_id}: {amount:.2f} {currency} ({usdt_amount:.2f} USDT), check_id: {check_id}, новый баланс: {new_balance:.2f} USD")
                
                back_button = InlineKeyboardButton(
                    texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
                    callback_data='cancel_to_personal_account'
                )
                check_status_button = InlineKeyboardButton(
                    texts.get(language, {'check_invoice_status': 'Проверить статус чека 🔍'}).get('check_invoice_status', 'Проверить статус чека 🔍'),
                    callback_data='check_invoice_status'
                )
                success_kb = InlineKeyboardMarkup().add(back_button, check_status_button)
                await callback_query.message.answer(
                    {
                        'ru': f'Чек на {usdt_amount:.2f} USDT успешно создан в CryptoBot!\n'
                              f'Активируйте чек, чтобы получить средства: {check_url}\n'
                              f'Сумма с учётом комиссии 1.5%: {usdt_amount:.2f} USDT (из {amount:.2f} {currency}).\n'
                              f'ID чека: {check_id}\n'
                              f'Списано с баланса: {amount_usd:.2f} USD. Новый баланс: {new_balance:.2f} USD.',
                        'en': f'Check for {usdt_amount:.2f} USDT successfully created in CryptoBot!\n'
                              f'Activate the check to receive funds: {check_url}\n'
                              f'Amount after 1.5% commission: {usdt_amount:.2f} USDT (from {amount:.2f} {currency}).\n'
                              f'Check ID: {check_id}\n'
                              f'Deducted from balance: {amount_usd:.2f} USD. New balance: {new_balance:.2f} USD.',
                        'uk': f'Чек на {usdt_amount:.2f} USDT успішно створено в CryptoBot!\n'
                              f'Активуйте чек, щоб отримати кошти: {check_url}\n'
                              f'Сума після 1.5% комісії: {usdt_amount:.2f} USDT (з {amount:.2f} {currency}).\n'
                              f'ID чека: {check_id}\n'
                              f'Списано з балансу: {amount_usd:.2f} USD. Новий баланс: {new_balance:.2f} USD.'
                    }.get(language),
                    reply_markup=success_kb
                )
                await callback_query.message.delete()
                await state.finish()
                await callback_query.answer()
            
            except Exception as e:
                new_sql.conn.rollback()
                logger.error(f'Ошибка в создании чека или списании баланса для {person_id}: {e}')
                raise
        
        elif method == 'withdraw_eth':
            messages = {
                'ru': 'Введите адрес ETH кошелька для вывода (начинается с 0x, 42 символа):',
                'en': 'Enter the ETH wallet address for withdrawal (starts with 0x, 42 characters):',
                'uk': 'Введіть адресу ETH гаманця для виведення (починається з 0x, 42 символи):'
            }
            await callback_query.message.answer(messages.get(language, messages['ru']), reply_markup=kb['cancel_button'])
            await callback_query.message.delete()
            await WithdrawFunds.waiting_for_address.set()
            await callback_query.answer()
        
        else:
            raise ValueError({
                'ru': 'Неверный метод вывода',
                'en': 'Invalid withdrawal method',
                'uk': 'Невірний метод виведення'
            }.get(language))
            
    except Exception as e:
        logger.error(f"Ошибка при обработке метода вывода для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await callback_query.message.answer(
            {
                'ru': f'Ошибка при выборе метода вывода: {str(e)}. Попробуйте снова или используйте /paysupport.',
                'en': f'Error selecting withdrawal method: {str(e)}. Try again or use /paysupport.',
                'uk': f'Помилка при виборі методу виведення: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'
            }.get(language, f'Ошибка при выборе метода вывода: {str(e)}. Попробуйте снова или используйте /paysupport.'),
            reply_markup=error_kb
        )
        await callback_query.message.delete()
        await state.finish()
        await callback_query.answer()

async def process_eth_address(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
    texts = keyboards.get_button_texts(language)
    kb = keyboards.create_keyboards(language)
    eth_address = message.text.strip()
    
    try:
        # Проверяем формат адреса ETH (начинается с 0x, 42 символа, шестнадцатеричный)
        if not re.match(r'^0x[a-fA-F0-9]{40}$', eth_address):
            raise ValueError({
                'ru': 'Неверный формат адреса ETH. Адрес должен начинаться с 0x и содержать 42 символа.',
                'en': 'Invalid ETH address format. Address must start with 0x and contain 42 characters.',
                'uk': 'Невірний формат адреси ETH. Адреса повинна починатися з 0x і містити 42 символи.'
            }.get(language))
        
        user_data = await state.get_data()
        amount = user_data.get('withdraw_amount')  # Сумма в валюте пользователя
        amount_usd = user_data.get('withdraw_amount_usd')  # Сумма в USD
        
        # Применяем комиссию 1.5%
        commission_rate = 0.015  # 1.5%
        amount_usd_after_commission = amount_usd * (1 - commission_rate)
        amount_after_commission = new_sql.convert_currency(amount_usd_after_commission, 'USD', currency)
        
        # Проверяем баланс
        if not new_sql.check_balance(person_id, amount_usd):
            raise ValueError({
                'ru': 'Недостаточно средств на балансе',
                'en': 'Insufficient funds in balance',
                'uk': 'Недостатньо коштів на балансі'
            }.get(language))
        
        # Списываем деньги
        new_sql.conn.execute("BEGIN TRANSACTION")
        try:
            new_sql.deduct_balance(person_id, amount_usd)
            new_balance = new_sql.get_balance(person_id)
            history = {
                'ru': f"Заявка на вывод ETH: {amount_after_commission:.2f} {currency} ({amount_usd_after_commission:.2f} USD после 1.5% комиссии) на адрес {eth_address}",
                'en': f"ETH withdrawal request: {amount_after_commission:.2f} {currency} ({amount_usd_after_commission:.2f} USD after 1.5% commission) to address {eth_address}",
                'uk': f"Заявка на виведення ETH: {amount_after_commission:.2f} {currency} ({amount_usd_after_commission:.2f} USD після 1.5% комісії) на адресу {eth_address}"
            }.get(language)
            new_sql.add_history(history, person_id)
            new_sql.conn.commit()
            
            logger.info(f"Заявка на вывод ETH для {person_id}: {amount_usd_after_commission:.2f} USD после комиссии, адрес {eth_address}")
            
            back_button = InlineKeyboardButton(
                texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
                callback_data='button19'  # Возвращает в главное меню (inline_kb1)
            )
            success_kb = InlineKeyboardMarkup().add(back_button)
            await message.answer(
                {
                    'ru': f'Вы подали заявку на вывод {amount_after_commission:.2f} {currency} ({amount_usd_after_commission:.2f} USD после 1.5% комиссии) на адрес {eth_address}.\n'
                          f'Ожидайте в течение 20 минут.\n'
                          f'Новый баланс: {new_balance:.2f} USD.',
                    'en': f'You submitted a withdrawal request for {amount_after_commission:.2f} {currency} ({amount_usd_after_commission:.2f} USD after 1.5% commission) to address {eth_address}.\n'
                          f'Please wait up to 20 minutes.\n'
                          f'New balance: {new_balance:.2f} USD.',
                    'uk': f'Ви подали заявку на виведення {amount_after_commission:.2f} {currency} ({amount_usd_after_commission:.2f} USD після 1.5% комісії) на адресу {eth_address}.\n'
                          f'Очікуйте протягом 20 хвилин.\n'
                          f'Новий баланс: {new_balance:.2f} USD.'
                }.get(language),
                reply_markup=success_kb
            )
            await state.finish()
        
        except Exception as e:
            new_sql.conn.rollback()
            logger.error(f'Ошибка при обработке вывода ETH для {person_id}: {e}')
            raise
        
    except Exception as e:
        logger.error(f"Ошибка при обработке адреса ETH для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {
                'ru': f'Ошибка при вводе адреса ETH: {str(e)}. Попробуйте снова или используйте /paysupport.',
                'en': f'Error entering ETH address: {str(e)}. Try again or use /paysupport.',
                'uk': f'Помилка при введенні адреси ETH: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'
            }.get(language, f'Ошибка при вводе адреса ETH: {str(e)}. Попробуйте снова или используйте /paysupport.'),
            reply_markup=error_kb
        )
        await state.finish()

async def check_invoice_status(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    texts = keyboards.get_button_texts(language)
    kb = keyboards.create_keyboards(language)
    
    try:
        # Получаем данные о последнем ожидающем выводе
        pending_withdrawal = new_sql.get_pending_withdrawal(person_id)
        if not pending_withdrawal:
            raise ValueError({
                'ru': 'Нет ожидающих выводов',
                'en': 'No pending withdrawals',
                'uk': 'Немає очікуваних виведень'
            }.get(language))
        
        check_id = pending_withdrawal['invoice_id']  # Используем invoice_id как check_id
        amount_usd = pending_withdrawal['amount_usd']
        usdt_amount = pending_withdrawal['usdt_amount']
        
        # Проверяем статус чека через CryptoBot API
        async with aiohttp.ClientSession() as session:
            headers = {"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY}
            async with session.get(f"{CRYPTOBOT_TESTNET_URL}/getChecks?check_ids={check_id}", headers=headers) as response:
                response_text = await response.text()
                logger.info(f"Проверка статуса чека {check_id}: status={response.status}, text={response_text}")
                if response.status != 200:
                    logger.error(f"Ошибка проверки статуса чека {check_id}: {response_text}")
                    raise Exception({
                        'ru': f'Ошибка проверки статуса чека: {response_text}',
                        'en': f'Error checking check status: {response_text}',
                        'uk': f'Помилка перевірки статусу чека: {response_text}'
                    }.get(language))
                data = await response.json()
                if not data.get("ok"):
                    logger.error(f"Ошибка API CryptoBot: {data.get('error', 'Unknown error')}")
                    raise Exception({
                        'ru': f'Ошибка проверки статуса: {data.get("error", "Unknown error")}',
                        'en': f'Error checking status: {data.get("error", "Unknown error")}',
                        'uk': f'Помилка перевірки статусу: {data.get("error", "Unknown error")}'
                    }.get(language))
                
                check = data["result"]["items"][0]
                status = check.get("status")
                
                if status == "activated":
                    # Чек активирован, удаляем из ожидающих выводов
                    new_sql.conn.execute("BEGIN TRANSACTION")
                    try:
                        new_sql.remove_pending_withdrawal(person_id, check_id)
                        new_sql.conn.commit()
                        
                        logger.info(f"Чек {check_id} активирован для {person_id}")
                        
                        back_button = InlineKeyboardButton(
                            texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
                            callback_data='button19'  # Возвращает в главное меню
                        )
                        success_kb = InlineKeyboardMarkup().add(back_button)
                        await callback_query.message.answer(
                            {
                                'ru': f'Чек {check_id} успешно активирован!\n'
                                      f'Сумма: {usdt_amount:.2f} USDT.',
                                'en': f'Check {check_id} successfully activated!\n'
                                      f'Amount: {usdt_amount:.2f} USDT.',
                                'uk': f'Чек {check_id} успішно активовано!\n'
                                      f'Сума: {usdt_amount:.2f} USDT.'
                            }.get(language),
                            reply_markup=success_kb
                        )
                    except Exception as e:
                        new_sql.conn.rollback()
                        logger.error(f'Ошибка удаления ожидающего вывода для {person_id}: {e}')
                        raise
                else:
                    # Чек ещё не активирован
                    back_button = InlineKeyboardButton(
                        texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
                        callback_data='button19'  # Возвращает в главное меню
                    )
                    kb_not_activated = InlineKeyboardMarkup().add(back_button)
                    await callback_query.message.answer(
                        {
                            'ru': f'Чек {check_id} ещё не активирован. Пожалуйста, активируйте чек.',
                            'en': f'Check {check_id} is not yet activated. Please activate the check.',
                            'uk': f'Чек {check_id} ще не активовано. Будь ласка, активуйте чек.'
                        }.get(language),
                        reply_markup=kb_not_activated
                    )
                
                await callback_query.message.delete()
                await callback_query.answer()
    
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса чека для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            texts.get(language, {'back': 'Назад'}).get('back', 'Назад'),
            callback_data='button19'  # Возвращает в главное меню
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await callback_query.message.answer(
            {
                'ru': f'Ошибка при проверке статуса чека: {str(e)}. Попробуйте снова или используйте /paysupport.',
                'en': f'Error checking check status: {str(e)}. Try again or use /paysupport.',
                'uk': f'Помилка при перевірці статусу чека: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'
            }.get(language, f'Ошибка при проверке статуса чека: {str(e)}. Попробуйте снова или используйте /paysupport.'),
            reply_markup=error_kb
        )
        await callback_query.message.delete()
        await state.finish()
        await callback_query.answer()

async def top_up_stars(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    logger.debug(f"Callback top_up_stars triggered for user {person_id}, language: {language}")
    
    messages = {
        'ru': 'Введите сумму для пополнения баланса (в USD, минимум 0.02):',
        'en': 'Enter the amount to top up your balance (in USD, minimum 0.02):',
        'uk': 'Введіть суму для поповнення балансу (в USD, мінімум 0.02):'
    }
    
    try:
        await callback_query.message.answer(
            messages.get(language, messages['ru']),
            reply_markup=kb['cancel_button']
        )
        await asyncio.sleep(0.2)  # Prevent Telegram API rate limits
        try:
            await callback_query.message.delete()
            logger.debug(f"Исходное сообщение удалено для {person_id}")
        except Exception as delete_error:
            logger.warning(f"Не удалось удалить сообщение для {person_id}: {delete_error}")
        
        await TopUpBalance.waiting_for_amount.set()
        logger.info(f"Пользователь {person_id} перешел к вводу суммы для пополнения")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе суммы пополнения для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await callback_query.message.answer(
            {'ru': f'Ошибка при вводе суммы: {str(e)}. Попробуйте снова или используйте /paysupport.',
             'en': f'Error entering amount: {str(e)}. Try again or use /paysupport.',
             'uk': f'Помилка при введенні суми: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'}.get(language),
            reply_markup=error_kb
        )
        await state.finish()
        await callback_query.answer()

async def process_top_up_amount(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    
    logger.debug(f"Пользователь {person_id} ввел сумму: {message.text}")
    
    if message.text.startswith('/') or message.text in ['Меню', 'Menu', 'Меню']:
        logger.info(f"Пользователь {person_id} ввел некорректный текст: {message.text}")
        await message.answer(
            {'ru': 'Пожалуйста, введите сумму цифрами (не менее 0.02 USD).',
             'en': 'Please enter the amount in digits (at least 0.02 USD).',
             'uk': 'Будь ласка, введіть суму цифрами (не менше 0.02 USD).'}
            .get(language),
            reply_markup=kb['cancel_button']
        )
        return
    
    try:
        amount_usd = float(message.text)
        logger.debug(f"Сумма в USD: {amount_usd}")
        if amount_usd < 0.02:
            raise ValueError("Сумма должна быть не менее 0.02 USD")
        
        stars_needed = int(amount_usd / 0.02)
        logger.debug(f"Требуется звезд: {stars_needed}")
        if stars_needed < 1:
            raise ValueError("Сумма слишком мала, минимум 0.02 USD (1 звезда)")
        
        await state.update_data(amount_usd=amount_usd, stars_needed=stars_needed)
        logger.info(f"Сумма сохранена для {person_id}: {amount_usd} USD, {stars_needed} звезд")
        
        messages = {
            'ru': f'Для пополнения на {amount_usd:.2f} USD потребуется {stars_needed} Telegram Stars.\n'
                  f'Курс: 100 звезд = 2 USD.\n'
                  f'Подтвердите оплату, нажав кнопку ниже.',
            'en': f'To top up {amount_usd:.2f} USD, you need {stars_needed} Telegram Stars.\n'
                  f'Rate: 100 stars = 2 USD.\n'
                  f'Confirm payment by clicking the button below.',
            'uk': f'Для поповнення на {amount_usd:.2f} USD потрібно {stars_needed} Telegram Stars.\n'
                  f'Курс: 100 зірок = 2 USD.\n'
                  f'Підтвердіть оплату, натиснувши кнопку нижче.'
        }
        
        confirm_button = InlineKeyboardButton(
            {'ru': 'Оплатить', 'en': 'Pay', 'uk': 'Сплатити'}.get(language, 'Оплатить'),
            callback_data='confirm_top_up'
        )
        cancel_button = InlineKeyboardButton(
            {'ru': 'Отмена', 'en': 'Cancel', 'uk': 'Скасувати'}.get(language, 'Отмена'),
            callback_data='cancel_to_personal_account'
        )
        payment_kb = InlineKeyboardMarkup().add(confirm_button, cancel_button)
        
        await message.answer(messages.get(language, messages['ru']), reply_markup=payment_kb)
        await TopUpBalance.waiting_for_payment.set()
    
    except ValueError as e:
        logger.error(f"Ошибка при обработке суммы для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': f'Ошибка: {str(e)}. Введите сумму цифрами, не менее 0.02 USD!',
             'en': f'Error: {str(e)}. Enter the amount in digits, at least 0.02 USD!',
             'uk': f'Помилка: {str(e)}. Введіть суму цифрами, не менше 0.02 USD!'}.get(language),
            reply_markup=error_kb
        )

async def confirm_top_up(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    user_data = await state.get_data()
    amount_usd = user_data.get('amount_usd')
    stars_needed = user_data.get('stars_needed')
    
    logger.debug(f"Confirm top-up for {person_id}: amount_usd={amount_usd}, stars_needed={stars_needed}")
    
    if not amount_usd or not stars_needed:
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await callback_query.message.answer(
            {'ru': 'Ошибка: данные о пополнении отсутствуют. Начните заново.',
             'en': 'Error: top-up data is missing. Start again.',
             'uk': 'Помилка: дані про поповнення відсутні. Почніть заново.'}.get(language),
            reply_markup=error_kb
        )
        await state.finish()
        await callback_query.answer()
        return
    
    try:
        logger.info(f"Создание инвойса для {person_id}: amount_usd={amount_usd}, stars_needed={int(stars_needed)}")
        invoice_message = await callback_query.message.bot.send_invoice(
            chat_id=person_id,
            title={'ru': 'Пополнение баланса', 'en': 'Balance Top-Up', 'uk': 'Поповнення балансу'}.get(language),
            description={'ru': f'Пополнение на {amount_usd:.2f} USD ({int(stars_needed)} Telegram Stars)',
                         'en': f'Top up {amount_usd:.2f} USD ({int(stars_needed)} Telegram Stars)',
                         'uk': f'Поповнення на {amount_usd:.2f} USD ({int(stars_needed)} Telegram Stars)'}.get(language),
            payload=f'top_up_{person_id}_{amount_usd}_{int(datetime.now().timestamp())}',
            provider_token="",
            currency='XTR',
            prices=[LabeledPrice(label='Top Up', amount=int(stars_needed))],
            start_parameter='top-up-balance'
        )
        await state.update_data(invoice_message_id=invoice_message.message_id)
        logger.info(f"Инвойс создан для {person_id}, message_id: {invoice_message.message_id}")
        
        cancel_button = InlineKeyboardButton(
            {'ru': 'Отмена', 'en': 'Cancel', 'uk': 'Скасувати'}.get(language, 'Отмена'),
            callback_data='cancel_to_personal_account'
        )
        invoice_kb = InlineKeyboardMarkup().add(cancel_button)
        
        await callback_query.message.answer(
            {'ru': 'Пожалуйста, оплатите инвойс для пополнения баланса.',
             'en': 'Please pay the invoice to top up your balance.',
             'uk': 'Будь ласка, сплатіть інвойс для поповнення балансу.'}.get(language),
            reply_markup=invoice_kb
        )
        await callback_query.message.delete()
        await callback_query.answer()
    
    except Exception as e:
        logger.error(f"Ошибка при создании инвойса для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await callback_query.message.answer(
            {'ru': f'Ошибка при создании инвойса: {str(e)}. Попробуйте позже или используйте /paysupport.',
             'en': f'Error creating invoice: {str(e)}. Try again later or use /paysupport.',
             'uk': f'Помилка при створенні інвойсу: {str(e)}. Спробуйте пізніше або використовуйте /paysupport.'}.get(language),
            reply_markup=error_kb
        )
        await state.finish()
        await callback_query.answer()

async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext):
    person_id = str(pre_checkout_query.from_user.id)
    try:
        logger.info(f"Получен pre_checkout_query для {person_id}, ID: {pre_checkout_query.id}")
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_checkout_query.id,
            ok=True
        )
        logger.info(f"Успешно отправлен answer_pre_checkout_query для {person_id}")
    except Exception as e:
        logger.error(f'Ошибка при обработке pre_checkout_query для {person_id}: {e}')
        await pre_checkout_query.bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_checkout_query.id,
            ok=False,
            error_message=f"Ошибка обработки платежа: {str(e)}"
        )

async def process_successful_payment(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    
    try:
        logger.info(f"Получен successful_payment для {person_id}, payment_id: {message.successful_payment.telegram_payment_charge_id}")
        user_data = await state.get_data()
        amount_usd = user_data.get('amount_usd')
        
        if not amount_usd:
            logger.error(f"Ошибка: данные о пополнении отсутствуют для {person_id}")
            back_button = InlineKeyboardButton(
                {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
                callback_data='cancel_to_personal_account'
            )
            error_kb = InlineKeyboardMarkup().add(back_button)
            await message.answer(
                {'ru': 'Ошибка: данные о пополнении отсутствуют. Начните заново.',
                 'en': 'Error: top-up data is missing. Start again.',
                 'uk': 'Помилка: дані про поповнення відсутні. Почніть заново.'}.get(language),
                reply_markup=error_kb
            )
            await state.finish()
            return
        
        new_sql.conn.execute("BEGIN TRANSACTION")
        try:
            current_balance = new_sql.get_balance(person_id)
            new_sql.add_balance(person_id, amount_usd)
            new_balance = new_sql.get_balance(person_id)
            
            payment_id = message.successful_payment.telegram_payment_charge_id
            new_sql.save_payment(person_id, payment_id, amount_usd, 'XTR')
            
            history = {'ru': f"Пополнение баланса: {amount_usd:.2f} USD",
                       'en': f"Balance top-up: {amount_usd:.2f} USD",
                       'uk': f"Поповнення балансу: {amount_usd:.2f} USD"}.get(language)
            new_sql.add_history(history, person_id)
            
            new_sql.conn.commit()
            logger.info(f"Баланс обновлен для {person_id}: старый={current_balance:.2f}, новый={new_balance:.2f}, payment_id={payment_id}")
            
            back_button = InlineKeyboardButton(
                {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
                callback_data='cancel_to_personal_account'
            )
            success_kb = InlineKeyboardMarkup().add(back_button)
            
            await message.answer(
                {'ru': f'Баланс успешно пополнен на {amount_usd:.2f} USD! Новый баланс: {new_balance:.2f} USD.',
                 'en': f'Balance successfully topped up by {amount_usd:.2f} USD! New balance: {new_balance:.2f} USD.',
                 'uk': f'Баланс успішно поповнено на {amount_usd:.2f} USD! Новий баланс: {new_balance:.2f} USD.'}.get(language),
                reply_markup=success_kb
            )
            
            await state.finish()
        
        except Exception as e:
            new_sql.conn.rollback()
            logger.error(f'Ошибка в транзакции для {person_id}: {e}')
            raise
        
    except Exception as e:
        logger.error(f'Ошибка при обработке платежа для {person_id}: {e}')
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': 'Ошибка при обработке платежа. Попробуйте снова или используйте /paysupport.',
             'en': 'Error processing payment. Try again or use /paysupport.',
             'uk': 'Помилка при обробці платежу. Спробуйте ще раз або використовуйте /paysupport.'}.get(language),
            reply_markup=error_kb
        )
        await state.finish()

async def handle_pay_support(message: types.Message):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    await message.answer(
        {'ru': 'Для решения вопросов с платежами обратитесь к @YourSupportUsername или используйте /paysupport.',
         'en': 'For payment issues, please contact @YourSupportUsername or use /paysupport.',
         'uk': 'Для вирішення питань з платежами зверніться до @YourSupportUsername або використовуйте /paysupport.'}.get(language),
    )

async def pay_seller_start(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)
    
    messages = {
        'ru': 'Введите ID продавца:',
        'en': 'Enter the seller’s ID:',
        'uk': 'Введіть ID продавця:'
    }
    try:
        await callback_query.message.answer(messages.get(language, messages['ru']), reply_markup=kb['cancel_button'])
        await callback_query.message.delete()
        logger.info(f"Пользователь {person_id} перешел к вводу ID продавца")
        await PaySeller.waiting_for_seller_id.set()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе ID продавца для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при вводе ID продавца. Попробуйте снова.',
             'en': 'Error entering seller ID. Try again.',
             'uk': 'Помилка при введенні ID продавця. Спробуйте ще раз.'}.get(language),
            reply_markup=kb['personal_account_menu']
        )
        await state.finish()
        await callback_query.answer()

async def process_seller_id(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    seller_id = message.text.strip()
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
    
    new_sql.user_in_bd(seller_id)
    if not new_sql.cursor.execute("SELECT user_id FROM personal_account WHERE user_id = ?", (seller_id,)).fetchone():
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': 'Продавец с таким ID не найден. Попробуйте снова.',
             'en': 'Seller with this ID not found. Try again.',
             'uk': 'Продавець з таким ID не знайдений. Спробуйте ще раз.'}.get(language),
            reply_markup=error_kb
        )
        return
    
    if seller_id == person_id:
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': 'Вы не можете отправить деньги самому себе!',
             'en': 'You cannot send money to yourself!',
             'uk': 'Ви не можете надіслати гроші самому собі!'}.get(language),
            reply_markup=error_kb
        )
        return
    
    await state.update_data(seller_id=seller_id)
    messages = {
        'ru': f'Введите сумму для оплаты продавцу (в {currency}):',
        'en': f'Enter the amount to pay the seller (in {currency}):',
        'uk': f'Введіть суму для оплати продавцю (в {currency}):'
    }
    await message.answer(messages.get(language, messages['ru']), reply_markup=keyboards.create_keyboards(language)['cancel_button'])
    await PaySeller.waiting_for_amount.set()

async def process_payment_amount(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
    user_data = await state.get_data()
    seller_id = user_data.get('seller_id')
    
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        
        amount_usd = new_sql.convert_currency(amount, currency, 'USD')
        
        if not new_sql.check_balance(person_id, amount_usd):
            back_button = InlineKeyboardButton(
                {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
                callback_data='cancel_to_personal_account'
            )
            error_kb = InlineKeyboardMarkup().add(back_button)
            await message.answer(
                {'ru': f'Недостаточно средств на балансе! Текущий баланс: {new_sql.get_balance(person_id):.2f} USD',
                 'en': f'Insufficient funds! Current balance: {new_sql.get_balance(person_id):.2f} USD',
                 'uk': f'Недостатньо коштів на балансі! Поточний баланс: {new_sql.get_balance(person_id):.2f} USD'}.get(language),
                reply_markup=error_kb
            )
            return
        
        new_sql.conn.execute("BEGIN TRANSACTION")
        try:
            new_sql.deduct_balance(person_id, amount_usd)
            new_sql.add_balance(seller_id, amount_usd)
            
            current_pay = float(new_sql.get_all_information(person_id)[0])
            current_sold = float(new_sql.get_all_information(seller_id)[2])
            current_count_buyer = int(new_sql.get_all_information(person_id)[1] or 0)
            current_count_seller = int(new_sql.get_all_information(seller_id)[1] or 0)
            
            new_sql.add_pay(str(current_pay + amount), person_id)
            new_sql.add_sold(str(current_sold + amount), seller_id)
            new_sql.add_count(str(current_count_buyer + 1), person_id)
            new_sql.add_count(str(current_count_seller + 1), seller_id)
            new_sql.increment_total_deals()  # Увеличиваем общее количество сделок
            
            history_buyer = f"Оплата продавцу {seller_id}: {amount:.2f} {currency} ({amount_usd:.2f} USD)"
            history_seller = f"Получено от покупателя {person_id}: {amount:.2f} {currency} ({amount_usd:.2f} USD)"
            new_sql.add_history(history_buyer, person_id)
            new_sql.add_history(history_seller, seller_id)
            
            new_sql.conn.commit()
            
            await message.answer(
                {'ru': f'Оплата успешно выполнена! Списано {amount:.2f} {currency} ({amount_usd:.2f} USD).',
                 'en': f'Payment successful! Deducted {amount:.2f} {currency} ({amount_usd:.2f} USD).',
                 'uk': f'Оплата успішно виконана! Списано {amount:.2f} {currency} ({amount_usd:.2f} USD).'}
                .get(language),
                reply_markup=keyboards.keyboard(language)
            )
            
            try:
                seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
                seller_currency = new_sql.get_user_preferences(seller_id).get('currency', 'USD')
                amount_seller_currency = new_sql.convert_currency(amount_usd, 'USD', seller_currency)
                await message.bot.send_message(
                    seller_id,
                    {'ru': f'Вам зачислено {amount_seller_currency:.2f} {seller_currency} ({amount_usd:.2f} USD) от пользователя {person_id}.',
                     'en': f'You received {amount_seller_currency:.2f} {seller_currency} ({amount_usd:.2f} USD) from user {person_id}.',
                     'uk': f'Вам зараховано {amount_seller_currency:.2f} {seller_currency} ({amount_usd:.2f} USD) від користувача {person_id}.'}
                    .get(seller_language)
                )
            except Exception as e:
                logger.error(f"Не удалось уведомить продавца {seller_id}: {e}")
            
            await state.finish()
        except Exception as e:
            new_sql.conn.rollback()
            logger.error(f'Ошибка в транзакции оплаты продавцу для {person_id}: {e}')
            back_button = InlineKeyboardButton(
                {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
                callback_data='cancel_to_personal_account'
            )
            error_kb = InlineKeyboardMarkup().add(back_button)
            await message.answer(
                {'ru': 'Ошибка при обработке оплаты продавцу. Попробуйте снова или используйте /paysupport.',
                 'en': 'Error processing seller payment. Try again or use /paysupport.',
                 'uk': 'Помилка при обробці оплати продавцю. Спробуйте ще раз або використовуйте /paysupport.'}.get(language),
                reply_markup=error_kb
            )
            await state.finish()
            return
    except ValueError:
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': 'Пожалуйста, введите корректную сумму (число больше 0).',
             'en': 'Please enter a valid amount (number greater than 0).',
             'uk': 'Будь ласка, введіть коректну суму (число більше 0).'}
            .get(language),
            reply_markup=error_kb
        )

async def deal_count(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    try:
        total_deals = new_sql.get_total_deals()
        await callback_query.message.answer(
            {
                'ru': f'Всего проведено сделок: {total_deals}',
                'en': f'Total deals completed: {total_deals}',
                'uk': f'Загалом завершено угод: {total_deals}'
            }.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при отображении количества сделок для {person_id}: {e}")
        await callback_query.message.answer(
            {
                'ru': 'Ошибка при отображении количества сделок. Попробуйте снова.',
                'en': 'Error displaying deal count. Try again.',
                'uk': 'Помилка при відображенні кількості угод. Спробуйте ще раз.'
            }.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.message.delete()
        await callback_query.answer()

async def helper_fo_users(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    try:
        await callback_query.message.answer(
            {'ru': "Подробно опишите вашу проблему и отправьте ее одним сообщением боту.",
             'en': "Describe your issue in detail and send it to the bot in one message.",
             'uk': "Детально опишіть вашу проблему та надішліть її одним повідомленням боту."}.get(language),
            reply_markup=keyboards.create_keyboards(language)['inline_kb9']
        )
        await callback_query.message.delete()
        await WaiteMes.waite_person_mes.set()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе сообщения в поддержку для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при отправке сообщения в поддержку. Попробуйте снова.',
             'en': 'Error sending message to support. Try again.',
             'uk': 'Помилка при надсиланні повідомлення в підтримку. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['personal_account_menu']
        )
        await callback_query.answer()

async def waite_message(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    username = message.from_user.username or ""  # Use username or empty string if none
    question = message.text.strip()  # The message text is the question
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    
    try:
        new_sql.add_question(person_id, username, question)  # Pass all three arguments
        await message.answer(
            {
                'ru': "Ваше сообщение на рассмотрении! Ждите ответа🕔",
                'en': "Your message is under review! Please wait for a response🕔",
                'uk': "Ваше повідомлення на розгляді! Чекайте відповіді🕔"
            }.get(language, "Ваше сообщение на рассмотрении! Ждите ответа🕔"),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        logger.info(f"Пользователь {person_id} (@{username}) написал в техподдержку: {question}")
        await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при добавлении вопроса в поддержку для {person_id}: {e}")
        await message.answer(
            {
                'ru': "Ошибка при отправке сообщения. Попробуйте снова.",
                'en': "Error sending message. Try again.",
                'uk': "Помилка при надсиланні повідомлення. Спробуйте ще раз."
            }.get(language, "Ошибка при отправке сообщения. Попробуйте снова."),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await state.finish()

async def about_us(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    about_us_texts = {
        'ru': f'{hbold("О нас:")}\n\n'
              f'🔒 Grimasee защищает интересы сторон при сделках. '
              f'Исключить мошеннические действия и проконтролировать исполнение обязательств.\n\n'
              f'🛡Grimasee является промежуточным звеном при любых сделках и договорах, чтобы стороны соблюдали их условия.\n\n'
              f'Если есть дополнительные вопросы, вы можете обратиться в поддержку.\n'
              f'Приятного пользования!',
        'en': f'{hbold("About Us:")}\n\n'
              f'🔒 Grimasee protects the interests of parties in transactions. '
              f'Prevent fraudulent actions and ensure compliance with obligations.\n\n'
              f'🛡Grimasee acts as an intermediary in any deals and agreements to ensure the parties adhere to their terms.\n\n'
              f'If you have additional questions, you can contact support.\n'
              f'Enjoy using!',
        'uk': f'{hbold("Про нас:")}\n\n'
              f'🔒 Grimasee захищає інтереси сторін під час угод. '
              f'Виключити шахрайські дії та проконтролировать виконання зобов’язань.\n\n'
              f'🛡Grimasee є посередником при будь-яких угодах і договорах, щоб сторони дотримувалися їх умов.\n\n'
              f'Якщо є додаткові запитання, ви можете звернутися до підтримки.\n'
              f'Приємного користування!'
    }
    try:
        await callback_query.message.answer(about_us_texts.get(language, about_us_texts['ru']), reply_markup=keyboards.create_keyboards(language)['inline_kb2'])
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при отображении 'О нас' для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при отображении информации. Попробуйте снова.',
             'en': 'Error displaying information. Try again.',
             'uk': 'Помилка при відображенні інформації. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.answer()

async def add_rev(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    logger.info(f"Запуск add_rev для {person_id}, язык: {language}")
    try:
        sent_message = await callback_query.message.answer(
            {
                'ru': "Напишите ваш отзыв о боте:",
                'en': "Write your review about the bot:",
                'uk': "Напишіть ваш відгук про бота:"
            }.get(language, "Напишите ваш отзыв о боте:")
        )
        try:
            await callback_query.message.delete()
            logger.info(f"Удалено callback-сообщение в add_rev для {person_id}")
        except BadRequest as e:
            logger.warning(f"Не удалось удалить callback-сообщение в add_rev для {person_id}: {e}")
        await asyncio.sleep(0.5)  # Задержка для Telegram
        await Feedback.waite_feedback.set()
        logger.info(f"Сохранение review_message_id={sent_message.message_id} для {person_id}")
        await state.update_data(review_message_id=sent_message.message_id)
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при запросе отзыва для {person_id}: {e}")
        inline_kb2 = keyboards.create_keyboards(language)['inline_kb2']
        logger.info(f"Отправка клавиатуры inline_kb2 в блоке except для {person_id}: {inline_kb2.to_python()}")
        await callback_query.message.answer(
            {
                'ru': 'Ошибка при отправке отзыва. Попробуйте снова.',
                'en': 'Error sending review. Try again.',
                'uk': 'Помилка при надсиланні відгуку. Спробуйте ще раз.'
            }.get(language, 'Ошибка при отправке отзыва. Попробуйте снова.'),
            reply_markup=inline_kb2
        )
        await callback_query.answer()

async def back_to_about_us(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    logger.info(f"Обработка button13 для {person_id}, язык: {language}")
    try:
        # Получаем ID сообщения с запросом отзыва
        user_data = await state.get_data()
        review_message_id = user_data.get('review_message_id')
        if review_message_id:
            try:
                await callback_query.message.bot.delete_message(
                    chat_id=person_id,
                    message_id=review_message_id
                )
                logger.info(f"Удалено сообщение с запросом отзыва {review_message_id} для {person_id}")
            except BadRequest as e:
                logger.warning(f"Не удалось удалить сообщение {review_message_id} для {person_id}: {e}")
        
        # Добавляем задержку для стабильности Telegram API
        await asyncio.sleep(0.5)
        
        # Отправляем сообщение "О нас" с клавиатурой inline_kb2
        inline_kb2 = keyboards.create_keyboards(language)['inline_kb2']
        logger.info(f"Отправка клавиатуры inline_kb2 для {person_id}: {inline_kb2.to_python()}")
        await callback_query.message.answer(
            {
                'ru': f'{hbold("О нас:")}\n\n'
                      f'🔒 Grimasee защищает интересы сторон при сделках. '
                      f'Исключить мошеннические действия и проконтролировать исполнение обязательств.\n\n'
                      f'🛡Grimasee является промежуточным звеном при любых сделках и договорах, чтобы стороны соблюдали их условия.\n\n'
                      f'Если есть дополнительные вопросы, вы можете обратиться в поддержку.\n'
                      f'Приятного пользования!',
                'en': f'{hbold("About Us:")}\n\n'
                      f'🔒 Grimasee protects the interests of parties in transactions. '
                      f'Prevent fraudulent actions and ensure compliance with obligations.\n\n'
                      f'🛡Grimasee acts as an intermediary in any deals and agreements to ensure the parties adhere to their terms.\n\n'
                      f'If you have additional questions, you can contact support.\n'
                      f'Enjoy using!',
                'uk': f'{hbold("Про нас:")}\n\n'
                      f'🔒 Grimasee захищає інтереси сторін під час угод. '
                      f'Виключити шахрайські дії та проконтролировать виконання зобов’язань.\n\n'
                      f'🛡Grimasee є посередником при будь-яких угодах і договорах, щоб сторони дотримувалися їх умов.\n\n'
                      f'Якщо є додаткові запитання, ви можете звернутися до підтримки.\n'
                      f'Приємного користування!'
            }.get(language, f'{hbold("О нас:")}\n\n'
                           f'🔒 Grimasee защищает интересы сторон при сделках. '
                           f'Исключить мошеннические действия и проконтролировать исполнение обязательств.\n\n'
                           f'🛡Grimasee является промежуточным звеном при любых сделках и договорах, чтобы стороны соблюдали их условия.\n\n'
                           f'Если есть дополнительные вопросы, вы можете обратиться в поддержку.\n'
                           f'Приятного пользования!'),
            reply_markup=inline_kb2
        )
        try:
            await callback_query.message.delete()
            logger.info(f"Удалено callback-сообщение для {person_id}")
        except BadRequest as e:
            logger.warning(f"Не удалось удалить callback-сообщение для {person_id}: {e}")
        
        await state.finish()
        await callback_query.answer()
        logger.info(f"Пользователь {person_id} вернулся в раздел 'О нас' (button13)")
    except Exception as e:
        logger.error(f"Ошибка при возврате в раздел 'О нас' для {person_id}: {e}")
        inline_kb2 = keyboards.create_keyboards(language)['inline_kb2']
        logger.info(f"Отправка клавиатуры inline_kb2 в блоке except для {person_id}: {inline_kb2.to_python()}")
        await callback_query.message.answer(
            {
                'ru': 'Ошибка при возврате. Попробуйте снова.',
                'en': 'Error returning back. Try again.',
                'uk': 'Помилка при поверненні. Спробуйте ще раз.'
            }.get(language, 'Ошибка при возврате. Попробуйте снова.'),
            reply_markup=inline_kb2
        )
        try:
            await callback_query.message.delete()
            logger.info(f"Удалено callback-сообщение в блоке except для {person_id}")
        except BadRequest as e:
            logger.warning(f"Не удалось удалить callback-сообщение в блоке except для {person_id}: {e}")
        await state.finish()
        await callback_query.answer()

async def feed_back_2(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    await state.update_data(feedback=message.text)
    
    try:
        await message.answer(
            {'ru': "Оцените бота от 1 до 5 звезд (введите число):",
             'en': "Rate the bot from 1 to 5 stars (enter a number):",
             'uk': "Оцініть бота від 1 до 5 зірок (введіть число):"}.get(language),
            reply_markup=keyboards.create_keyboards(language)['cancel_button']
        )
        await Feedback.waite_stars.set()
    except Exception as e:
        logger.error(f"Ошибка при запросе оценки для {person_id}: {e}")
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': 'Ошибка при запросе оценки. Попробуйте снова.',
             'en': 'Error requesting rating. Try again.',
             'uk': 'Помилка при запиті оцінки. Спробуйте ще раз.'}.get(language),
            reply_markup=error_kb
        )
        await state.finish()

async def waite_stars(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    username = message.from_user.username or ''  # Получаем username или пустую строку
    try:
        stars = int(message.text)
        if stars < 1 or stars > 5:
            raise ValueError("Оценка должна быть от 1 до 5")
        
        user_data = await state.get_data()
        feedback = user_data.get('feedback')
        if not feedback:
            raise ValueError("Отзыв отсутствует")
        
        new_sql.add_feed_back(person_id, feedback, f"{stars}/5", username)  # Передаем username
        await message.answer(
            {'ru': "Спасибо за ваш отзыв!",
             'en': "Thank you for your review!",
             'uk': "Дякуємо за ваш відгук!"}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        logger.info(f"Пользователь {person_id} оставил отзыв: {feedback}, оценка: {stars}/5")
        await state.finish()
    except ValueError as e:
        back_button = InlineKeyboardButton(
            {'ru': 'Назад', 'en': 'Back', 'uk': 'Назад'}.get(language, 'Назад'),
            callback_data='cancel_to_personal_account'
        )
        error_kb = InlineKeyboardMarkup().add(back_button)
        await message.answer(
            {'ru': f'Ошибка: {str(e)}. Введите число от 1 до 5!',
             'en': f'Error: {str(e)}. Enter a number from 1 to 5!',
             'uk': f'Помилка: {str(e)}. Введіть число від 1 до 5!'}.get(language),
            reply_markup=error_kb
        )

async def delete_review(callback_query: types.CallbackQuery):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    
    # Проверка, является ли пользователь администратором
    if person_id != str(ROOT_ADMIN_ID):
        await callback_query.answer(
            {'ru': "У вас нет прав для удаления отзывов!",
             'en': "You don't have permission to delete reviews!",
             'uk': "У вас немає прав для видалення відгуків!"}.get(language),
            show_alert=True
        )
        return
    
    review_id = int(callback_query.data.split('_')[-1])
    
    try:
        # Используем ваш метод delete_review_by_id
        if new_sql.delete_review_by_id(review_id):
            await callback_query.message.answer(
                {'ru': f'Отзыв ID {review_id} успешно удален.',
                 'en': f'Review ID {review_id} successfully deleted.',
                 'uk': f'Відгук ID {review_id} успішно видалено.'}.get(language),
                reply_markup=keyboards.create_keyboards(language)['back_main_menu']
            )
        else:
            await callback_query.message.answer(
                {'ru': f'Отзыв ID {review_id} не найден.',
                 'en': f'Review ID {review_id} not found.',
                 'uk': f'Відгук ID {review_id} не знайдено.'}.get(language),
                reply_markup=keyboards.create_keyboards(language)['back_main_menu']
            )
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при удалении отзыва {review_id} для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при удалении отзыва. Попробуйте снова.',
             'en': 'Error deleting review. Try again.',
             'uk': 'Помилка при видаленні відгуку. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.message.delete()
        await callback_query.answer()

async def send_rev(callback_query: types.CallbackQuery, state: FSMContext):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    texts = get_button_texts(language)
    
    # Получаем текущую страницу из состояния или устанавливаем 1
    user_data = await state.get_data()
    current_page = user_data.get('current_page', 1)
    
    # Проверка, является ли пользователь администратором
    is_admin = person_id == str(ROOT_ADMIN_ID)
    
    try:
        reviews = new_sql.get_all_reviews()
        logger.info(f"Отзывы для {person_id}: {reviews}")
        if not reviews:
            await callback_query.message.answer(
                {'ru': 'Отзывов пока нет.',
                 'en': 'No reviews yet.',
                 'uk': 'Відгуків поки немає.'}.get(language),
                reply_markup=keyboards.create_keyboards(language)['back_main_menu']
            )
            await callback_query.message.delete()
            await callback_query.answer()
            await state.finish()
            return
        
        # Параметры пагинации
        reviews_per_page = 5
        total_reviews = len(reviews)
        total_pages = (total_reviews + reviews_per_page - 1) // reviews_per_page
        
        # Проверяем, что текущая страница валидна
        if current_page < 1:
            current_page = 1
        elif current_page > total_pages:
            current_page = total_pages
        
        # Выбираем отзывы для текущей страницы
        start_idx = (current_page - 1) * reviews_per_page
        end_idx = start_idx + reviews_per_page
        page_reviews = reviews[start_idx:end_idx]
        
        # Формируем текст для текущей страницы
        review_text = {
            'ru': f'Отзывы о боте (страница {current_page} из {total_pages}):\n\n',
            'en': f'Reviews about the bot (page {current_page} of {total_pages}):\n\n',
            'uk': f'Відгуки про бота (сторінка {current_page} з {total_pages}):\n\n'
        }.get(language)
        
        for review in page_reviews:
            if len(review) < 5:  # Проверяем, что отзыв содержит все поля
                logger.warning(f"Некорректный отзыв для {person_id}: {review}")
                continue
                
            if is_admin:
                # Формат для администратора с кнопкой удаления
                review_text += (
                    f"ID отзыва: {review[0]}\n"
                    f"Отзыв оставил: @{review[4] if review[4] else 'Аноним'}\n"
                    f"ID пользователя: {review[2]}\n"
                    f"Текст: {review[1]}\n"
                    f"Оценка: {review[3]} ⭐\n\n"
                )
            else:
                # Формат для обычного пользователя
                review_text += (
                    f"Отзыв оставил: @{review[4] if review[4] else 'Аноним'}\n"
                    f"Текст: {review[1]}\n"
                    f"Оценка: {review[3]} ⭐\n\n"
                )
        
        # Создаем клавиатуру с кнопками пагинации
        kb = InlineKeyboardMarkup(row_width=3)
        if current_page > 1:
            kb.add(InlineKeyboardButton(texts['prev_page'], callback_data=f'prev_page_{current_page - 1}'))
        if current_page < total_pages:
            kb.add(InlineKeyboardButton(texts['next_page'], callback_data=f'next_page_{current_page + 1}'))
        kb.add(InlineKeyboardButton(texts['back'], callback_data='button13'))
        
        if review_text == {
            'ru': f'Отзывы о боте (страница {current_page} из {total_pages}):\n\n',
            'en': f'Reviews about the bot (page {current_page} of {total_pages}):\n\n',
            'uk': f'Відгуки про бота (сторінка {current_page} з {total_pages}):\n\n'
        }.get(language):
            await callback_query.message.answer(
                {'ru': 'Отзывов на этой странице нет или они некорректны.',
                 'en': 'No reviews on this page or they are invalid.',
                 'uk': 'Відгуків на цій сторінці немає або вони некоректні.'}.get(language),
                reply_markup=keyboards.create_keyboards(language)['back_main_menu']
            )
        else:
            await callback_query.message.edit_text(
                review_text,
                reply_markup=kb
            )
        
        # Сохраняем текущую страницу в состоянии
        await state.update_data(current_page=current_page)
        await Feedback.view_reviews.set()
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при отображении отзывов для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при отображении отзывов. Попробуйте снова.',
             'en': 'Error displaying reviews. Try again.',
             'uk': 'Помилка при відображенні відгуків. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.message.delete()
        await state.finish()
        await callback_query.answer()

async def handle_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    data = callback_query.data
    
    try:
        # Извлекаем номер страницы из callback_data
        if data.startswith('prev_page_') or data.startswith('next_page_'):
            new_page = int(data.split('_')[-1])
            await state.update_data(current_page=new_page)
            # Вызываем send_rev для отображения новой страницы
            await send_rev(callback_query, state)
        else:
            logger.warning(f"Неизвестный callback_data для пагинации: {data}")
            await callback_query.answer("Ошибка в обработке пагинации", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка при обработке пагинации для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при переключении страницы. Попробуйте снова.',
             'en': 'Error switching page. Try again.',
             'uk': 'Помилка при перемиканні сторінки. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.message.delete()
        await state.finish()
        await callback_query.answer()


async def back_button(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    try:
        await callback_query.message.answer(
            {
                'ru': f'{hbold("О нас:")}\n\n'
                      f'🔒 Grimasee защищает интересы сторон при сделках. '
                      f'Исключить мошеннические действия и проконтролировать исполнение обязательств.\n\n'
                      f'🛡Grimasee является промежуточным звеном при любых сделках и договорах, чтобы стороны соблюдали их условия.\n\n'
                      f'Если есть дополнительные вопросы, вы можете обратиться в поддержку.\n'
                      f'Приятного пользования!',
                'en': f'{hbold("About Us:")}\n\n'
                      f'🔒 Grimasee protects the interests of parties in transactions. '
                      f'Prevent fraudulent actions and ensure compliance with obligations.\n\n'
                      f'🛡Grimasee acts as an intermediary in any deals and agreements to ensure the parties adhere to their terms.\n\n'
                      f'If you have additional questions, you can contact support.\n'
                      f'Enjoy using!',
                'uk': f'{hbold("Про нас:")}\n\n'
                      f'🔒 Grimasee захищає інтереси сторін під час угод. '
                      f'Виключити шахрайські дії та проконтролировать виконання зобов’язань.\n\n'
                      f'🛡Grimasee є посередником при будь-яких угодах і договорах, щоб сторони дотримувалися їх умов.\n\n'
                      f'Якщо є додаткові запитання, ви можете звернутися до підтримки.\n'
                      f'Приємного користування!'
            }.get(language),
            reply_markup=keyboards.create_keyboards(language)['inline_kb2']
        )
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при возврате назад для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при возврате. Попробуйте снова.',
             'en': 'Error returning back. Try again.',
             'uk': 'Помилка при поверненні. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['back_main_menu']
        )
        await callback_query.answer()

async def cancel_to_personal_account(callback_query: types.CallbackQuery, state: FSMContext):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    try:
        user_data = await state.get_data()
        invoice_message_id = user_data.get('invoice_message_id')
        if invoice_message_id:
            try:
                await callback_query.message.bot.delete_message(
                    chat_id=person_id,
                    message_id=invoice_message_id
                )
                logger.info(f"Удалено сообщение с инвойсом {invoice_message_id} для пользователя {person_id} (cancel_to_personal_account)")
            except Exception as e:
                logger.warning(f"Не удалось удалить инвойс {invoice_message_id} для {person_id}: {e}")

        information = new_sql.get_all_information(person_id)
        currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
        personal_account_texts = {
            'ru': f'{hbold("🙋Добро пожаловать в личный кабинет!")}\n'
                  f'Твой 🆔: {person_id}\n\n'
                  f'♾{hbold("Совершено сделок")}: {information[1]}\n'
                  f'🤑{hbold("Продано на")}: {information[2]:.2f} {currency}\n'
                  f'💰{hbold("Куплено на")}: {information[0]:.2f} {currency}\n'
                  f'💵{hbold("Баланс")}: {information[3]:.2f} {currency}',
            'en': f'{hbold("🙋Welcome to your personal account!")}\n'
                  f'Your 🆔: {person_id}\n\n'
                  f'♾{hbold("Completed deals")}: {information[1]}\n'
                  f'🤑{hbold("Sold for")}: {information[2]:.2f} {currency}\n'
                  f'💰{hbold("Bought for")}: {information[0]:.2f} {currency}\n'
                  f'💵{hbold("Balance")}: {information[3]:.2f} {currency}',
            'uk': f'{hbold("🙋Ласкаво просимо до особистого кабінету!")}\n'
                  f'Твій 🆔: {person_id}\n\n'
                  f'♾{hbold("Завершено угод")}: {information[1]}\n'
                  f'🤑{hbold("Продано на")}: {information[2]:.2f} {currency}\n'
                  f'💰{hbold("Куплено на")}: {information[0]:.2f} {currency}\n'
                  f'💵{hbold("Баланс")}: {information[3]:.2f} {currency}'
        }
        await callback_query.message.answer(
            personal_account_texts.get(language, personal_account_texts['ru']),
            reply_markup=keyboards.create_keyboards(language)['personal_account_menu']
        )
        await callback_query.message.delete()
        await state.finish()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при возврате в личный кабинет для {person_id}: {e}")
        await callback_query.message.answer(
            {'ru': 'Ошибка при возврате в личный кабинет. Попробуйте снова.',
             'en': 'Error returning to personal account. Try again.',
             'uk': 'Помилка при поверненні до особистого кабінету. Спробуйте ще раз.'}.get(language),
            reply_markup=keyboards.create_keyboards(language)['personal_account_menu']
        )
        await state.finish()
        await callback_query.answer()

async def transaction_history(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    texts = keyboards.get_button_texts(language)
    kb = keyboards.create_keyboards(language)

    try:
        # Получаем историю транзакций из базы данных
        history = new_sql.get_users_history(person_id)  # Исправлено: get_history -> get_users_history
        if not history or history.strip() == '':
            await callback_query.message.answer(
                {
                    'ru': 'История транзакций пуста.',
                    'en': 'Transaction history is empty.',
                    'uk': 'Історія транзакцій порожня.'
                }.get(language),
                reply_markup=kb['personal_account_menu']  # Исправлено: personal_account -> personal_account_menu
            )
            await callback_query.message.delete()
            await callback_query.answer()
            return

        # Формируем сообщение с историей
        history_text = f"{texts.get('history', 'История транзакций')}:\n\n{history}"
        
        await callback_query.message.answer(
            history_text,
            reply_markup=kb['personal_account_menu']  # Исправлено: personal_account -> personal_account_menu
        )
        await callback_query.message.delete()
        await callback_query.answer()

    except Exception as e:
        logger.error(f"Ошибка при получении истории транзакций для {person_id}: {e}")
        await callback_query.message.answer(
            {
                'ru': f'Ошибка при получении истории: {str(e)}. Попробуйте снова или используйте /paysupport.',
                'en': f'Error retrieving transaction history: {str(e)}. Try again or use /paysupport.',
                'uk': f'Помилка при отриманні історії: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'
            }.get(language),
            reply_markup=kb['personal_account_menu']  # Исправлено: personal_account -> personal_account_menu
        )
        await callback_query.message.delete()
        await callback_query.answer()

async def faq_callback(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)

    try:
        faq_text = {
            'ru': (
                f'{hbold("Часто задаваемые вопросы (FAQ):")}\n\n'
                f'1. {hbold("Как работает бот?")}\n'
                f'Бот выступает гарантом сделок между покупателем и продавцом, обеспечивая безопасность и выполнение условий.\n\n'
                f'2. {hbold("Как пополнить баланс?")}\n'
                f'Перейдите в личный кабинет, выберите "Пополнить баланс" и следуйте инструкциям для оплаты через Telegram Stars или другие методы.\n\n'
                f'3. {hbold("Как вывести средства?")}\n'
                f'В личном кабинете выберите "Вывод средств", укажите сумму и способ вывода (CryptoBot или ETH).\n\n'
                f'4. {hbold("Как связаться с поддержкой?")}\n'
                f'Используйте кнопку "Поддержка" или команду /paysupport для связи с администратором.'
            ),
            'en': (
                f'{hbold("Frequently Asked Questions (FAQ):")}\n\n'
                f'1. {hbold("How does the bot work?")}\n'
                f'The bot acts as a guarantor for transactions between buyers and sellers, ensuring safety and compliance.\n\n'
                f'2. {hbold("How to top up balance?")}\n'
                f'Go to your personal account, select "Top up balance," and follow the instructions to pay via Telegram Stars or other methods.\n\n'
                f'3. {hbold("How to withdraw funds?")}\n'
                f'In your personal account, select "Withdraw funds," specify the amount and withdrawal method (CryptoBot or ETH).\n\n'
                f'4. {hbold("How to contact support?")}\n'
                f'Use the "Support" button or the /paysupport command to contact the administrator.'
            ),
            'uk': (
                f'{hbold("Часті питання (FAQ):")}\n\n'
                f'1. {hbold("Як працює бот?")}\n'
                f'Бот виступає гарантом угод між покупцем і продавцем, забезпечуючи безпеку та виконання умов.\n\n'
                f'2. {hbold("Як поповнити баланс?")}\n'
                f'Перейдіть до особистого кабінету, виберіть "Поповнити баланс" і дотримуйтесь інструкцій для оплати через Telegram Stars або інші методи.\n\n'
                f'3. {hbold("Як вивести кошти?")}\n'
                f'В особистому кабінеті виберіть "Вивести кошти", вкажіть суму та спосіб виведення (CryptoBot або ETH).\n\n'
                f'4. {hbold("Як зв’язатися з підтримкою?")}\n'
                f'Використовуйте кнопку "Підтримка" або команду /paysupport для зв’язку з адміністратором.'
            )
        }
        await callback_query.message.answer(
            faq_text.get(language, faq_text['ru']),
            reply_markup=kb['inline_kb2']
        )
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при обработке FAQ для {person_id}: {e}")
        await callback_query.message.answer(
            {
                'ru': f'Ошибка при загрузке FAQ: {str(e)}. Попробуйте снова или используйте /paysupport.',
                'en': f'Error loading FAQ: {str(e)}. Try again or use /paysupport.',
                'uk': f'Помилка при завантаженні FAQ: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'
            }.get(language),
            reply_markup=kb['inline_kb2']
        )
        await callback_query.message.delete()
        await callback_query.answer()

async def terms_callback(callback_query: types.CallbackQuery):
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    kb = keyboards.create_keyboards(language)

    try:
        terms_text = {
            'ru': (
                f'{hbold("Пользовательское соглашение")}\n\n'
                f'1. {hbold("Общие положения")}\n'
                f'Используя бота Grimasee, вы соглашаетесь с настоящими правилами и обязуетесь их соблюдать. Бот предназначен для обеспечения безопасности сделок между покупателями и продавцами.\n\n'
                f'2. {hbold("Обязанности пользователя")}\n'
                f'- Пользователь обязан предоставлять достоверную информацию при регистрации и совершении транзакций.\n'
                f'- Запрещается использовать бота для мошенничества, незаконной деятельности или нарушения законодательства.\n'
                f'- Пользователь несёт ответственность за сохранность своих данных для входа и конфиденциальность транзакций.\n\n'
                f'3. {hbold("Правила совершения сделок")}\n'
                f'- Все сделки осуществляются через бота как гаранта. Пользователь обязуется следовать инструкциям бота.\n'
                f'- Средства переводятся продавцу только после подтверждения выполнения условий сделки.\n'
                f'- Комиссия за вывод средств составляет 1.5% от суммы.\n\n'
                f'4. {hbold("Ответственность сторон")}\n'
                f'- Grimasee не несёт ответственности за действия пользователей, нарушающие настоящее соглашение.\n'
                f'- В случае споров пользователи могут обратиться в поддержку через команду /paysupport.\n\n'
                f'5. {hbold("Изменения соглашения")}\n'
                f'Администрация бота оставляет за собой право изменять данное соглашение. Уведомления об изменениях публикуются в боте.\n\n'
                f'{hbold("Незнание правил не освобождает от ответственности.")}'
            ),
            'en': (
                f'{hbold("Terms of Service")}\n\n'
                f'1. {hbold("General Provisions")}\n'
                f'By using the Grimasee bot, you agree to these terms and undertake to comply with them. The bot is designed to ensure the safety of transactions between buyers and sellers.\n\n'
                f'2. {hbold("User Responsibilities")}\n'
                f'- The user must provide accurate information during registration and transactions.\n'
                f'- It is prohibited to use the bot for fraud, illegal activities, or violation of applicable laws.\n'
                f'- The user is responsible for the security of their login credentials and the confidentiality of transactions.\n\n'
                f'3. {hbold("Transaction Rules")}\n'
                f'- All transactions are conducted through the bot as a guarantor. The user must follow the bot’s instructions.\n'
                f'- Funds are transferred to the seller only after confirmation of the transaction terms’ fulfillment.\n'
                f'- A withdrawal fee of 1.5% is applied to the transaction amount.\n\n'
                f'4. {hbold("Liability of Parties")}\n'
                f'- Grimasee is not responsible for user actions that violate these terms.\n'
                f'- In case of disputes, users can contact support via the /paysupport command.\n\n'
                f'5. {hbold("Changes to the Terms")}\n'
                f'The bot administration reserves the right to amend these terms. Notifications of changes will be published in the bot.\n\n'
                f'{hbold("Ignorance of the rules does not exempt from responsibility.")}'
            ),
            'uk': (
                f'{hbold("Угода користувача")}\n\n'
                f'1. {hbold("Загальні положення")}\n'
                f'Користуючись ботом Grimasee, ви погоджуєтеся з цими правилами та зобов’язуєтесь їх дотримуватися. Бот призначений для забезпечення безпеки угод між покупцями та продавцями.\n\n'
                f'2. {hbold("Обов’язки користувача")}\n'
                f'- Користувач зобов’язаний надавати правдиву інформацію під час реєстрації та здійснення транзакцій.\n'
                f'- Забороняється використовувати бот для шахрайства, незаконної діяльності або порушення законодавства.\n'
                f'- Користувач несе відповідальність за збереження своїх даних для входу та конфіденційність транзакцій.\n\n'
                f'3. {hbold("Правила здійснення угод")}\n'
                f'- Усі угоди проводяться через бота як гаранта. Користувач зобов’язаний дотримуватися інструкцій бота.\n'
                f'- Кошти перераховуються продавцю лише після підтвердження виконання умов угоди.\n'
                f'- Комісія за виведення коштів становить 1.5% від суми.\n\n'
                f'4. {hbold("Відповідальність сторін")}\n'
                f'- Grimasee не несе відповідальності за дії користувачів, які порушують цю угоду.\n'
                f'- У разі спорів користувачі можуть звернутися до підтримки через команду /paysupport.\n\n'
                f'5. {hbold("Зміни до угоди")}\n'
                f'Адміністрація бота залишає за собою право змінювати цю угоду. Повідомлення про зміни публікуються в боті.\n\n'
                f'{hbold("Незнання правил не звільняє від відповідальності.")}'
            )
        }
        await callback_query.message.answer(
            terms_text.get(language, terms_text['ru']),
            reply_markup=kb['inline_kb2']
        )
        await callback_query.message.delete()
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при обработке пользовательского соглашения для {person_id}: {e}")
        await callback_query.message.answer(
            {
                'ru': f'Ошибка при загрузке пользовательского соглашения: {str(e)}. Попробуйте снова или используйте /paysupport.',
                'en': f'Error loading terms of service: {str(e)}. Try again or use /paysupport.',
                'uk': f'Помилка при завантаженні угоди користувача: {str(e)}. Спробуйте ще раз або використовуйте /paysupport.'
            }.get(language),
            reply_markup=kb['inline_kb2']
        )
        await callback_query.message.delete()
        await callback_query.answer()

async def handle_menu_in_feedback(message: types.Message, state: FSMContext):
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    
    # Удаляем сообщение с запросом отзыва или оценки, если оно есть
    user_data = await state.get_data()
    review_message_id = user_data.get('review_message_id')
    if review_message_id:
        try:
            await message.bot.delete_message(chat_id=person_id, message_id=review_message_id)
            logger.info(f"Удалено сообщение с запросом отзыва {review_message_id} для {person_id}")
        except BadRequest as e:
            logger.warning(f"Не удалось удалить сообщение {review_message_id}: {e}")
    
    # Возвращаем пользователя в главное меню
    await show_main_menu(message, person_id)
    await state.finish()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(main_menu, commands=['start', 'menu'], state='*')
    dp.register_message_handler(main_menu_message_reply, lambda message: message.text in ['Меню', 'Menu', 'Меню'])
    dp.register_message_handler(handle_pay_support, commands=['paysupport'])
    dp.register_callback_query_handler(process_language_selection, lambda c: c.data.startswith('lang_'), state=UserPreferences.waiting_for_language)
    dp.register_callback_query_handler(process_currency_selection, lambda c: c.data.startswith('cur_'), state=UserPreferences.waiting_for_currency)
    dp.register_callback_query_handler(change_preferences, lambda c: c.data == 'change_preferences')
    dp.register_callback_query_handler(process_change_language, lambda c: c.data.startswith('lang_'), state=UserPreferences.change_language)
    dp.register_callback_query_handler(process_change_currency, lambda c: c.data.startswith('cur_'), state=UserPreferences.change_currency)
    dp.register_callback_query_handler(personal_account, lambda c: c.data == 'personal_account')
    dp.register_callback_query_handler(top_up_balance_start, lambda c: c.data == 'top_up_balance', state='*')
    dp.register_message_handler(process_top_up_amount, state=TopUpBalance.waiting_for_amount)
    dp.register_callback_query_handler(confirm_top_up, lambda c: c.data == 'confirm_top_up', state=TopUpBalance.waiting_for_payment)
    dp.register_pre_checkout_query_handler(process_pre_checkout_query, state=TopUpBalance.waiting_for_payment)
    dp.register_message_handler(process_successful_payment, content_types=types.ContentType.SUCCESSFUL_PAYMENT, state=TopUpBalance.waiting_for_payment)
    dp.register_callback_query_handler(withdraw_funds_start, lambda c: c.data == 'withdraw_funds', state='*')
    dp.register_message_handler(process_withdraw_amount, state=WithdrawFunds.waiting_for_amount)
    dp.register_callback_query_handler(process_withdraw_method, lambda c: c.data in ['withdraw_cryptobot', 'withdraw_eth'], state='*')
    dp.register_callback_query_handler(check_invoice_status, lambda c: c.data == 'check_invoice_status', state='*')
    dp.register_message_handler(process_eth_address, state=WithdrawFunds.waiting_for_address)
    dp.register_callback_query_handler(pay_seller_start, lambda c: c.data == 'pay_seller', state='*')
    dp.register_callback_query_handler(deal_count, lambda c: c.data == 'deal_count')
    dp.register_message_handler(process_seller_id, state=PaySeller.waiting_for_seller_id)
    dp.register_message_handler(process_payment_amount, state=PaySeller.waiting_for_amount)
    dp.register_callback_query_handler(helper_fo_users, lambda c: c.data == 'helper_fo_users')
    dp.register_message_handler(waite_message, state=WaiteMes.waite_person_mes)
    dp.register_callback_query_handler(about_us, lambda c: c.data == 'about_us')
    dp.register_callback_query_handler(add_rev, lambda c: c.data == 'add_rev')
    dp.register_message_handler(feed_back_2, state=Feedback.waite_feedback)
    dp.register_message_handler(waite_stars, state=Feedback.waite_stars)
    dp.register_callback_query_handler(send_rev, lambda c: c.data == 'send_rev')
    dp.register_callback_query_handler(back_button, lambda c: c.data == 'inline_button2')
    dp.register_callback_query_handler(cancel_to_personal_account, lambda c: c.data == 'cancel_to_personal_account', state='*')
    dp.register_callback_query_handler(faq_callback, lambda c: c.data == 'faq') 
    dp.register_callback_query_handler(terms_callback, lambda c: c.data == 'terms')
    dp.register_callback_query_handler(back_to_main_menu, lambda c: c.data == 'button19', state='*')
    dp.register_callback_query_handler(transaction_history, lambda c: c.data == 'transaction_history')
    dp.register_callback_query_handler(back_to_about_us, lambda c: c.data == 'button13', state=[Feedback.waite_feedback, Feedback.view_reviews])
    dp.register_callback_query_handler(handle_pagination, lambda c: c.data.startswith(('prev_page_', 'next_page_')), state=Feedback.view_reviews)
    dp.register_callback_query_handler(top_up_stars, lambda c: c.data == 'top_up_stars', state=TopUpBalance.waiting_for_method)
    dp.register_callback_query_handler(delete_review, lambda c: c.data.startswith('delete_review_'))
    dp.register_message_handler(handle_menu_in_feedback,lambda message: message.text in ['Меню', 'Menu', 'Меню'],state=[Feedback.waite_feedback, Feedback.waite_stars, Feedback.view_reviews])

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)