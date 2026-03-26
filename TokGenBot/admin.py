from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import API_TOKEN, ADMINS

from bot import user_balance

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def is_admin(uid):
    return uid in ADMINS

@dp.message_handler(commands=["admin"])
async def admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.reply("Нет доступа")

    await message.answer("Админка активна")

@dp.message_handler(commands=["add_balance"])
async def add_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)

        user_balance[uid] = user_balance.get(uid, 0) + amount

        await message.answer("Баланс выдан")
    except:
        await message.answer("Ошибка команды")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)