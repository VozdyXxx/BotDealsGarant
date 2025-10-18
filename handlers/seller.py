import os
from utils import keyboards
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hbold
from loguru import logger
from loader import bot
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils import sqliter

new_sql = sqliter.Sqlite(os.path.abspath(os.path.join('bot_garant.db')))

class WaiteSoldMessage(StatesGroup):
    """
    Режим FSM, создаем состояния
    для принятия ID,
    предметов для продажи и
    стоимости
    """
    waite_id = State()
    waite_sold_item = State()
    waite_cost = State()

def get_message_texts(language: str):
    """
    Возвращает переводы текстов сообщений
    """
    messages = {
        'ru': {
            'start_seller': 'Вы перешли в раздел продавца, следуйте дальнейшим указаниям бота:',
            'enter_buyer_id': 'Введите ID покупателя, если его у вас нет, то пускай покупатель запросит его у бота в разделе "Я покупатель"\nДля отмены сделки нажмите кнопку "Назад"',
            'invalid_id': 'ID введен некорректно, повторите попытку ввода (заметьте, ID не должен содержать букв и превышать 10 символов)',
            'self_transaction': 'Вы не можете проводить сделку сами с собой!',
            'enter_items': 'Введите предметы, которые собираетесь продавать (все в одном сообщении, для отмены сделки нажмите на кнопку ниже):',
            'enter_amount': 'Введите сумму, за которую вы продаете данные предметы (для отмены сделки нажмите на кнопку ниже):',
            'amount_not_digits': 'Введите сумму цифрами!',
            'invalid_id_data': 'Данные о ID указаны некорректно, проверьте правильность написания! Или попросите покупателя отправить ID повторно.',
            'deal_info': 'Сведения сделки:',
            'buyer_id': 'ID покупателя: {}',
            'items_for_sale': 'Предметы для продажи: {}',
            'total_price': 'Цена за все: {}',
            'data_correct': 'Данные верны?',
            'confirm_data': 'Да, верны',
            'reject_data': 'Нет, не верны',
            'deal_rejected': 'Покупатель отклонил сделку. Причина: Данные сделки некорректны!\nОбсудите со второй стороной подробнее сведения сделки.',
            'insufficient_funds': 'Недостаточно средств на балансе! Текущий баланс: {:.2f} USD',
            'deal_canceled_insufficient_funds': 'Сделка отменена: у покупателя недостаточно средств.',
            'payment_frozen_buyer': 'Оплата заморожена на сумму {:.2f} {} ({:.2f} USD). Подтвердите получение товара или укажите, что продавец не выполнил сделку.',
            'payment_frozen_seller': 'Покупатель оплатил сделку! Средства заморожены на сумму {:.2f} {} ({:.2f} USD). Выполните свою часть сделки и подтвердите ниже:',
            'payment_error': 'Произошла ошибка при обработке оплаты. Попробуйте снова или обратитесь в поддержку.',
            'seller_confirm': 'Подтвердить выполнение',
            'seller_confirmed': 'Вы подтвердили выполнение своей части сделки. Ожидайте подтверждения покупателя.',
            'deal_confirmed': 'Сделка завершена успешно! Средства переведены продавцу.',
            'seller_deal_confirmed': 'Сделка подтверждена покупцем! Зачислено {:.2f} {} ({:.2f} USD).',
            'deal_canceled': 'Сделка отменена...',
            'deal_data_missing': 'Ошибка: данные сделки отсутствуют или уже обработаны. Пожалуйста, начните сделку заново.',
            'buyer_not_found': 'Покупатель с указанным ID не найден. Проверьте ID и попробуйте снова.',
            'funds_returned': 'Сделка отменена. Средства в размере {:.2f} {} ({:.2f} USD) возвращены на ваш баланс.',
            'seller_deal_canceled': 'Покупатель отклонил сделку. Средства возвращены покупателю.',
            'seller_not_confirmed': 'Продавец еще не подтвердил выполнение своей части сделки.',
            'already_confirmed': 'Вы уже подтвердили выполнение своей части сделки.',
            'buyer_confirm': 'Подтвердить получение товара',
            'seller_not_fulfilled': 'Продавец не выполнил сделку',
            'seller_not_fulfilled_notification': 'Покупатель указал, что вы не выполнили свою часть сделки. Средства возвращены покупателю. Обсудите детали с покупателем.'
        },
        'en': {
            'start_seller': 'You have entered the seller section, follow the bot’s instructions:',
            'enter_buyer_id': 'Enter the buyer’s ID. If you don’t have it, ask the buyer to request it from the bot in the "I am a buyer" section\nTo cancel the deal, press the "Back" button',
            'invalid_id': 'ID entered incorrectly, try again (note that the ID must not contain letters and must not exceed 10 characters)',
            'self_transaction': 'You cannot conduct a transaction with yourself!',
            'enter_items': 'Enter the items you are going to sell (all in one message, to cancel the deal press the button below):',
            'enter_amount': 'Enter the amount for which you are selling these items (to cancel the deal press the button below):',
            'amount_not_digits': 'Enter the amount in digits!',
            'invalid_id_data': 'The ID data is incorrect, check the spelling! Or ask the buyer to send the ID again.',
            'deal_info': 'Deal details:',
            'buyer_id': 'Buyer ID: {}',
            'items_for_sale': 'Items for sale: {}',
            'total_price': 'Total price: {}',
            'data_correct': 'Is the data correct?',
            'confirm_data': 'Yes, correct',
            'reject_data': 'No, incorrect',
            'deal_rejected': 'The buyer rejected the deal. Reason: Deal details are incorrect!\nDiscuss the deal details with the other party.',
            'insufficient_funds': 'Insufficient funds! Current balance: {:.2f} USD',
            'deal_canceled_insufficient_funds': 'Deal canceled: buyer has insufficient funds.',
            'payment_frozen_buyer': 'Payment frozen for {:.2f} {} ({:.2f} USD). Confirm receipt of the item or indicate that the seller did not fulfill the deal.',
            'payment_frozen_seller': 'Buyer paid for the deal! Funds frozen for {:.2f} {} ({:.2f} USD). Complete your part of the deal and confirm below:',
            'payment_error': 'An error occurred while processing the payment. Try again or contact support.',
            'seller_confirm': 'Confirm completion',
            'seller_confirmed': 'You have confirmed completion of your part of the deal. Awaiting buyer confirmation.',
            'deal_confirmed': 'Deal completed successfully! Funds transferred to the seller.',
            'seller_deal_confirmed': 'Deal confirmed by buyer! Credited {:.2f} {} ({:.2f} USD).',
            'deal_canceled': 'Deal canceled...',
            'deal_data_missing': 'Error: deal data is missing or already processed. Please start the deal again.',
            'buyer_not_found': 'Buyer with the specified ID not found. Please check the ID and try again.',
            'funds_returned': 'Deal canceled. Funds of {:.2f} {} ({:.2f} USD) returned to your balance.',
            'seller_deal_canceled': 'Buyer rejected the deal. Funds returned to the buyer.',
            'seller_not_confirmed': 'Seller has not yet confirmed completion of their part of the deal.',
            'already_confirmed': 'You have already confirmed completion of your part of the deal.',
            'buyer_confirm': 'Confirm item receipt',
            'seller_not_fulfilled': 'Seller did not fulfill the deal',
            'seller_not_fulfilled_notification': 'The buyer indicated that you did not fulfill your part of the deal. Funds returned to the buyer. Discuss details with the buyer.'
        },
        'uk': {
            'start_seller': 'Ви перейшли до розділу продавця, дотримуйтесь подальших інструкцій бота:',
            'enter_buyer_id': 'Введіть ID покупця, якщо його у вас немає, попросіть покупця отримати його у бота в розділі "Я покупець"\nДля скасування угоди натисніть кнопку "Назад"',
            'invalid_id': 'ID введено неправильно, повторіть спробу (зауважте, ID не повинен містити букв і перевищувати 10 символів)',
            'self_transaction': 'Ви не можете проводити угоду самі з собою!',
            'enter_items': 'Введіть предмети, які ви збираєтеся продавати (усі в одному повідомленні, для скасування угоди натисніть на кнопку нижче):',
            'enter_amount': 'Введіть суму, за яку ви продаєте ці предмети (для скасування угоди натисніть на кнопку нижче):',
            'amount_not_digits': 'Введіть суму цифрами!',
            'invalid_id_data': 'Дані про ID вказані неправильно, перевірте правильність написання! Або попросіть покупця надіслати ID повторно.',
            'deal_info': 'Деталі угоди:',
            'buyer_id': 'ID покупця: {}',
            'items_for_sale': 'Предмети для продажу: {}',
            'total_price': 'Ціна за все: {}',
            'data_correct': 'Дані правильні?',
            'confirm_data': 'Так, вірні',
            'reject_data': 'Ні, не вірні',
            'deal_rejected': 'Покупець відхилив угоду. Причина: Дані угоди неправильні!\nОбговоріть деталі угоди з іншою стороною.',
            'insufficient_funds': 'Недостатньо коштів на балансі! Поточний баланс: {:.2f} USD',
            'deal_canceled_insufficient_funds': 'Угоду скасовано: у покупця недостатньо коштів.',
            'payment_frozen_buyer': 'Оплату заморожено на суму {:.2f} {} ({:.2f} USD). Підтвердіть отримання товару або вкажіть, що продавець не виконав угоду.',
            'payment_frozen_seller': 'Покупець оплатив угоду! Кошти заморожено на суму {:.2f} {} ({:.2f} USD). Виконайте свою частину угоди та підтвердіть нижче:',
            'payment_error': 'Сталася помилка при обробці оплати. Спробуйте ще раз або зверніться до підтримки.',
            'seller_confirm': 'Підтвердити виконання',
            'seller_confirmed': 'Ви підтвердили виконання своєї частини угоди. Очікуйте підтвердження покупця.',
            'deal_confirmed': 'Угоду завершено успішно! Кошти переведено продавцю.',
            'seller_deal_confirmed': 'Угоду підтверджено покупцем! Зараховано {:.2f} {} ({:.2f} USD).',
            'deal_canceled': 'Угоду скасовано...',
            'deal_data_missing': 'Помилка: дані угоди відсутні або вже оброблені. Будь ласка, почніть угоду заново.',
            'buyer_not_found': 'Покупця з вказаним ID не знайдено. Перевірте ID і спробуйте ще раз.',
            'funds_returned': 'Угоду скасовано. Кошти в розмірі {:.2f} {} ({:.2f} USD) повернено на ваш баланс.',
            'seller_deal_canceled': 'Покупець відхилив угоду. Кошти повернено покупцеві.',
            'seller_not_confirmed': 'Продавець ще не підтвердив виконання своєї частини угоди.',
            'already_confirmed': 'Ви вже підтвердили виконання своєї частини угоди.',
            'buyer_confirm': 'Підтвердити отримання товару',
            'seller_not_fulfilled': 'Продавець не виконав угоду',
            'seller_not_fulfilled_notification': 'Покупець вказав, що ви не виконали свою частину угоди. Кошти повернено покупцеві. Обговоріть деталі з покупцем.'
        }
    }
    return messages.get(language, messages['ru'])

