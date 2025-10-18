import os
import sqlite3
from utils import keyboards
from utils import sqliter
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from loguru import logger
from loader import bot
from aiogram.dispatcher.filters.state import State, StatesGroup

new_sql = sqliter.Sqlite(os.path.abspath(os.path.join('bot_garant.db')))

root = 697410695 # Telegram ID администратора

# --- FSM States ---
class Answer(StatesGroup):
    id_person_waite = State()
    answer_waite = State()

class WaitePost(StatesGroup):
    waite_title_headers = State()
    waite_text = State()
    waite_img = State()
    waite_href = State()

class DeleteReview(StatesGroup):
    waiting_review_id = State()

class AddBalance(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()

def get_message_texts(language: str = 'ru'):
    """
    Возвращает переводы текстов сообщений для админ-панели
    """
    messages = {
        'ru': {
            'admin_menu_opened': 'Админ меню открыто. Приятного пользования.\nЧтобы его закрыть, пропишите /start.',
            'no_permission': 'У вас нет прав для доступа к админ-панели.',
            'view_messages': 'Список сообщений:\n\n{}',
            'no_messages': 'Сообщений пока нет.',
            'user_count': 'Всего пользователей: {}',
            'enter_user_id': 'Введите ID пользователя, которому хотите ответить:',
            'enter_answer': 'Введите сообщение с ответом:',
            'message_sent': 'Сообщение отправлено!',
            'error_invalid_id': 'Ошибка: ID неправильный или пользователь заблокировал бота.',
            'enter_post_title': 'Введите заголовок рекламного поста:',
            'enter_post_text': 'Введите основной текст:',
            'enter_post_image': 'Вставьте фотографию для привлечения внимания:',
            'enter_post_url': 'Введите ссылку на рекламируемый объект:',
            'no_reviews': 'Отзывов пока нет.',
            'review_list': 'Список отзывов:\n\n{}',
            'enter_review_id': 'Введите ID отзыва для удаления (например, 1 или 2):',
            'review_deleted': '✅ Отзыв с ID {} успешно удалён.',
            'review_not_found': '❌ Отзыв с ID {} не найден. Убедитесь, что вы ввели правильный ID отзыва (например, 1 или 2).',
            'invalid_review_id': '❌ Введите корректный ID отзыва (целое число, например, 1 или 2).',
            'enter_balance_user_id': 'Введите ID пользователя для пополнения баланса:',
            'enter_balance_amount': 'Введите сумму для пополнения (в USD, например, 10.50):',
            'invalid_amount': '❌ Введите корректную сумму (положительное число, например, 10.50).',
            'balance_added': '✅ Баланс пользователя {} успешно пополнен на {:.2f} USD.',
            'user_not_found': '❌ Пользователь с ID {} не найден.'
        },
        'en': {
            'admin_menu_opened': 'Admin menu opened. Enjoy using it.\nTo close it, type /start.',
            'no_permission': 'You do not have permission to access the admin panel.',
            'view_messages': 'List of messages:\n\n{}',
            'no_messages': 'No messages yet.',
            'user_count': 'Total users: {}',
            'enter_user_id': 'Enter the user ID to reply to:',
            'enter_answer': 'Enter the response message:',
            'message_sent': 'Message sent!',
            'error_invalid_id': 'Error: Invalid ID or user has blocked the bot.',
            'enter_post_title': 'Enter the title of the promotional post:',
            'enter_post_text': 'Enter the main text:',
            'enter_post_image': 'Insert a photo to attract attention:',
            'enter_post_url': 'Enter the link to the promoted object:',
            'no_reviews': 'No reviews yet.',
            'review_list': 'List of reviews:\n\n{}',
            'enter_review_id': 'Enter the review ID to delete (e.g., 1 or 2):',
            'review_deleted': '✅ Review with ID {} successfully deleted.',
            'review_not_found': '❌ Review with ID {} not found. Ensure you entered the correct review ID (e.g., 1 or 2).',
            'invalid_review_id': '❌ Enter a valid review ID (an integer, e.g., 1 or 2).',
            'enter_balance_user_id': 'Enter the user ID to top up the balance:',
            'enter_balance_amount': 'Enter the amount to top up (in USD, e.g., 10.50):',
            'invalid_amount': '❌ Enter a valid amount (a positive number, e.g., 10.50).',
            'balance_added': '✅ User {} balance successfully topped up by {:.2f} USD.',
            'user_not_found': '❌ User with ID {} not found.'
        },
        'uk': {
            'admin_menu_opened': 'Адмін-меню відкрито. Приємного користування.\nЩоб його закрити, напишіть /start.',
            'no_permission': 'У вас немає прав для доступу до адмін-панелі.',
            'view_messages': 'Список повідомлень:\n\n{}',
            'no_messages': 'Повідомлень поки немає.',
            'user_count': 'Всього користувачів: {}',
            'enter_user_id': 'Введіть ID користувача, якому хочете відповісти:',
            'enter_answer': 'Введіть повідомлення з відповіддю:',
            'message_sent': 'Повідомлення відправлено!',
            'error_invalid_id': 'Помилка: Неправильний ID або користувач заблокував бота.',
            'enter_post_title': 'Введіть заголовок рекламного поста:',
            'enter_post_text': 'Введіть основний текст:',
            'enter_post_image': 'Вставте фотографію для привернення уваги:',
            'enter_post_url': 'Введіть посилання на рекламований об’єкт:',
            'no_reviews': 'Відгуків поки немає.',
            'review_list': 'Список відгуків:\n\n{}',
            'enter_review_id': 'Введіть ID відгуку для видалення (наприклад, 1 або 2):',
            'review_deleted': '✅ Відгук з ID {} успішно видалено.',
            'review_not_found': '❌ Відгук з ID {} не знайдено. Переконайтеся, що ви ввели правильний ID відгуку (наприклад, 1 або 2).',
            'invalid_review_id': '❌ Введіть коректний ID відгуку (ціле число, наприклад, 1 або 2).',
            'enter_balance_user_id': 'Введіть ID користувача для поповнення балансу:',
            'enter_balance_amount': 'Введіть суму для поповнення (у USD, наприклад, 10.50):',
            'invalid_amount': '❌ Введіть коректну суму (позитивне число, наприклад, 10.50).',
            'balance_added': '✅ Баланс користувача {} успішно поповнено на {:.2f} USD.',
            'user_not_found': '❌ Користувача з ID {} не знайдено.'
        }
    }
    return messages.get(language, messages['ru'])

# --- Хэндлеры ---
async def admin_menu(message: types.Message):
    """
    Открытие админ-панели
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = [
            messages.get('view_messages', 'Просмотр сообщений'),
            messages.get('enter_answer', 'Ответить на сообщение'),
            messages.get('user_count', 'Просмотреть ко-во пользователей'),
            messages.get('enter_post_title', 'Сделать рекламный пост'),
            messages.get('enter_review_id', 'Удалить отзыв по ID'),
            'Пополнить баланс по ID'  # Новая кнопка
        ]
        keyboard.add(*buttons)
        await message.answer(messages['admin_menu_opened'], reply_markup=keyboard)
    else:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['no_permission'])
        logger.info(f"Пользователь {message.from_user.id}|{message.from_user.username} пытался войти в 'админ меню'")

async def view(message: types.Message):
    """
    Просмотр всех сообщений из техподдержки
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        all_questions = new_sql.get_questions()
        response = ""
        if all_questions:
            for idx, question in enumerate(all_questions, 1):
                # question: (user_id, username, qestion)
                if len(question) != 3:
                    logger.warning(f"Некорректное сообщение из техподдержки: {question}")
                    continue
                user_id, username, message_text = question
                response += (
                    f"{hbold('Сообщение')} #{idx}\n"
                    f"От: @{username if username else 'Аноним'}\n"
                    f"ID пользователя: {user_id}\n"
                    f"Текст: {message_text}\n\n"
                )
                logger.info(f"Обработано сообщение #{idx}: user_id={user_id}, username={username}, text={message_text}")
            await message.answer(messages['view_messages'].format(response) if response else messages['no_messages'])
        else:
            await message.answer(messages['no_messages'])
    else:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['no_permission'])
        logger.info(f"Пользователь {message.from_user.id}|{message.from_user.username} пытался просмотреть сообщения")

