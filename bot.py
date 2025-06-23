
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import datetime
import csv
import os

import os

API_TOKEN = os.getenv("API_TOKEN")
ADMIN_USERNAME = '@TreshNT'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

DATA_FILE = 'requests.csv'

def save_request(username, starlink_login, gb):
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    new_row = [username, starlink_login, gb, timestamp]
    file_exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Telegram Username', 'Starlink Login', 'GB', 'Timestamp (UTC)'])
        writer.writerow(new_row)

class RequestState(StatesGroup):
    waiting_for_login = State()
    waiting_for_choice = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("👋 Добро пожаловать!\nПожалуйста, введите ваш логин Starlink:")
    await RequestState.waiting_for_login.set()

@dp.message_handler(state=RequestState.waiting_for_login)
async def process_login(message: types.Message, state: FSMContext):
    await state.update_data(starlink_login=message.text.strip())

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in range(2, 31):
        kb.add(KeyboardButton(f"{i} ГБ"))

    await message.answer("Выберите объём интернета:", reply_markup=kb)
    await RequestState.waiting_for_choice.set()

@dp.message_handler(state=RequestState.waiting_for_choice)
async def process_choice(message: types.Message, state: FSMContext):
    try:
        gb = int(message.text.strip().split()[0])
        if not 2 <= gb <= 30:
            raise ValueError
    except:
        await message.answer("Пожалуйста, выберите объём от 2 до 30 ГБ с кнопок ниже.")
        return

    user_data = await state.get_data()
    starlink_login = user_data['starlink_login']
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name

    save_request(username, starlink_login, gb)

    await message.answer(f"✅ Ваш запрос на {gb} ГБ принят. Ожидайте подтверждения администратора.\n\nЛогин: {starlink_login}", reply_markup=types.ReplyKeyboardRemove())

    text = f"🧾 Новый запрос:\nПользователь: {username}\nStarlink логин: {starlink_login}\nЗапрос: {gb} ГБ\nВремя: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    await bot.send_message(chat_id=ADMIN_USERNAME, text=text)

    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