async def started_seller(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Режим продавца, запрос ID начала сделки
    """
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    logger.info(f"started_seller called for user {person_id}, callback_data: {callback_query.data}")
    logger.info(f"back_main_menu for user {person_id}: {kb['back_main_menu'].to_python()}")
    try:
        await callback_query.message.edit_text(messages['start_seller'])
        await callback_query.message.answer(
            messages['enter_buyer_id'],
            reply_markup=kb['back_main_menu']  # Кнопка тут
        )
        await WaiteSoldMessage.waite_id.set()
        logger.info(f"started_seller completed for user {person_id}, state set to waite_id")
    except Exception as e:
        logger.error(f"Error in started_seller for user {person_id}: {e}")
        await callback_query.message.edit_text("Произошла ошибка. Попробуйте еще раз.")
    
    await callback_query.answer()


async def waite_sold_items(message: types.Message, state: FSMContext):
    """
    Запрос предметов на продажу, проверка на корректность введенного ID
    """
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    buyer_id = message.text.strip()
    await state.update_data(id=buyer_id)
    user_data = await state.get_data()

    if user_data['id'].isdigit() and len(user_data["id"]) <= 10:
        if int(user_data['id']) != int(message.from_user.id):
            # Проверяем, существует ли покупатель в базе
            if new_sql.cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_data['id'],)).fetchone():
                await message.answer(messages['enter_items'], reply_markup=kb['cancel_button'])
                await WaiteSoldMessage.waite_sold_item.set()
            else:
                await message.answer(messages['buyer_not_found'], reply_markup=kb['back_main_menu'])  # <---
        else:
            await message.answer(messages['self_transaction'], reply_markup=kb['back_main_menu'])  # тоже лучше добавить тут
    else:
        await message.answer(messages['invalid_id'], reply_markup=kb['back_main_menu'])  # и тут


async def waite_cost(message: types.Message, state: FSMContext):
    """
    Запрашиваем цену у покупателя, попутно все данные сохраняем в словарь
    """
    person_id = str(message.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    await state.update_data(item=message.text)
    await message.answer(messages['enter_amount'], reply_markup=kb['cancel_button'])
    await WaiteSoldMessage.waite_cost.set()

async def send_all_info_about_offer(message: types.Message, state: FSMContext):
    """
    Отправка сведений покупателю, сохранение данных сделки в state и базе,
    добавление ID, суммы и предметов сделки
    """
    person_id = message.from_user.id
    language = new_sql.get_user_preferences(str(person_id)).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    try:
        if message.text.isdigit() and float(message.text) > 0:
            user_data = await state.get_data()
            if not user_data.get("id") or not user_data.get("item"):
                logger.error(f"Ошибка: отсутствуют данные сделки для продавца {person_id}: id={user_data.get('id')}, item={user_data.get('item')}")
                await message.answer(messages['deal_data_missing'])
                await state.finish()
                return

            amount_usd = float(message.text)
            history = (f'{hbold(messages["deal_info"])}\n'
                       f'1️⃣{messages["buyer_id"].format(user_data["id"])}\n'
                       f'2️⃣{messages["items_for_sale"].format(user_data["item"])}\n'
                       f'3️⃣{messages["total_price"].format(amount_usd)}')
            await message.answer(history, reply_markup=kb['back_main_menu'])
            buyer_language = new_sql.get_user_preferences(user_data["id"]).get('language', 'ru')
            buyer_messages = get_message_texts(buyer_language)
            buyer_kb = keyboards.create_keyboards(buyer_language)
            confirm_button = types.InlineKeyboardButton(
                buyer_messages['confirm_data'],
                callback_data='btn6'
            )
            reject_button = types.InlineKeyboardButton(
                buyer_messages['reject_data'],
                callback_data='btn7'
            )
            inline_kb3 = types.InlineKeyboardMarkup().add(confirm_button, reject_button)
            await bot.send_message(
                user_data["id"],
                f'{hbold(buyer_messages["deal_info"])}\n'
                f'1️⃣{buyer_messages["buyer_id"].format(user_data["id"])}\n'
                f'2️⃣{buyer_messages["items_for_sale"].format(user_data["item"])}\n'
                f'3️⃣{buyer_messages["total_price"].format(amount_usd)}\n'
                f'\n{hbold(buyer_messages["data_correct"])}',
                reply_markup=inline_kb3
            )
            logger.info(f'{message.from_user.username} предложил сделку: {user_data["id"]}, цена: {amount_usd}, Предметы: {user_data["item"]}')

            # Сохраняем данные сделки в state
            await state.update_data(
                seller_id=str(person_id),
                amount_usd=amount_usd,
                item=user_data["item"],
                buyer_id=user_data["id"]
            )
            
            # Сохраняем данные в базе (включая items)
            new_sql.add_second_id(person_id, user_data["id"])
            new_sql.add_money(person_id, user_data["id"], str(amount_usd), user_data["item"])
            await state.finish()
        else:
            await message.answer(messages['amount_not_digits'])
    except Exception as exc:
        logger.error(f'Ошибка в send_all_info_about_offer: {exc}')
        await message.answer(messages['deal_data_missing'])
        await state.finish()

async def user_pay(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Покупатель подтверждает оплату, средства замораживаются
    """
    await callback_query.message.edit_reply_markup()
    buyer_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(buyer_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    try:
        # Получаем данные сделки из базы
        seller_id = new_sql.take_second_id(buyer_id)
        amount_usd, items = new_sql.get_money_and_items(buyer_id)
        
        # Проверяем наличие всех данных и существование покупателя
        if not seller_id or not amount_usd or not items:
            logger.error(f"Данные сделки отсутствуют: seller_id={seller_id}, amount_usd={amount_usd}, items={items}")
            await callback_query.message.edit_text(
                messages['deal_data_missing'],
                reply_markup=kb['back_main_menu']
            )
            if seller_id:
                seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
                seller_messages = get_message_texts(seller_language)
                seller_kb = keyboards.create_keyboards(seller_language)
                await bot.send_message(
                    seller_id,
                    seller_messages['deal_canceled'],
                    reply_markup=seller_kb['back_main_menu']
                )
            await state.finish()
            return
        
        # Проверяем существование покупателя
        if not new_sql.cursor.execute("SELECT user_id FROM users WHERE user_id=?", (buyer_id,)).fetchone():
            logger.error(f"Покупатель {buyer_id} не найден в базе данных")
            await callback_query.message.edit_text(
                messages['buyer_not_found'],
                reply_markup=kb['back_main_menu']
            )
            if seller_id:
                seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
                seller_messages = get_message_texts(seller_language)
                seller_kb = keyboards.create_keyboards(seller_language)
                await bot.send_message(
                    seller_id,
                    seller_messages['deal_canceled'],
                    reply_markup=seller_kb['back_main_menu']
                )
            await state.finish()
            return

        amount_usd = float(amount_usd)  # Преобразуем сумму в число
        
        # Проверяем баланс покупателя
        current_balance = new_sql.get_balance(buyer_id)
        logger.info(f"Проверка баланса: Покупатель {buyer_id}, текущий баланс {current_balance:.2f}, требуется {amount_usd:.2f} USD")
        if not new_sql.check_balance(buyer_id, amount_usd):
            await callback_query.message.edit_text(
                messages['insufficient_funds'].format(current_balance),
                reply_markup=kb['back_main_menu']
            )
            await state.finish()
            # Уведомляем продавца об отмене
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_messages = get_message_texts(seller_language)
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                seller_messages['deal_canceled_insufficient_funds'],
                reply_markup=seller_kb['back_main_menu']
            )
            return
        
        # Списываем с баланса покупателя и замораживаем средства
        new_sql.deduct_balance(buyer_id, amount_usd)
        transaction_id = new_sql.add_pending_transaction(buyer_id, seller_id, amount_usd, items)
        
        # Уведомляем покупателя о заморозке
        buyer_currency = new_sql.get_user_preferences(buyer_id).get('currency', 'USD')
        amount_buyer_currency = new_sql.convert_currency(amount_usd, 'USD', buyer_currency)
        await callback_query.message.edit_text(
            messages['payment_frozen_buyer'].format(amount_buyer_currency, buyer_currency, amount_usd),
            reply_markup=kb['back_main_menu']  # Удаляем кнопки подтверждения
        )
        
        # Уведомляем продавца
        seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
        seller_messages = get_message_texts(seller_language)
        seller_kb = keyboards.create_keyboards(seller_language)
        confirm_button = types.InlineKeyboardButton(
            seller_messages['seller_confirm'],
            callback_data='seller_confirm'
        )
        seller_confirm_kb = types.InlineKeyboardMarkup().add(confirm_button)
        await bot.send_message(
            seller_id,
            seller_messages['payment_frozen_seller'].format(amount_buyer_currency, buyer_currency, amount_usd),
            reply_markup=seller_confirm_kb
        )
        
        logger.info(f'Средства заморожены: транзакция {transaction_id}, покупатель {buyer_id}, продавец {seller_id}, сумма {amount_usd:.2f} USD')
        
    except Exception as exc:
        logger.error(f'Ошибка при обработке оплаты: {exc}')
        await callback_query.message.edit_text(
            messages['payment_error'],
            reply_markup=kb['back_main_menu']
        )
        if seller_id:
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_messages = get_message_texts(seller_language)
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                seller_messages['deal_canceled'],
                reply_markup=seller_kb['back_main_menu']
            )
    
    await state.finish()