async def count_people(message: types.Message):
    """
    Подсчет количества пользователей
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        users = new_sql.get_all_id().fetchall()  # Fetch all rows
        await message.answer(messages['user_count'].format(len(users)))
    else:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['no_permission'])
        logger.info(f"Пользователь {message.from_user.id}|{message.from_user.username} пытался просмотреть количество пользователей")

async def answer(message: types.Message):
    """
    Запрос ID пользователя для ответа на сообщение
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['enter_user_id'])
        await Answer.id_person_waite.set()

async def id_person_waite(message: types.Message, state: FSMContext):
    """
    Ожидание ввода ID пользователя для ответа
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await state.update_data(id=message.text.strip())
        await message.answer(messages['enter_answer'])
        await Answer.answer_waite.set()

async def answer_waite(message: types.Message, state: FSMContext):
    """
    Отправка ответа пользователю
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await state.update_data(answer=message.text)
        get_data = await state.get_data()
        try:
            await bot.send_message(get_data['id'], get_data['answer'])
            await message.answer(messages['message_sent'])
            logger.info(f'Ответ отправлен пользователю: {get_data["id"]}')
        except Exception as exc:
            logger.error(f'Ошибка отправки ответа: {exc}')
            await message.answer(messages['error_invalid_id'])
        finally:
            await state.finish()

