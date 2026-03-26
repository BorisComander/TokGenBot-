from aiogram.dispatcher import FSMContext
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import *

import openai

bot = Bot(token=API_TOKEN)

from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

openai.api_key = OPENAI_API_KEY

# Данные
user_balance = {}
user_state = {}
user_history = {}
cache = {}

# Клавиатура
main_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add("🎬 Сценарии", "⚡ Хуки")
main_kb.add("💡 Идеи", "🎲 Случайная идея")
main_kb.add("💎 PRO")

# Проверка доступа
def check_access(user_id):
    if user_id in ADMINS:
        return True
    return user_balance.get(user_id, START_BALANCE) >= UNIT_COST

# Генерация
async def generate(prompt):
    if prompt in cache:
        return cache[prompt]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response['choices'][0]['message']['content']
    cache[prompt] = text
    return text

# Старт
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    uid = message.from_user.id

    if uid not in user_balance:
        user_balance[uid] = START_BALANCE

    await message.answer("TokGenBot готов 🚀", reply_markup=main_kb)

# Кнопки
@dp.message_handler(lambda m: m.text in ["🎬 Сценарии", "⚡ Хуки"])
async def choose_niche(message: types.Message):
    user_state[message.from_user.id] = message.text
    await message.answer("Напиши нишу:")

# Текст
@dp.message_handler()
async def handle_text(message: types.Message):
    uid = message.from_user.id
    state = user_state.get(uid)

    if not state:
        return

    if not check_access(uid):
        await message.answer("❌ Лимит закончился")
        return

    loading = await message.answer("⌛ Генерируем...")

    if state == "🎬 Сценарии":
        prompt = f"Сделай 3 вирусных TikTok сценария. Ниша: {message.text}"

    elif state == "⚡ Хуки":
        prompt = f"Сделай 10 вирусных хуков для TikTok. Ниша: {message.text}"

    else:
        return

    result = await generate(prompt)

    await loading.edit_text(result)

    user_balance[uid] = user_balance.get(uid, START_BALANCE) - UNIT_COST
    user_state[uid] = None

# 💎 PRO оплата
@dp.message_handler(lambda m: m.text == "💎 PRO")
async def pro(message: types.Message):
    await bot.send_invoice(
        chat_id=message.chat.id,
        title="PRO доступ",
        description="Безлимитный доступ к TokGenBot",
        payload="pro_access",
        provider_token=PROVIDER_TOKEN,
        currency="RUB",
        prices=[types.LabeledPrice(label="PRO", amount=19900)]
    )

# Оплата
@dp.pre_checkout_query_handler(lambda q: True)
async def checkout(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def success(message: types.Message):
    uid = message.from_user.id

    user_balance[uid] = 999999

    await message.answer("🔥 PRO активирован!")

# Баланс
@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    uid = message.from_user.id
    await message.answer(f"💰 Баланс: {user_balance.get(uid, START_BALANCE)}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)