async def seller_confirm(callback_query: types.CallbackQuery):
    """
    Продавец подтверждает выполнение своей части сделки
    """
    seller_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    # Проверяем, есть ли активная транзакция
    buyer_id = new_sql.take_second_id(seller_id)
    if not buyer_id:
        await callback_query.message.edit_text(
            messages['deal_data_missing'],
            reply_markup=kb['back_main_menu']
        )
        await callback_query.answer()
        return
    
    transaction_id, _, amount_usd, _, status, seller_confirmed = new_sql.get_pending_transaction(buyer_id)
    if transaction_id and status == 'pending':
        if seller_confirmed == 1:
            await callback_query.message.edit_text(
                messages['already_confirmed'],
                reply_markup=kb['back_main_menu']
            )
            await callback_query.answer()
            return
        
        # Отмечаем, что продавец подтвердил выполнение
        new_sql.cursor.execute(
            "UPDATE pending_transactions SET seller_confirmed = ? WHERE transaction_id = ?",
            (1, transaction_id)
        )
        new_sql.conn.commit()
        
        # Уведомляем продавца
        await callback_query.message.edit_text(
            messages['seller_confirmed'],
            reply_markup=kb['back_main_menu']
        )
        
        # Уведомляем покупателя, что продавец подтвердил, с кнопками для подтверждения или указания невыполнения
        buyer_language = new_sql.get_user_preferences(buyer_id).get('language', 'ru')
        buyer_messages = get_message_texts(buyer_language)
        buyer_kb = keyboards.create_keyboards(buyer_language)
        buyer_currency = new_sql.get_user_preferences(buyer_id).get('currency', 'USD')
        amount_buyer_currency = new_sql.convert_currency(amount_usd, 'USD', buyer_currency)
        confirm_button = types.InlineKeyboardButton(
            buyer_messages['buyer_confirm'],
            callback_data='btn9'
        )
        not_fulfilled_button = types.InlineKeyboardButton(
            buyer_messages['seller_not_fulfilled'],
            callback_data='btn10'
        )
        buyer_confirm_kb = types.InlineKeyboardMarkup().add(confirm_button, not_fulfilled_button)
        await bot.send_message(
            buyer_id,
            buyer_messages['payment_frozen_buyer'].format(amount_buyer_currency, buyer_currency, amount_usd),
            reply_markup=buyer_confirm_kb
        )
        
        logger.info(f"Продавец {seller_id} подтвердил выполнение для транзакции {transaction_id}")
    else:
        await callback_query.message.edit_text(
            messages['deal_data_missing'],
            reply_markup=kb['back_main_menu']
        )
    
    await callback_query.answer()

