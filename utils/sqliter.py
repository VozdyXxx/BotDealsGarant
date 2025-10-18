import sqlite3
from loguru import logger
import datetime

class Sqlite:
    def __init__(self, db_file: str) -> None:
        """
        Подключаемся к БД
        """
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()
        self.migrate_feedback()
        self.migrate_balance_column()
        self.migrate_items_column()
        self.migrate_pending_transactions()
        self.migrate_total_deals()
        self.migrate_username_column()  # Добавляем вызов новой миграции

    def init_db(self) -> None:
        """
        Инициализация базы данных и создание таблиц
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    second_id TEXT,
                    price TEXT,
                    items TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS personal_account (
                    user_id TEXT PRIMARY KEY,
                    count TEXT,
                    pay TEXT,
                    sold TEXT,
                    feedback TEXT,
                    qestion TEXT,
                    history TEXT,
                    balance REAL DEFAULT 0.0,
                    username TEXT DEFAULT ''
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    text TEXT,
                    rating TEXT DEFAULT '5/5',
                    username TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    currency TEXT DEFAULT 'USD'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buyer_id TEXT,
                    seller_id TEXT,
                    amount_usd REAL,
                    items TEXT,
                    status TEXT DEFAULT 'pending',
                    seller_confirmed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    payment_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pending_withdrawals (
                    user_id TEXT,
                    invoice_id TEXT,
                    amount_usd REAL,
                    usdt_amount REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, invoice_id)
                )
            """)
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS total_deals (
                        id INTEGER PRIMARY KEY,
                        count INTEGER DEFAULT 7485
                    )
                """)
                # Проверяем, есть ли запись с id=1
                cursor.execute("SELECT count FROM total_deals WHERE id = 1")
                result = cursor.fetchone()
                if not result:
                    cursor.execute("INSERT INTO total_deals (id, count) VALUES (1, 7485)")
                    logger.info("Создана начальная запись в total_deals с count=7485")
                else:
                    logger.info(f"Таблица total_deals уже содержит запись: count={result[0]}")
                conn.commit()

    def migrate_username_column(self) -> None:
        """
        Миграция для добавления столбца username в таблицу personal_account, если он отсутствует
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(personal_account)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'username' not in columns:
                    cursor.execute("ALTER TABLE personal_account ADD COLUMN username TEXT DEFAULT ''")
                    conn.commit()
                    logger.info("Добавлен столбец username (TEXT) в таблицу personal_account")
        except sqlite3.Error as e:
            logger.error(f"Ошибка миграции столбца username: {e}")

    def add_question(self, user_id: str, username: str, question: str) -> None:
        """
        Добавление вопроса с сохранением имени пользователя
        """
        try:
            self.cursor.execute(
                "UPDATE personal_account SET qestion = ?, username = ? WHERE user_id = ?",
                (question, username, user_id)
            )
            self.conn.commit()
            logger.info(f"Добавлен вопрос от пользователя {user_id} (@{username}): {question}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении вопроса: {e}")

    def get_questions(self) -> list:
        """
        Вывод вопросов с user_id и username
        """
        try:
            self.cursor.execute(
                "SELECT user_id, username, qestion FROM personal_account WHERE qestion != '' AND qestion IS NOT NULL"
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении вопросов: {e}")
            return []

    def migrate_total_deals(self) -> None:
        """
        Миграция для создания таблицы total_deals, если она отсутствует
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(total_deals)")
                columns = [info[1] for info in cursor.fetchall()]
                if not columns:
                    cursor.execute("""
                        CREATE TABLE total_deals (
                            id INTEGER PRIMARY KEY,
                            count INTEGER DEFAULT 7485
                        )
                    """)
                    cursor.execute("INSERT OR IGNORE INTO total_deals (id, count) VALUES (1, 7485)")
                    conn.commit()
                    logger.info("Создана таблица total_deals с начальным значением 7485")
        except sqlite3.Error as e:
            logger.error(f"Ошибка миграции таблицы total_deals: {e}")

    def get_total_deals(self) -> int:
        """
        Получает общее количество сделок
        """
        try:
            result = self.cursor.execute("SELECT count FROM total_deals WHERE id = 1").fetchone()
            if result:
                return result[0]
            logger.warning("Запись в total_deals не найдена, создаем новую с count=7485")
            self.cursor.execute("INSERT INTO total_deals (id, count) VALUES (1, 7485)")
            self.conn.commit()
            return 7485
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении общего количества сделок: {e}")
            return 7485

    def increment_total_deals(self) -> None:
        """
        Увеличивает общее количество сделок на 1
        """
        try:
            # Проверяем текущее значение перед обновлением
            current_count = self.get_total_deals()
            logger.info(f"Текущее количество сделок перед инкрементом: {current_count}")
            self.cursor.execute("UPDATE total_deals SET count = count + 1 WHERE id = 1")
            if self.cursor.rowcount == 0:
                logger.warning("Обновление total_deals не затронуло ни одной строки. Проверяем наличие записи с id=1")
                self.cursor.execute("INSERT OR IGNORE INTO total_deals (id, count) VALUES (1, 7485)")
            self.conn.commit()
            new_count = self.get_total_deals()
            logger.info(f"Общее количество сделок увеличено: {new_count}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при увеличении общего количества сделок: {e}")
            raise

    def save_pending_withdrawal(self, user_id: str, invoice_id: str, amount_usd: float, usdt_amount: float) -> None:
        """
        Сохраняет данные о созданном чеке до его активации
        """
        try:
            self.cursor.execute("""
                INSERT INTO pending_withdrawals (user_id, invoice_id, amount_usd, usdt_amount)
                VALUES (?, ?, ?, ?)
            """, (user_id, invoice_id, amount_usd, usdt_amount))
            self.conn.commit()
            logger.info(f"Сохранён ожидающий вывод для {user_id}: invoice_id={invoice_id}, amount_usd={amount_usd}, usdt_amount={usdt_amount}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при сохранении ожидающего вывода для {user_id}: {e}")
            raise

    def get_pending_withdrawal(self, user_id: str) -> dict:
        """
        Получает данные о последнем ожидающем выводе для пользователя
        """
        try:
            result = self.cursor.execute("""
                SELECT invoice_id, amount_usd, usdt_amount
                FROM pending_withdrawals
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user_id,)).fetchone()
            if result:
                return {'invoice_id': result[0], 'amount_usd': result[1], 'usdt_amount': result[2]}
            return None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении ожидающего вывода для {user_id}: {e}")
            raise

    def remove_pending_withdrawal(self, user_id: str, invoice_id: str) -> None:
        """
        Удаляет данные о чеке после его активации
        """
        try:
            self.cursor.execute("""
                DELETE FROM pending_withdrawals
                WHERE user_id = ? AND invoice_id = ?
            """, (user_id, invoice_id))
            self.conn.commit()
            logger.info(f"Удалён ожидающий вывод для {user_id}: invoice_id={invoice_id}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении ожидающего вывода для {user_id}: {e}")
            raise
    def migrate_feedback(self) -> None:
        """
        Перенос существующих отзывов из personal_account.feedback в таблицу feedback
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, feedback FROM personal_account WHERE feedback != '' AND feedback IS NOT NULL")
            old_feedbacks = cursor.fetchall()
            for user_id, feedback in old_feedbacks:
                cursor.execute("INSERT INTO feedback (user_id, text, rating, username) VALUES (?, ?, ?, ?)",
                              (user_id, feedback, '5/5', ''))
            cursor.execute("UPDATE personal_account SET feedback = ''")
            conn.commit()
            if old_feedbacks:
                logger.info(f"Перенесено {len(old_feedbacks)} отзывов из personal_account в таблицу feedback")

    def migrate_balance_column(self) -> None:
        """
        Миграция для добавления столбца balance, если он отсутствует, или преобразования его в REAL
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(personal_account)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'balance' not in columns:
                    cursor.execute("ALTER TABLE personal_account ADD COLUMN balance REAL DEFAULT 0.0")
                    conn.commit()
                    logger.info("Добавлен столбец balance (REAL) в таблицу personal_account")
                else:
                    cursor.execute("PRAGMA table_info(personal_account)")
                    columns_info = {info[1]: info[2] for info in cursor.fetchall()}
                    if columns_info['balance'].upper() == 'TEXT':
                        cursor.execute("ALTER TABLE personal_account RENAME TO personal_account_old")
                        cursor.execute("""
                            CREATE TABLE personal_account (
                                user_id TEXT PRIMARY KEY,
                                count TEXT,
                                pay TEXT,
                                sold TEXT,
                                feedback TEXT,
                                qestion TEXT,
                                history TEXT,
                                balance REAL DEFAULT 0.0
                            )
                        """)
                        cursor.execute("""
                            INSERT INTO personal_account (user_id, count, pay, sold, feedback, qestion, history, balance)
                            SELECT user_id, count, pay, sold, feedback, qestion, history, CAST(balance AS REAL)
                            FROM personal_account_old
                        """)
                        cursor.execute("DROP TABLE personal_account_old")
                        conn.commit()
                        logger.info("Столбец balance в таблице personal_account успешно мигрирован с TEXT на REAL")
        except sqlite3.Error as e:
            logger.error(f"Ошибка миграции столбца balance: {e}")

    def migrate_items_column(self) -> None:
        """
        Миграция для добавления столбца items в таблицу users, если он отсутствует
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(users)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'items' not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN items TEXT")
                    conn.commit()
                    logger.info("Добавлен столбец items (TEXT) в таблицу users")
        except sqlite3.Error as e:
            logger.error(f"Ошибка миграции столбца items: {e}")

    def migrate_pending_transactions(self) -> None:
        """
        Миграция для создания таблицы pending_transactions, если она отсутствует
        """
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(pending_transactions)")
                columns = [info[1] for info in cursor.fetchall()]
                if not columns:
                    cursor.execute("""
                        CREATE TABLE pending_transactions (
                            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            buyer_id TEXT,
                            seller_id TEXT,
                            amount_usd REAL,
                            items TEXT,
                            status TEXT DEFAULT 'pending',
                            seller_confirmed INTEGER DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    conn.commit()
                    logger.info("Создана таблица pending_transactions")
                elif 'seller_confirmed' not in columns:
                    cursor.execute("ALTER TABLE pending_transactions ADD COLUMN seller_confirmed INTEGER DEFAULT 0")
                    conn.commit()
                    logger.info("Добавлен столбец seller_confirmed в таблицу pending_transactions")
        except sqlite3.Error as e:
            logger.error(f"Ошибка миграции таблицы pending_transactions: {e}")

    def user_in_bd(self, user_id: str) -> None:
        """
        Проверяем есть пользователь в БД, если его нет, то добавляем его
        """
        txt = ''
        check = self.cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if check is None:
            self.cursor.execute('INSERT INTO users (user_id, second_id, price, items) VALUES (?, ?, ?, ?)', (user_id, txt, txt, txt))
            self.cursor.execute(
                '''
                INSERT INTO personal_account (user_id, count, pay, sold, feedback, qestion, history, balance, username)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (user_id, '0', '0', '0', txt, txt, txt, 0.0, '')
            )
            self.cursor.execute('INSERT INTO user_preferences (user_id, language, currency) VALUES (?, ?, ?)', (user_id, 'ru', 'USD'))
            self.conn.commit()
            logger.info(f'Новый пользователь--{user_id}')
        else:
            check_pa = self.cursor.execute("SELECT * FROM personal_account WHERE user_id=?", (user_id,)).fetchone()
            if check_pa is None:
                self.cursor.execute(
                    '''
                    INSERT INTO personal_account (user_id, count, pay, sold, feedback, qestion, history, balance, username)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (user_id, '0', '0', '0', txt, txt, txt, 0.0, '')
                )
                self.conn.commit()
                logger.info(f'Добавлена запись в personal_account для пользователя--{user_id}')
            check_prefs = self.cursor.execute("SELECT * FROM user_preferences WHERE user_id=?", (user_id,)).fetchone()
            if check_prefs is None:
                self.cursor.execute('INSERT INTO user_preferences (user_id, language, currency) VALUES (?, ?, ?)', (user_id, 'ru', 'USD'))
                self.conn.commit()
                logger.info(f'Добавлена запись в user_preferences для пользователя--{user_id}')
            else:
                logger.info(f'Пользователь есть--{user_id}')

    def save_user_language(self, user_id: str, language: str) -> None:
        """
        Сохраняет выбранный язык пользователя
        """
        self.cursor.execute("UPDATE user_preferences SET language = ? WHERE user_id = ?", (language, user_id))
        self.conn.commit()
        logger.info(f'Язык пользователя {user_id} обновлен на {language}')

    def save_user_currency(self, user_id: str, currency: str) -> None:
        """
        Сохраняет выбранную валюту пользователя
        """
        self.cursor.execute("UPDATE user_preferences SET currency = ? WHERE user_id = ?", (currency, user_id))
        self.conn.commit()
        logger.info(f'Валюта пользователя {user_id} обновлена на {currency}')

    def get_user_preferences(self, user_id: str) -> dict:
        """
        Получает настройки пользователя (язык и валюта)
        """
        self.user_in_bd(user_id)
        result = self.cursor.execute("SELECT language, currency FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
        return {'language': result[0], 'currency': result[1]} if result else {'language': 'ru', 'currency': 'USD'}

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """
        Конвертирует сумму из одной валюты в другую
        """
        rates = {
            'USD': 1.0,
            'RUB': 90.0,
            'UAH': 42.0
        }
        try:
            converted_amount = amount * rates[to_currency.upper()] / rates[from_currency.upper()]
            return round(converted_amount, 2)
        except (KeyError, ZeroDivisionError) as e:
            logger.error(f"Ошибка конвертации: {e}")
            return amount

    def get_balance(self, user_id: str) -> float:
        """
        Получает текущий баланс пользователя в USD
        """
        self.user_in_bd(user_id)
        balance_result = self.cursor.execute("SELECT balance FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        return float(balance_result[0]) if balance_result else 0.0

    def check_balance(self, user_id: str, amount: float) -> bool:
        """
        Проверяет, достаточно ли средств на балансе пользователя
        """
        current_balance = self.get_balance(user_id)
        return current_balance >= amount

    def deduct_balance(self, user_id: str, amount: float) -> None:
        """
        Списывает сумму с баланса пользователя (в USD)
        """
        current_balance = self.get_balance(user_id)
        if current_balance < amount:
            raise ValueError(f"Недостаточно средств на балансе пользователя {user_id}: {current_balance} USD, требуется {amount} USD")
        new_balance = current_balance - amount
        self.cursor.execute("UPDATE personal_account SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        self.conn.commit()
        logger.info(f"С баланса пользователя {user_id} списано {amount} USD. Новый баланс: {new_balance} USD")

    def add_balance(self, user_id: str, amount: float) -> None:
        """
        Добавляет сумму к балансу пользователя (в USD)
        """
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount
        self.cursor.execute("UPDATE personal_account SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        self.conn.commit()
        logger.info(f"Баланс пользователя {user_id} пополнен на {amount} USD. Новый баланс: {new_balance} USD")

    def save_payment(self, user_id: str, payment_id: str, amount: float, currency: str) -> None:
        """
        Сохраняет информацию о платеже в таблицу payments
        """
        try:
            self.cursor.execute(
                "INSERT INTO payments (user_id, payment_id, amount, currency, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, payment_id, amount, currency, datetime.datetime.now().timestamp())
            )
            self.conn.commit()
            logger.info(f"Сохранен платеж для {user_id}: payment_id={payment_id}, amount={amount} {currency}")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при сохранении платежа для {user_id}: {e}")
            raise

    def add_pending_transaction(self, buyer_id: str, seller_id: str, amount_usd: float, items: str) -> int:
        """
        Добавляет замороженную транзакцию
        """
        self.cursor.execute("""
            INSERT INTO pending_transactions (buyer_id, seller_id, amount_usd, items, status, seller_confirmed)
            VALUES (?, ?, ?, ?, 'pending', 0)
        """, (buyer_id, seller_id, amount_usd, items))
        self.conn.commit()
        transaction_id = self.cursor.lastrowid
        logger.info(f"Добавлена замороженная транзакция: ID={transaction_id}, buyer_id={buyer_id}, seller_id={seller_id}, amount_usd={amount_usd}, items={items}")
        return transaction_id

    def get_pending_transaction(self, buyer_id: str) -> tuple:
        """
        Получает последнюю замороженную транзакцию для покупателя
        """
        result = self.cursor.execute("""
            SELECT transaction_id, seller_id, amount_usd, items, status, seller_confirmed
            FROM pending_transactions
            WHERE buyer_id = ? AND status = 'pending'
            ORDER BY created_at DESC LIMIT 1
        """, (buyer_id,)).fetchone()
        return result if result else (None, None, None, None, None, None)

    def confirm_transaction(self, transaction_id: int, seller_id: str) -> bool:
        """
        Подтверждает транзакцию, переводит средства продавцу и увеличивает счетчик сделок
        """
        logger.info(f"Попытка подтвердить транзакцию {transaction_id} для продавца {seller_id}")
        result = self.cursor.execute("SELECT buyer_id, seller_id, amount_usd, status FROM pending_transactions WHERE transaction_id = ? AND status = 'pending'", (transaction_id,)).fetchone()
        if result:
            buyer_id, _, amount_usd, _ = result
            self.add_balance(seller_id, amount_usd)
            self.cursor.execute("UPDATE pending_transactions SET status = 'completed' WHERE transaction_id = ?", (transaction_id,))
            self.increment_total_deals()
            self.conn.commit()
            logger.info(f"Транзакция {transaction_id} подтверждена, переведено {amount_usd} USD продавцу {seller_id}, общее количество сделок: {self.get_total_deals()}")
            return True
        logger.warning(f"Не удалось подтвердить транзакцию {transaction_id}: транзакция не найдена или уже завершена")
        return False

    def cancel_transaction(self, transaction_id: int, buyer_id: str) -> bool:
        """
        Отменяет транзакцию, возвращает средства покупателю
        """
        result = self.cursor.execute("SELECT buyer_id, amount_usd, status FROM pending_transactions WHERE transaction_id = ? AND status = 'pending'", (transaction_id,)).fetchone()
        if result:
            _, amount_usd, _ = result
            self.add_balance(buyer_id, amount_usd)
            self.cursor.execute("UPDATE pending_transactions SET status = 'canceled' WHERE transaction_id = ?", (transaction_id,))
            self.conn.commit()
            logger.info(f"Транзакция {transaction_id} отменена, возвращено {amount_usd} USD покупателю {buyer_id}")
            return True
        logger.warning(f"Не удалось отменить транзакцию {transaction_id}: транзакция не найдена или уже завершена")
        return False

    def clear_transaction_data(self, user_id: str) -> None:
        """
        Очищает данные о сделке в таблице users
        """
        self.cursor.execute("UPDATE users SET second_id = '', price = '', items = '' WHERE user_id = ?", (user_id,))
        self.conn.commit()
        logger.info(f"Данные о сделке очищены для пользователя {user_id}")

    def add_second_id(self, user_id: str, second_id: str) -> None:
        """
        Добавляем второй ID
        """
        self.cursor.execute("UPDATE users SET second_id = ? WHERE user_id = ?", (second_id, user_id))
        self.cursor.execute("UPDATE users SET second_id = ? WHERE user_id = ?", (user_id, second_id))
        self.conn.commit()

    def add_money(self, first_id: str, second_id: str, money: str, items: str = '') -> None:
        """
        Добавляем сумму сделки и предметы
        """
        self.cursor.execute("UPDATE users SET price = ?, items = ? WHERE user_id = ?", (money, items, first_id))
        self.cursor.execute("UPDATE users SET price = ?, items = ? WHERE user_id = ?", (money, items, second_id))
        self.conn.commit()

    def get_money_and_items(self, user_id: str) -> tuple:
        """
        Достаем сумму сделки и предметы
        """
        result = self.cursor.execute("SELECT price, items FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return (result[0], result[1]) if result else ("0", "")

    def clear_feedback(self, user_id: str) -> None:
        """
        Удаление всех отзывов пользователя
        """
        self.cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def add_feed_back(self, feedback: str, user_id: str, rating: str = '5/5', username: str = '') -> None:
        """
        Добавление отзыва
        """
        self.cursor.execute("INSERT INTO feedback (user_id, text, rating, username) VALUES (?, ?, ?, ?)",
                           (user_id, feedback, rating, username))
        self.conn.commit()
    def get_all_reviews(self) -> list:
        """
        Получить все отзывы
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, text, rating, username FROM feedback")
            return cursor.fetchall()

    def delete_review_by_id(self, review_id: int) -> bool:
        """
        Удалить отзыв по ID
        """
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback WHERE id = ?", (review_id,))
            conn.commit()
            return cursor.rowcount > 0

    def take_second_id(self, user_id: str) -> str:
        """
        Достаем второй ID
        """
        sec_id = self.cursor.execute("SELECT second_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return sec_id[0] if sec_id else ''

    def get_feed_back(self) -> sqlite3.Cursor:
        """
        Вывод всех отзывов
        """
        return self.cursor.execute("SELECT id, user_id, text, rating, username FROM feedback")


    def get_all_id(self) -> sqlite3.Cursor:
        """
        Достаем все ID
        """
        users_id = self.cursor.execute("SELECT user_id FROM users")
        return users_id

    def add_count(self, counter: str, user_id: str) -> None:
        """
        Добавляем кол-во сделок
        """
        self.cursor.execute("UPDATE personal_account SET count = ? WHERE user_id = ?", (counter, user_id))
        self.conn.commit()

    def add_pay(self, pay: str, user_id: str) -> None:
        """
        Добавляем сумму покупки
        """
        self.cursor.execute("UPDATE personal_account SET pay = ? WHERE user_id = ?", (pay, user_id))
        self.conn.commit()

    def add_sold(self, sold: str, user_id: str) -> None:
        """
        Добавляем сумму продажи
        """
        self.cursor.execute("UPDATE personal_account SET sold = ? WHERE user_id = ?", (sold, user_id))
        self.conn.commit()

    def get_all_information(self, user_id: str) -> tuple:
        """
        Достаем все значения из БД
        """
        self.user_in_bd(user_id)
        count_result = self.cursor.execute("SELECT count FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        pay_result = self.cursor.execute("SELECT pay FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        sold_result = self.cursor.execute("SELECT sold FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        balance_result = self.cursor.execute("SELECT balance FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        count = count_result[0] if count_result else '0'
        pay = pay_result[0] if pay_result else '0'
        sold = sold_result[0] if sold_result else '0'
        balance = balance_result[0] if balance_result else 0.0
        user_prefs = self.get_user_preferences(user_id)
        currency = user_prefs.get('currency', 'USD')
        try:
            pay = self.convert_currency(float(pay), 'USD', currency)
            sold = self.convert_currency(float(sold), 'USD', currency)
            balance = self.convert_currency(float(balance), 'USD', currency)
            return pay, count, sold, balance
        except ValueError as e:
            logger.error(f"Ошибка преобразования сумм для user_id {user_id}: pay={pay}, sold={sold}, balance={balance}, error={e}")
            return float(pay) if pay else 0.0, count, float(sold) if sold else 0.0, float(balance) if balance else 0.0

    def add_history(self, history: str, user_id: str) -> None:
        """
        Добавление записи в историю
        """
        history_list = []
        hist_result = self.cursor.execute("SELECT history FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        hist = hist_result[0] if hist_result else ''
        history_list.append(hist)
        history_list.append(history)
        all_history = ''
        for i_history in history_list:
            if i_history:
                all_history += '\n\n' + i_history + f" Время проведения сделки: {datetime.datetime.now().timestamp()}\n"
        self.cursor.execute("UPDATE personal_account SET history = ? WHERE user_id = ?", (all_history, user_id))
        self.conn.commit()


    def get_users_history(self, user_id: str) -> str:
        """
        Вывод истории
        """
        hist_result = self.cursor.execute("SELECT history FROM personal_account WHERE user_id = ?", (user_id,)).fetchone()
        hist = hist_result[0] if hist_result else ''
        user_prefs = self.get_user_preferences(user_id)
        language = user_prefs.get('language', 'ru')
        empty_history = {
            'ru': 'История пуста',
            'en': 'History is empty',
            'uk': 'Історія порожня'
        }
        return hist if hist else empty_history.get(language, empty_history['ru'])

    def close(self) -> None:
        """
        Закрытие соединения с базой данных
        """
        if self.conn:
            self.conn.close()
            logger.info("Соединение с базой данных закрыто")