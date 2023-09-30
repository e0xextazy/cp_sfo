import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv(".env")

bot = Bot(token=str(os.getenv("BOT_TOKEN")))
dp = Dispatcher()
form_router = Router()
dp.include_router(form_router)


class UserState(StatesGroup):
    message_count = State()  # state for counting messages


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    item1 = InlineKeyboardButton(text="Отпуск", callback_data="vacation")
    item2 = InlineKeyboardButton(text="Больничный", callback_data="sick_leave")
    item3 = InlineKeyboardButton(text="Задать вопрос", callback_data="ask_question")
    markup = InlineKeyboardMarkup(inline_keyboard=[[item1, item2, item3]])
    await message.answer("Выберите опцию:", reply_markup=markup)


@dp.callback_query(lambda c: c.data and c.data.startswith("ask"))
async def process_callback_kb1btn1(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(message_count=0)
    await state.set_state(UserState.message_count)
    await bot.send_message(callback_query.from_user.id, "Задайте свой вопрос:")


@dp.message(UserState.message_count)
async def process_message(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    message_count = user_data.get("message_count", 0) + 1
    await state.update_data({"message_count": message_count})

    if message_count == 3:
        item1 = InlineKeyboardButton(
            text="Связь с оператором", callback_data="contact_operator"
        )
        markup = InlineKeyboardMarkup(inline_keyboard=[[item1]])
        await message.answer("Хотите связаться с оператором?", reply_markup=markup)
        await state.update_data({"message_count": 0})
    else:
        item1 = InlineKeyboardButton(text="Да, вопрос решен", callback_data="resolved")
        markup = InlineKeyboardMarkup(inline_keyboard=[[item1]])
        await message.answer(
            f"Ответ на вопрос: {message.text}. Мы смогли ответить на ваш вопрос?",
            reply_markup=markup,
        )


@dp.callback_query(lambda c: c.data and c.data.startswith("contact_operator"))
async def process_callback_operator(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Связь с оператором...")


@dp.callback_query(lambda c: c.data and c.data.startswith("contact_operator"))
async def process_resolved(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Связь с оператором...")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