async def add_post(message: types.Message):
    """
    Начало создания рекламного поста
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['enter_post_title'])
        await WaitePost.waite_title_headers.set()

async def waite_title(message: types.Message, state: FSMContext):
    """
    Ожидание заголовка рекламного поста
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await state.update_data(title=message.text)
        await message.answer(messages['enter_post_text'])
        await WaitePost.waite_text.set()

async def waite_text(message: types.Message, state: FSMContext):
    """
    Ожидание текста рекламного поста
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await state.update_data(text=message.text)
        await message.answer(messages['enter_post_image'])
        await WaitePost.waite_img.set()

async def waite_img(message: types.Message, state: FSMContext):
    """
    Ожидание изображения для рекламного поста
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await state.update_data(img=message.photo[0].file_id)
        await message.answer(messages['enter_post_url'])
        await WaitePost.waite_href.set()

async def waite_href_and_send(message: types.Message, state: FSMContext):
    """
    Ожидание ссылки и отправка рекламного поста
    """
    if message.from_user.id == root:
        await state.update_data(href=message.text)
        user_data = await state.get_data()
        inline_post_kb = keyboards.InlineKeyboardButton('Перейти к источнику', url=user_data["href"])
        post_keyboard = keyboards.InlineKeyboardMarkup().add(inline_post_kb)
        users_id = new_sql.get_all_id()

        for i_id in users_id:
            try:
                await bot.send_photo(
                    i_id[0],
                    user_data["img"],
                    f'{hbold(user_data["title"])}\n\n{user_data["text"]}',
                    reply_markup=post_keyboard
                )
            except Exception as exc:
                logger.error(f"Пользователь {i_id[0]} заблокировал бота | {exc}")
        await state.finish()

# --- Удаление отзыва ---
async def delete_review_prompt(message: types.Message):
    """
    Запрос ID отзыва для удаления
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        reviews = new_sql.get_all_reviews()
        logger.info(f"Отзывы для админ-панели {message.from_user.id}: {reviews}")
        if not reviews:
            await message.answer(messages['no_reviews'])
            return

        # Формируем список отзывов для отображения
        response = ""
        for review in reviews:
            if len(review) < 5:
                logger.warning(f"Некорректный отзыв для админ-панели: {review}")
                continue
            review_id, text, user_id, rating, username = review
            response += (
                f"ID отзыва: {review_id}\n"
                f"От: @{username if username else 'Аноним'}\n"
                f"ID пользователя: {user_id}\n"
                f"Текст: {text}\n"
                f"Рейтинг: {rating}\n\n"
            )
        
        await message.answer(messages['review_list'].format(response))
        await message.answer(messages['enter_review_id'])
        await DeleteReview.waiting_review_id.set()
    else:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['no_permission'])
        logger.info(f"Пользователь {message.from_user.id} пытался войти в админ-панель для удаления отзыва")
async def delete_review(message: types.Message, state: FSMContext):
    """
    Удаление отзыва по ID
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        review_id = message.text.strip()
        logger.info(f"Попытка удаления отзыва ID {review_id} пользователем {message.from_user.id}")
        try:
            review_id = int(review_id)
            if new_sql.delete_review_by_id(review_id):
                await message.answer(messages['review_deleted'].format(review_id))
                logger.info(f"Отзыв ID {review_id} успешно удален")
            else:
                await message.answer(messages['review_not_found'].format(review_id))
                logger.warning(f"Отзыв ID {review_id} не найден")
        except ValueError:
            await message.answer(messages['invalid_review_id'])
            logger.error(f"Некорректный ID отзыва: {review_id}")
        except Exception as e:
            logger.error(f"Ошибка при удалении отзыва ID {review_id}: {e}")
            await message.answer(f"❌ Ошибка при удалении: {e}")
        finally:
            await state.finish()
    else:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['no_permission'])
        logger.info(f"Пользователь {message.from_user.id} пытался удалить отзыв без прав")
        await state.finish()

