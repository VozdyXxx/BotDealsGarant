import os
from utils import keyboards, sqliter
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import bot
from loguru import logger

new_sql = sqliter.Sqlite(os.path.abspath(os.path.join('bot_garant.db')))

class ConfirmDeal(StatesGroup):
    """
    Состояние для ожидания уведомления о сделке
    """
    waiting_for_deal = State()

# Тестовая команда для отображения клавиатуры yes_or_no_2
async def test_keyboard_command(message: types.Message):
    """
    Тестовая команда для проверки отображения клавиатуры yes_or_no_2
    """
    language = 'ru'  # Временное значение для теста
    kb = keyboards.create_keyboards(language)
    await message.answer("Выберите роль:", reply_markup=kb['yes_or_no_2'])
    logger.info(f"Test keyboard yes_or_no_2 displayed for user {message.from_user.id}")

async def get_users_id(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает выбор роли покупателя и показывает клавиатуру с кнопкой "Получить 🆔"
    """
    logger.info(f"get_users_id called for user {callback_query.from_user.id}, callback_data: {callback_query.data}")
    try:
        await state.finish()  # Сбрасываем текущее состояние
        person_id = str(callback_query.from_user.id)
        language = new_sql.get_user_preferences(person_id).get('language', 'ru')
        kb = keyboards.create_keyboards(language)
        messages = {
            'ru': 'Нажмите "Получить 🆔", чтобы получить ваш ID.',
            'en': 'Press "Get 🆔" to receive your ID.',
            'uk': 'Натисніть "Отримати 🆔", щоб отримати ваш ID.'
        }
        # Логируем содержимое inline_kb1
        logger.info(f"inline_kb1 for user {person_id}: {kb['inline_kb1'].to_python()}")
        # Создаём временную клавиатуру для стабильности
        temp_kb = InlineKeyboardMarkup()
        temp_kb.add(InlineKeyboardButton("Получить 🆔", callback_data="button1"))
        temp_kb.add(InlineKeyboardButton("<<Назад", callback_data="button19"))
        logger.info(f"Temporary inline_kb1 for user {person_id}: {temp_kb.to_python()}")
        await callback_query.message.delete()
        await callback_query.message.answer(
            messages.get(language, messages['ru']),
            reply_markup=temp_kb  # Используем временную клавиатуру
        )
        logger.info(f"get_users_id completed for user {person_id}")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in get_users_id for user {person_id}: {e}")
        await callback_query.message.answer("Произошла ошибка. Попробуйте еще раз.")
        await callback_query.answer()

async def send_user_id(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Отправляет пользователю только его ID
    """
    logger.info(f"send_user_id called for user {callback_query.from_user.id}, callback_data: {callback_query.data}")
    try:
        person_id = str(callback_query.from_user.id)
        await callback_query.message.delete()
        await callback_query.message.answer(person_id)  # Отправляем только ID
        logger.info(f"send_user_id completed for user {person_id}")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in send_user_id for user {person_id}: {e}")
        await callback_query.message.answer("Произошла ошибка. Попробуйте еще раз.")
        await callback_query.answer()

async def back_to_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в главное меню (inline_kb2)
    """
    logger.info(f"back_to_menu called for user {callback_query.from_user.id}, callback_data: {callback_query.data}")
    try:
        person_id = str(callback_query.from_user.id)
        language = new_sql.get_user_preferences(person_id).get('language', 'ru')
        kb = keyboards.create_keyboards(language)
        # Логируем содержимое inline_kb2
        logger.info(f"inline_kb2 for user {person_id}: {kb['inline_kb2'].to_python()}")
        messages = {
            'ru': 'Вы вернулись в главное меню.',
            'en': 'You have returned to the main menu.',
            'uk': 'Ви повернулися до головного меню.'
        }
        await callback_query.message.delete()
        await callback_query.message.answer(
            messages.get(language, messages['ru']),
            reply_markup=kb['inline_kb2']  # Главное меню
        )
        await state.finish()
        logger.info(f"back_to_menu completed for user {person_id}")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in back_to_menu for user {person_id}: {e}")
        await callback_query.message.answer("Произошла ошибка. Попробуйте еще раз.")
        await callback_query.answer()

async def callback_no(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Покупатель отклоняет сделку
    """
    logger.info(f"callback_no called for user {callback_query.from_user.id}, callback_data: {callback_query.data}")
    try:
        buyer_id = str(callback_query.from_user.id)
        language = new_sql.get_user_preferences(buyer_id).get('language', 'ru')
        kb = keyboards.create_keyboards(language)
        messages = {
            'ru': {
                'deal_rejected': 'Сделка отклонена.',
                'seller_deal_rejected': 'Сделка отклонена покупателем. Обсудите детали с покупателем.'
            },
            'en': {
                'deal_rejected': 'Deal rejected.',
                'seller_deal_rejected': 'Deal rejected by buyer. Discuss details with the buyer.'
            },
            'uk': {
                'deal_rejected': 'Угоду відхилено.',
                'seller_deal_rejected': 'Угоду відхилено покупцем. Обговоріть деталі з покупцем.'
            }
        }
        await callback_query.message.delete()
        await callback_query.message.answer(
            messages[language]['deal_rejected'],
            reply_markup=kb['back_main_menu']
        )
        seller_id = new_sql.take_second_id(buyer_id)
        if seller_id:
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                messages[seller_language]['seller_deal_rejected'],
                reply_markup=seller_kb['back_main_menu']
            )
        await state.finish()
        logger.info(f"callback_no completed for user {buyer_id}")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Error in callback_no for user {buyer_id}: {e}")
        await callback_query.message.answer("Произошла ошибка. Попробуйте еще раз.")
        await callback_query.answer()

def register_buyer_handlers(dispatcher: Dispatcher):
    """
    Регистрация хэндлеров
    """
    logger.info("Registering buyer handlers")
    dispatcher.register_message_handler(test_keyboard_command, commands=['testkeyboard'])
    dispatcher.register_callback_query_handler(get_users_id, text='button18')
    dispatcher.register_callback_query_handler(send_user_id, text='button1')
    dispatcher.register_callback_query_handler(back_to_menu, text=['button19', 'back_to_menu'])
    dispatcher.register_callback_query_handler(callback_no, text='btn7', state=ConfirmDeal.waiting_for_deal)