async def check_offer(callback_query: types.CallbackQuery):
    """
    Покупатель подтверждает получение товара, средства переводятся продавцу
    """
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    seller_id = new_sql.take_second_id(person_id)
    transaction_id, _, amount_usd, items, status, seller_confirmed = new_sql.get_pending_transaction(person_id)
    
    if transaction_id and status == 'pending':
        if not seller_confirmed:
            await callback_query.message.edit_text(
                messages['seller_not_confirmed'],
                reply_markup=kb['back_main_menu']
            )
            await callback_query.answer()
            return
        
        buyer_currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
        amount_buyer_currency = new_sql.convert_currency(amount_usd, 'USD', buyer_currency)
        seller_currency = new_sql.get_user_preferences(seller_id).get('currency', 'USD')
        amount_seller_currency = new_sql.convert_currency(amount_usd, 'USD', seller_currency)
        
        # Подтверждаем транзакцию
        if new_sql.confirm_transaction(transaction_id, seller_id):
            # Обновляем статистику
            current_pay = float(new_sql.get_all_information(person_id)[0] or 0)
            current_sold = float(new_sql.get_all_information(seller_id)[2] or 0)
            current_count_buyer = int(new_sql.get_all_information(person_id)[1] or 0)
            current_count_seller = int(new_sql.get_all_information(seller_id)[1] or 0)
            
            new_sql.add_pay(str(current_pay + amount_buyer_currency), person_id)
            new_sql.add_sold(str(current_sold + amount_seller_currency), seller_id)
            new_sql.add_count(str(current_count_buyer + 1), person_id)
            new_sql.add_count(str(current_count_seller + 1), seller_id)
            
            # Добавляем запись в историю
            history_buyer = f"Оплата продавцу {seller_id}: {items} за {amount_buyer_currency:.2f} {buyer_currency} ({amount_usd:.2f} USD)"
            history_seller = f"Получено от покупателя {person_id}: {items} за {amount_seller_currency:.2f} {seller_currency} ({amount_usd:.2f} USD)"
            new_sql.add_history(history_buyer, person_id)
            new_sql.add_history(history_seller, seller_id)
            
            # Уведомляем покупателя
            await callback_query.message.edit_text(
                messages['deal_confirmed'],
                reply_markup=kb['back_main_menu']
            )
            
            # Уведомляем продавца
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_messages = get_message_texts(seller_language)
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                seller_messages['seller_deal_confirmed'].format(amount_seller_currency, seller_currency, amount_usd),
                reply_markup=seller_kb['back_main_menu']
            )
            
            # Очищаем данные о сделке
            new_sql.clear_transaction_data(person_id)
            new_sql.clear_transaction_data(seller_id)
            
            logger.info(f'Сделка завершена: транзакция {transaction_id}, продавец {seller_id}, покупатель {person_id}')
        else:
            await callback_query.message.edit_text(
                messages['deal_data_missing'],
                reply_markup=kb['back_main_menu']
            )
            if seller_id:
                seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
                seller_messages = get_message_texts(seller_language)
                seller_kb = keyboards.create_keyboards(seller_language)
                await bot.send_message(
                    seller_id,
                    seller_messages['deal_canceled'],
                    reply_markup=seller_kb['back_main_menu']
                )
    else:
        await callback_query.message.edit_text(
            messages['deal_data_missing'],
            reply_markup=kb['back_main_menu']
        )
        if seller_id:
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_messages = get_message_texts(seller_language)
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                seller_messages['deal_canceled'],
                reply_markup=seller_kb['back_main_menu']
            )
    
    await callback_query.answer()

