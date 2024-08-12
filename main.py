import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
ADMIN_ID = 7021260028
TOKEN = "7464216992:AAFm7-aKgBZJbqLlDrIFdbs5GFZFbHlLg9g"
bot = Bot(token=TOKEN)
dp = Dispatcher()


class ReplyState(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Написать в поддержку",
        callback_data="writing_support")
    )
    await message.answer(
        "Что хотите шеф",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "writing_support")
async def w_support(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('Отправьте сообщение, которое хотите передать саппорту')
    await state.set_state(ReplyState.waiting_for_message)


@dp.message(ReplyState.waiting_for_message)
async def receive_feedback(message: types.Message, state: FSMContext):
    user_data = {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'first_name': message.from_user.first_name,
        'message': message.text
    }
    await state.update_data(user_data=user_data)

    keyboard = InlineKeyboardBuilder()
    keyboard.add(types.InlineKeyboardButton(text="Ответить", callback_data=f"reply_{message.from_user.id}"))

    admin_message = (
        f"Новое сообщение от пользователя @{message.from_user.username} ({message.from_user.first_name}):\n\n"
        f"{message.text}"
    )
    await bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard.as_markup())
    await message.answer("Ваше сообщение отправлено админу.")
    await state.clear()


@dp.callback_query(F.data.startswith('reply_'))
async def ask_for_reply(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.data.split('_')[1]
    await state.update_data(reply_to_user_id=user_id)
    await callback_query.message.answer("Напишите ваш ответ:")
    await state.set_state(ReplyState.waiting_for_reply)


@dp.message(ReplyState.waiting_for_reply)
async def send_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['reply_to_user_id']
    await bot.send_message(user_id, f"Ответ от админа:\n\n{message.text}")
    await message.answer("Ваш ответ отправлен.")
    await state.clear()


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
