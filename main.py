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
ADMIN_IDS = [7021260028]
TOKEN = "7464216992:AAG39lJRIRuPRdQ2ovg8vyiQcJGQnoe8oC0"

dp = Dispatcher()
bot = Bot(token=TOKEN)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
class ReplyState(StatesGroup):
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
async def w_support(callback: types.CallbackQuery):
    await callback.message.answer('Отправьте сообщение, которое хотите передать саппорту')
    await callback.answer()  # Закрываем уведомление о нажатии кнопки


@dp.message()
async def forward_to_admins(message: types.Message):
    # Игнорируем сообщения от админов
    if message.from_user.id in ADMIN_IDS:
        return

    user_id = message.from_user.id
    for admin_id in ADMIN_IDS:
        try:
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Ответить",
                callback_data=f'reply_{user_id}'))

            await bot.send_message(
                admin_id,
                f"Новое сообщение от {message.from_user.full_name} (@{message.from_user.username}):\n\n{message.text}",
                reply_markup=builder.as_markup()
            )

        except Exception as e:
            logging.exception(f"Ошибка при отправке сообщения администратору: {e}")

    await message.reply("Ваше сообщение было успешно отправлено администраторам.")


@dp.callback_query(lambda c: c.data.startswith('reply_'))
async def process_callback_reply(callback: types.CallbackQuery, state: FSMContext):
    user_chat_id = int(callback.data.split('_')[1])
    await state.update_data(user_chat_id=user_chat_id)
    await callback.message.edit_text('Пожалуйста, введите ваш ответ:')
    await state.set_state(ReplyState.waiting_for_reply)


@dp.message(ReplyState.waiting_for_reply)
async def handle_admin_reply(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_chat_id = data.get('user_chat_id')

    # После получения ответа сразу очищаем состояние, чтобы предотвратить неожиданные последующие отправки.
    await state.clear()

    if user_chat_id:
        # Отправляем ответ пользователю
        await bot.send_message(user_chat_id, f"Ответ администратора: {message.text}",
                               reply_markup=ReplyKeyboardRemove())

        # Уведомляем администратора, что ответ отправлен
        await message.answer("Ваш ответ был отправлен пользователю.", reply_markup=ReplyKeyboardRemove())
    else:
        # Если контекст не найден, напоминаем админу, что состояние было сброшено
        await message.answer("Произошла ошибка или время ожидания ответа истекло.")




async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