async def callback_no(callback_query: types.CallbackQuery):
    """
    Покупатель отклоняет сделку, средства возвращаются
    """
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    await callback_query.message.edit_reply_markup()
    seller_id = new_sql.take_second_id(person_id)
    transaction_id, _, amount_usd, _, status, _ = new_sql.get_pending_transaction(person_id)
    
    if transaction_id and status == 'pending':
        # Проверяем сумму в users.price для согласованности
        price, _ = new_sql.get_money_and_items(person_id)
        price = float(price) if price and price.replace('.', '', 1).isdigit() else None
        if price and price != amount_usd:
            logger.warning(f"Несоответствие сумм: users.price={price}, pending_transactions.amount_usd={amount_usd} для покупателя {person_id}")
        
        buyer_currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
        amount_buyer_currency = new_sql.convert_currency(amount_usd, 'USD', buyer_currency)
        # Возвращаем средства через cancel_transaction
        current_balance = new_sql.get_balance(person_id)
        logger.info(f"Перед возвратом средств (callback_no): Покупатель {person_id}, текущий баланс {current_balance:.2f}, возвращаемая сумма {amount_usd:.2f} USD")
        if new_sql.cancel_transaction(transaction_id, person_id):
            new_balance = new_sql.get_balance(person_id)
            logger.info(f"После возврата средств (callback_no): Покупатель {person_id}, новый баланс {new_balance:.2f} USD")
            await callback_query.message.edit_text(
                messages['funds_returned'].format(amount_buyer_currency, buyer_currency, amount_usd),
                reply_markup=kb['back_main_menu']
            )
            if seller_id:
                seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
                seller_messages = get_message_texts(seller_language)
                seller_kb = keyboards.create_keyboards(seller_language)
                await bot.send_message(
                    seller_id,
                    seller_messages['seller_deal_canceled'],
                    reply_markup=seller_kb['back_main_menu']
                )
            new_sql.clear_transaction_data(person_id)
            if seller_id:
                new_sql.clear_transaction_data(seller_id)
            # Добавляем запись в историю об отмене
            history = f"Сделка отменена: данные неверны, возвращено {amount_buyer_currency:.2f} {buyer_currency} ({amount_usd:.2f} USD)"
            new_sql.add_history(history, person_id)
        else:
            logger.error(f"Не удалось отменить транзакцию {transaction_id} для покупателя {person_id}")
            await callback_query.message.edit_text(
                messages['deal_data_missing'],
                reply_markup=kb['back_main_menu']
            )
    else:
        await callback_query.message.edit_text(
            messages['deal_data_missing'],
            reply_markup=kb['back_main_menu']
        )
        if seller_id:
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_messages = get_message_texts(seller_language)
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                seller_messages['deal_canceled'],
                reply_markup=seller_kb['back_main_menu']
            )
    
    await callback_query.answer()