# --- Пополнение баланса ---
async def add_balance_prompt(message: types.Message):
    """
    Запрос ID пользователя для пополнения баланса
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['enter_balance_user_id'])
        await AddBalance.waiting_user_id.set()
    else:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        await message.answer(messages['no_permission'])

async def add_balance_user_id(message: types.Message, state: FSMContext):
    """
    Ожидание ввода ID пользователя для пополнения баланса
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        user_id = message.text.strip()
        # Проверяем, существует ли пользователь
        if new_sql.cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,)).fetchone():
            await state.update_data(user_id=user_id)
            await message.answer(messages['enter_balance_amount'])
            await AddBalance.waiting_amount.set()
        else:
            await message.answer(messages['user_not_found'].format(user_id))
            await state.finish()

async def add_balance_amount(message: types.Message, state: FSMContext):
    """
    Ожидание ввода суммы для пополнения баланса
    """
    if message.from_user.id == root:
        language = new_sql.get_user_preferences(str(message.from_user.id)).get('language', 'ru')
        messages = get_message_texts(language)
        try:
            amount = float(message.text.strip())
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")
            user_data = await state.get_data()
            user_id = user_data['user_id']
            new_sql.add_balance(user_id, amount)
            await message.answer(messages['balance_added'].format(user_id, amount))
            # Уведомляем пользователя о пополнении
            user_language = new_sql.get_user_preferences(user_id).get('language', 'ru')
            user_messages = get_message_texts(user_language)
            user_currency = new_sql.get_user_preferences(user_id).get('currency', 'USD')
            amount_converted = new_sql.convert_currency(amount, 'USD', user_currency)
            await bot.send_message(
                user_id,
                f"Ваш баланс пополнен на {amount_converted:.2f} {user_currency} ({amount:.2f} USD).",
                reply_markup=keyboards.create_keyboards(user_language)['back_main_menu']
            )
            logger.info(f"Админ пополнил баланс пользователя {user_id} на {amount} USD")
        except ValueError:
            await message.answer(messages['invalid_amount'])
        except Exception as e:
            logger.error(f"Ошибка при пополнении баланса: {e}")
            await message.answer(f"❌ Ошибка при пополнении: {e}")
        finally:
            await state.finish()

# --- Регистрация ---
def register_admin_menu(dispatcher: Dispatcher):
    """
    Регистрация хэндлеров админ-панели
    """
    # Список текстов кнопки "Удалить отзыв по ID" для всех языков
    delete_review_texts = [
        get_message_texts('ru')['enter_review_id'],
        get_message_texts('en')['enter_review_id'],
        get_message_texts('uk')['enter_review_id']
    ]
    
    dispatcher.register_message_handler(admin_menu, commands=['admin'])
    dispatcher.register_message_handler(view, lambda message: message.text in [
        get_message_texts('ru')['view_messages'],
        get_message_texts('en')['view_messages'],
        get_message_texts('uk')['view_messages']
    ])
    dispatcher.register_message_handler(count_people, lambda message: message.text in [
        get_message_texts('ru')['user_count'],
        get_message_texts('en')['user_count'],
        get_message_texts('uk')['user_count']
    ])
    dispatcher.register_message_handler(answer, lambda message: message.text in [
        get_message_texts('ru')['enter_answer'],
        get_message_texts('en')['enter_answer'],
        get_message_texts('uk')['enter_answer']
    ])
    dispatcher.register_message_handler(id_person_waite, state=Answer.id_person_waite, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(answer_waite, state=Answer.answer_waite, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(add_post, lambda message: message.text in [
        get_message_texts('ru')['enter_post_title'],
        get_message_texts('en')['enter_post_title'],
        get_message_texts('uk')['enter_post_title']
    ])
    dispatcher.register_message_handler(waite_title, state=WaitePost.waite_title_headers)
    dispatcher.register_message_handler(waite_text, state=WaitePost.waite_text)
    dispatcher.register_message_handler(waite_img, state=WaitePost.waite_img, content_types=types.ContentTypes.PHOTO)
    dispatcher.register_message_handler(waite_href_and_send, state=WaitePost.waite_href)
    dispatcher.register_message_handler(delete_review_prompt, lambda message: message.text in delete_review_texts)
    dispatcher.register_message_handler(delete_review, state=DeleteReview.waiting_review_id, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(add_balance_prompt, lambda message: message.text == 'Пополнить баланс по ID')
    dispatcher.register_message_handler(add_balance_user_id, state=AddBalance.waiting_user_id, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(add_balance_amount, state=AddBalance.waiting_amount, content_types=types.ContentTypes.TEXT)