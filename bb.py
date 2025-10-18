from aiogram import Bot, Dispatcher, types, executor
import requests

# === НАСТРОЙКИ ===
BOT_TOKEN = '8351456052:AAH1c9k2Z7bRznF35fcfVchIAVVI6fWy3s8'
        
CRYPTO_PAY_API_TOKEN = '45684:AAJfSLZCK2VTN7OKJOBEXJHx7IsMAHeOSvW'
CRYPTO_PAY_API_URL = 'https://testnet-pay.crypt.bot/api/createInvoice'
ASSET = 'USDT'  # Можно также использовать 'TON', 'BTC', 'ETH' и т.д.

# === ЗАПУСК ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# === Хэндлер старта ===
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Введите сумму в USDT, которую хотите перевести на ваш Crypto Pay аккаунт:")

# === Хэндлер суммы ===
@dp.message_handler(lambda msg: msg.text.replace('.', '', 1).isdigit())
async def create_invoice(message: types.Message):
    amount = message.text.strip()

    try:
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN
        }
        data = {
            "asset": ASSET,
            "amount": amount,
            "description": "Перевод в Crypto Pay через бота"
        }

        response = requests.post(CRYPTO_PAY_API_URL, headers=headers, json=data)
        result = response.json()

        if "result" in result:
            pay_url = result["result"]["pay_url"]
            await message.answer(f"Оплатите по ссылке:\n{pay_url}")
        else:
            await message.answer(f"Crypto Pay API вернул ошибку:\n{result}")

    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")

# === Фолбэк ===
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Введите корректную сумму в USDT, например: 12.5")

# === Запуск ===
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