async def seller_not_fulfilled(callback_query: types.CallbackQuery):
    """
    Покупатель указывает, что продавец не выполнил свою часть сделки, средства возвращаются
    """
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    await callback_query.message.edit_reply_markup()
    seller_id = new_sql.take_second_id(person_id)
    transaction_id, _, amount_usd, _, status, _ = new_sql.get_pending_transaction(person_id)
    
    if transaction_id and status == 'pending':
        # Проверяем сумму в users.price для согласованности
        price, _ = new_sql.get_money_and_items(person_id)
        price = float(price) if price and price.replace('.', '', 1).isdigit() else None
        if price and price != amount_usd:
            logger.warning(f"Несоответствие сумм: users.price={price}, pending_transactions.amount_usd={amount_usd} для покупателя {person_id}")
        
        buyer_currency = new_sql.get_user_preferences(person_id).get('currency', 'USD')
        amount_buyer_currency = new_sql.convert_currency(amount_usd, 'USD', buyer_currency)
        # Возвращаем средства через cancel_transaction
        current_balance = new_sql.get_balance(person_id)
        logger.info(f"Перед возвратом средств (seller_not_fulfilled): Покупатель {person_id}, текущий баланс {current_balance:.2f}, возвращаемая сумма {amount_usd:.2f} USD")
        if new_sql.cancel_transaction(transaction_id, person_id):
            new_balance = new_sql.get_balance(person_id)
            logger.info(f"После возврата средств (seller_not_fulfilled): Покупатель {person_id}, новый баланс {new_balance:.2f} USD")
            await callback_query.message.edit_text(
                messages['funds_returned'].format(amount_buyer_currency, buyer_currency, amount_usd),
                reply_markup=kb['back_main_menu']
            )
            if seller_id:
                seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
                seller_messages = get_message_texts(seller_language)
                seller_kb = keyboards.create_keyboards(seller_language)
                await bot.send_message(
                    seller_id,
                    seller_messages['seller_not_fulfilled_notification'],
                    reply_markup=seller_kb['back_main_menu']
                )
            new_sql.clear_transaction_data(person_id)
            if seller_id:
                new_sql.clear_transaction_data(seller_id)
            # Добавляем запись в историю об отмене
            history = f"Сделка отменена: продавец не выполнил, возвращено {amount_buyer_currency:.2f} {buyer_currency} ({amount_usd:.2f} USD)"
            new_sql.add_history(history, person_id)
        else:
            logger.error(f"Не удалось отменить транзакцию {transaction_id} для покупателя {person_id}")
            await callback_query.message.edit_text(
                messages['deal_data_missing'],
                reply_markup=kb['back_main_menu']
            )
    else:
        await callback_query.message.edit_text(
            messages['deal_data_missing'],
            reply_markup=kb['back_main_menu']
        )
        if seller_id:
            seller_language = new_sql.get_user_preferences(seller_id).get('language', 'ru')
            seller_messages = get_message_texts(seller_language)
            seller_kb = keyboards.create_keyboards(seller_language)
            await bot.send_message(
                seller_id,
                seller_messages['deal_canceled'],
                reply_markup=seller_kb['back_main_menu']
            )
    
    await callback_query.answer()

