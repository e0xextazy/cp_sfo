import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, PollAnswer
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv(".env")

bot = Bot(token=str(os.getenv("BOT_TOKEN")))
dp = Dispatcher()
form_router = Router()
dp.include_router(form_router)


class UserState(StatesGroup):
    main_menu = State()
    faq_menu = State()
    message_count = State()


def get_document_updates():
    return False  # заглушка, нужен бэкенд


def get_subscribed_users():
    return []


def get_all_users():
    return []


def get_contact_info(query):
    return ""


def time_until_next_week():
    return 3600 * 7


def get_today_birthdays():
    return []


# Предположим, что у вас есть функция save_poll_answer для сохранения ответов на опросы в базе данных
def save_poll_answer(user_id: int, poll_id: str, option_ids: list):
    # Сохраните ответ на опрос в базе данных
    pass


@dp.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    user_id = poll_answer.user.id
    poll_id = poll_answer.poll_id
    # это список индексов выбранных вариантов ответа
    option_ids = poll_answer.option_ids

    # Сохраните результаты опроса
    save_poll_answer(user_id, poll_id, option_ids)

    # await bot.send_message(user_id, "Ваш ответ на опрос сохранен.")


# обновления документов
async def check_document_updates():
    while True:
        # Проверьте наличие обновлений в документах (например, в базе данных или внешнем сервисе)
        updates = get_document_updates()
        if updates:
            message_text = f"Обновлены следующие документы:\n{updates}"
            for user_id in get_subscribed_users():
                await bot.send_message(user_id, message_text)
        await asyncio.sleep(3600 * 8)  # Проверяйте обновления каждый день


asyncio.create_task(check_document_updates())


# Поиск коллег
@dp.message(Command("search"))
async def search_colleague(message: types.Message):
    query = message.get_args()
    contact_info = get_contact_info(query)
    await message.reply(contact_info)


async def weekly_survey():
    while True:
        # Ожидайте начала новой недели
        await asyncio.sleep(time_until_next_week())
        poll_options = ["Легко", "Нормально", "Очень тяжело"]
        for (
            user_id
        ) in get_all_users():  # функция, которая возвращает список всех пользователей
            await bot.send_poll(user_id, "Как прошла неделя?", poll_options)


asyncio.create_task(weekly_survey())


async def birthday_greetings():
    while True:
        # Проверьте, есть ли сегодня у кого-то день рождения
        birthdays = get_today_birthdays()
        for birthday_person in birthdays:
            message_text = f"С днем рождения, {birthday_person['name']}! 🎂"
            for user_id in get_all_users():
                await bot.send_message(user_id, message_text)
        await asyncio.sleep(86400)  # Проверяйте дни рождения каждый день


asyncio.create_task(birthday_greetings())


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    item1 = InlineKeyboardButton(text="Ответы на FAQ", callback_data="faq")
    item2 = InlineKeyboardButton(
        text="Задать вопрос AI-ассистенту", callback_data="ask"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[[item1], [item2]])
    await message.answer("Главное меню:", reply_markup=markup)


@dp.callback_query(lambda c: c.data and c.data.startswith("back_to_main"))
async def back_to_main(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    item1 = InlineKeyboardButton(text="Ответы на FAQ", callback_data="faq")
    item2 = InlineKeyboardButton(
        text="Задать вопрос AI-ассистенту", callback_data="ask"
    )

    markup = InlineKeyboardMarkup(inline_keyboard=[[item1], [item2]])
    await bot.edit_message_text(
        "Главное меню:",
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=markup,
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("faq"))
async def show_faq_menu(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    item1 = InlineKeyboardButton(text="Отпуск", callback_data="vacation")
    item2 = InlineKeyboardButton(text="Больничный", callback_data="sick_leave")
    item3 = InlineKeyboardButton(text="ЗП", callback_data="salary")
    item_back = InlineKeyboardButton(text="Назад", callback_data="back_to_main")
    markup = InlineKeyboardMarkup(inline_keyboard=[[item_back, item1], [item2, item3]])
    await bot.edit_message_text(
        "Выберите интересующую тему:",
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=markup,
    )


# пример обработки кнопки
@dp.callback_query(lambda c: c.data and c.data.startswith("salary"))
async def process_callback_salary(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(message_count=0)
    await state.set_state(UserState.message_count)
    await bot.send_message(callback_query.from_user.id, f"топ 5 вопросов-ответов")


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