async def cancel_button(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Отмена сделки через инлайн клавиатуру
    """
    person_id = str(callback_query.from_user.id)
    language = new_sql.get_user_preferences(person_id).get('language', 'ru')
    messages = get_message_texts(language)
    kb = keyboards.create_keyboards(language)
    
    await state.finish()
    await callback_query.message.answer(messages['deal_canceled'])
    await callback_query.message.edit_reply_markup(reply_markup=kb['back_main_menu'])
    await callback_query.answer()

def register_seller_handlers(dispatcher: Dispatcher):
    """
    Регистрация хэндлеров
    """
    logger.info("Registering seller handlers")
    dispatcher.register_callback_query_handler(started_seller, text='button17')
    dispatcher.register_message_handler(waite_sold_items, state=WaiteSoldMessage.waite_id, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(waite_cost, state=WaiteSoldMessage.waite_sold_item, content_types=types.ContentTypes.TEXT)
    dispatcher.register_message_handler(send_all_info_about_offer, state=WaiteSoldMessage.waite_cost, content_types=types.ContentTypes.TEXT)
    dispatcher.register_callback_query_handler(callback_no, text='btn7')
    dispatcher.register_callback_query_handler(user_pay, text='btn6')
    dispatcher.register_callback_query_handler(check_offer, text='btn9')
    dispatcher.register_callback_query_handler(seller_confirm, text='seller_confirm')
    dispatcher.register_callback_query_handler(seller_not_fulfilled, text='btn10')
    dispatcher.register_callback_query_handler(cancel_button, text='cancel', state='*')