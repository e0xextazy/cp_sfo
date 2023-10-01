import asyncio
import logging
import os
import sys
import json

import httpx
import requests
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    PollAnswer,
    URLInputFile,
)
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv(".env")

bot = Bot(token=str(os.getenv("BOT_TOKEN")))
BD_API = str(os.getenv("BD_API"))
dp = Dispatcher()
form_router = Router()
dp.include_router(form_router)
N_TRIES = 2
import os


async def save_message_database(chat_id, type, text):
    data = {"chat_id": chat_id, "message": {"type": type, "text": text}}

    async with httpx.AsyncClient() as client:
        response = await client.post(BD_API, json=data)
        if response.status_code == 200:
            logger.info("Message saved successfully")
        else:
            logger.error(f"Failed to save message: {response.text}")


def load_faq(directory="faq_answers"):
    faq_answers = dict()
    for path in os.listdir(directory):
        theme = path.split(".")[0]
        with open(os.path.join(directory, path), "r", encoding='UTF8') as f:
            faq_answers[theme] = f.read()

    return faq_answers


FAQ_ANSWERS = load_faq()


async def on_startup(dp):
    asyncio.create_task(weekly_survey())  # Создание задачи внутри асинхронной функции
    asyncio.create_task(check_document_updates())


class UserState(StatesGroup):
    main_menu = State()
    faq_menu = State()
    message_count = State()
    search_colleague = State()
    wait_course_description = State()


def get_main_menu_markup():
    item1 = InlineKeyboardButton(text="❓ FAQ", callback_data="all_faq")
    item2 = InlineKeyboardButton(
        text="👱‍♀️ Задать вопрос AI-ассистенту 👱‍♀️", callback_data="ask"
    )
    item3 = InlineKeyboardButton(
        text="📁 Получить шаблон документа 📁", callback_data="doc_template"
    )
    item4 = InlineKeyboardButton(text="🔎 Найти коллегу", callback_data="search_colleague")
    item6 = InlineKeyboardButton(text="👨‍🎓 Найти корпоративный курс", callback_data="search_course")

    item5 = InlineKeyboardButton(text="Как пользоваться ботом?", callback_data="None", url="https://youtu.be/5ZBoqkwkMAo")

    markup = InlineKeyboardMarkup(inline_keyboard=[[item1, item4], [item3], [item6], [item2], [item5]])
    return markup


### здесь модель работает
### chat id для поиска истории запросов через DB API (можно просто сделать вид)
def get_answer(chat_id, question):
    # json.loads(r2.text) -> {'response': '60% среднего заработка, если страховой стаж от 6 месяцев до 5 лет; 80% от 5 до 8 лет; 100% более 8 лет.'}
    resp = requests.post("https://9fa3-62-217-190-168.ngrok.io/get_answer",
                        data=json.dumps({"query": question}))
    resp = json.loads(resp.text)['response']
    return resp


def get_contact_info(query):
    return "Почта: ivan_ivanov@smart.ru"


def time_until_next_week():
    return 3600 * 7


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


@form_router.callback_query(lambda c: c.data and c.data.startswith("search_course"))
async def request_colleague_name(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await bot.answer_callback_query(callback_query.id)
    await state.set_state(UserState.wait_course_description)

    item_back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    markup = InlineKeyboardMarkup(inline_keyboard=[[item_back]])
    
    text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\nОпишите, какой навык Вам хотелось бы получить? Какой Ваш текущий уровень знаний в этом вопросе?"
    
    await bot.edit_message_text(
        text,
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )



@form_router.message(UserState.wait_course_description)
async def search_colleague(message: types.Message, state: FSMContext):
    query = message.text
    # contact_info = get_contact_info(query)
    course_info = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
                   f"\n\n<b>Результат поиска:</b>"\
                   f'\n1. <a href="https://stepik.org/course/401/promo">Нейронные сети</a>'\
                   f'\n2. <a href="https://stepik.org/course/50352/info">Нейронные сети и компьютерное зрение</a>'\
                   f'\n3. <a href="https://stepik.org/course/67/promo">Программирование на Python</a>'\
                   
    await state.clear()
    await message.reply(
        course_info,
        reply_markup=None,  # Это уберет кнопку "Назад" после того, как пользователь введет ФИО
        parse_mode="HTML"
    )
    text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\n<b>Имя:</b> {message.from_user.first_name}"\
           f"\n<b>Следующая ЗП:</b> 01.10.2023"\
           f"\n<b>Дней отпуска:</b> 15"\
           f"\n\nДля начала пработы, просто <u>нажми на кнопку</u>  интересующего раздела."
    await message.answer(text=text, reply_markup=get_main_menu_markup(), parse_mode="HTML")


# обновления документов
# не запускается без бэка
async def check_document_updates():
    while True:
        # Проверьте наличие обновлений в документах (например, в базе данных или внешнем сервисе)
        updates = False
        if updates:
            message_text = f"Обновлены следующие документы:\n{updates}"
            for user_id in []:
                await bot.send_message(user_id, message_text)
        await asyncio.sleep(3600 * 8)  # Проверяйте обновления каждый день

    search_colleague = State()  # добавьте это состояние


@form_router.callback_query(lambda c: c.data and c.data.startswith("search_colleague"))
async def request_colleague_name(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await bot.answer_callback_query(callback_query.id)
    await state.set_state(UserState.search_colleague)

    item_back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    markup = InlineKeyboardMarkup(inline_keyboard=[[item_back]])
    
    text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\nВведите <u>ФИО</u> коллеги для поиска"
    
    await bot.edit_message_text(
        text,
        callback_query.from_user.id,
        callback_query.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )


@form_router.message(UserState.search_colleague)
async def search_colleague(message: types.Message, state: FSMContext):
    query = message.text
    # contact_info = get_contact_info(query)
    contact_info = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
                   f"\n\n<b>Результат поиска:</b>"\
                   f"\n<b>ФИО</b>: {query}"\
                   f"\n<b>Почта</b>: cf_pror@mail.ru"\
                   f"\n<b>Часы работы</b>: 10:00-17:00"
    await state.clear()
    await message.reply(
        contact_info,
        reply_markup=None,  # Это уберет кнопку "Назад" после того, как пользователь введет ФИО
        parse_mode="HTML"
    )
    text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\n<b>Имя:</b> {message.from_user.first_name}"\
           f"\n<b>Следующая ЗП:</b> 01.10.2023"\
           f"\n<b>Дней отпуска:</b> 15"\
           f"\n\nДля начала пработы, просто <u>нажми на кнопку</u>  интересующего раздела."
    await message.answer(text=text, reply_markup=get_main_menu_markup(), parse_mode="HTML")


async def weekly_survey():
    while True:
        # Ожидайте начала новой недели
        await asyncio.sleep(time_until_next_week())
        poll_options = ["Легко", "Нормально", "Очень тяжело"]
        for user_id in []:
            await bot.send_poll(user_id, "Как прошла неделя?", poll_options)


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
                   f"\n\n<b>Имя:</b> {message.from_user.first_name}"\
                   f"\n<b>Следующая ЗП:</b> 01.10.2023"\
                   f"\n<b>Дней отпуска:</b> 15"\
                   f"\n\nДля начала пработы, просто <u>нажми на кнопку</u>  интересующего раздела."
    markup = get_main_menu_markup()
    await message.answer(welcome_text, reply_markup=markup, parse_mode="HTML")


### Шаблон документа PDF ###
@dp.callback_query(lambda c: c.data and c.data.startswith("doc_template"))
async def show_doc_template_menu(callback_query: types.CallbackQuery):
    item1 = InlineKeyboardButton(text="🏖️ Отпуск", callback_data="doc_vacation")
    item2 = InlineKeyboardButton(text="👨‍⚕️ Больничный", callback_data="doc_sick_leave")
    item3 = InlineKeyboardButton(text="🛫 Командировка", callback_data="doc_business_trip")
    back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")

    markup = InlineKeyboardMarkup(inline_keyboard=[[item1], [item2], [item3], [back]])

    text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\nВыберите интересующий документ"

    await bot.edit_message_text(
        text=text,
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("doc_"))
async def send_template_document(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    callback_data = callback_query.data
    text = f"👱‍♀️ <b><u>Хьюстон</u></b>\n\n"
    if callback_data == "doc_vacation":
        document_path = "templates/vacation.doc"
        instruction = "Заполните этот шаблон для оформления <u>отпуска</u>."
    elif callback_data == "doc_sick_leave":
        document_path = "templates/sick_leave.doc"
        instruction = "Заполните этот шаблон для оформления <u>больничного</u>."
    elif callback_data == "doc_business_trip":
        document_path = "templates/trip.doc"
        instruction = "Заполните этот шаблон для оформления <u>командировки</u>."
    else:
        return  # Неизвестное значение callback_data
    if document_path.startswith("http"):  # может быть ссылка на файл
        doc = URLInputFile(document_path)
    else:
        doc = FSInputFile(document_path)
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
    )
    await bot.send_document(
        chat_id, document=doc, caption=text+instruction, parse_mode="HTML"
    )  # Отправляем документ
    main_menu_text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\n<b>Имя:</b> {callback_query.from_user.first_name}"\
           f"\n<b>Следующая ЗП:</b> 01.10.2023"\
           f"\n<b>Дней отпуска:</b> 15"\
           f"\n\nДля начала пработы, просто <u>нажми на кнопку</u>  интересующего раздела."
    await bot.send_message(
        callback_query.from_user.id,
        text=main_menu_text,
        reply_markup=get_main_menu_markup(),
        parse_mode="HTML"
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("back_to_main"))
async def back_to_main(callback_query: types.CallbackQuery):
    markup = get_main_menu_markup()
    await bot.edit_message_text(
        "Главное меню:",
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=markup,
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("all_faq"))
async def show_faq_menu(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    item1 = InlineKeyboardButton(text="🏖️ Отпуск", callback_data="faq_vacation")
    item3 = InlineKeyboardButton(text="💰 ЗП", callback_data="faq_salary")
    item4 = InlineKeyboardButton(text="👨‍⚕️ ДМС", callback_data="faq_sick_leave")
    
    item_back = InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
                [item3, item4],
                [item1],
                [item_back]
            ]
        )

    text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\nВыбирите интересующую тему"
    
    await bot.edit_message_text(
        text=text,
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=markup,
        parse_mode="HTML"
    )


async def answer_faq(callback_query: types.CallbackQuery, state: FSMContext, type: str):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(message_count=0)
    await state.set_state(UserState.message_count)
    await bot.delete_message(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
    )
    text = text = f"👱‍♀️ <b><u>Хьюстон</u></b>"\
           f"\n\nЗдесь собраны наиболее популярные вопросы по выбранной категории."
    await bot.send_message(
        text=text,
        parse_mode="HTML",
        chat_id=callback_query.from_user.id
    )
    await bot.send_message(
        callback_query.from_user.id, FAQ_ANSWERS.get(type, "FAQ пуст")
    )
    await bot.send_message(
        callback_query.from_user.id,
        "Главное меню:",
        reply_markup=get_main_menu_markup(),
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("faq_salary"))
async def process_callback_salary(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await answer_faq(callback_query, state, "salary")


@dp.callback_query(lambda c: c.data and c.data.startswith("faq_vacation"))
async def process_callback_salary(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await answer_faq(callback_query, state, "vacation")


@dp.callback_query(lambda c: c.data and c.data.startswith("faq_sick_leave"))
async def process_callback_salary(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await answer_faq(callback_query, state, "sick_leave")


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

    chat_id = message.chat.id
    question = message.text
    await save_message_database(chat_id, "q", question)
    answer = get_answer(chat_id, question)
    await save_message_database(chat_id, "a", answer)

    if message_count == N_TRIES:
        item1 = InlineKeyboardButton(
            text="Да, вернуться в меню", callback_data="back_to_main"
        )
        item2 = InlineKeyboardButton(
            text="Нет, свяжите меня с человеком", callback_data="contact_operator"
        )

        markup = InlineKeyboardMarkup(inline_keyboard=[[item1], [item2]])
        await message.answer(f"Ответ на вопрос: {answer}.")
        await message.answer(
            "Я смогла ответить на ваш вопрос?",
            reply_markup=markup,
        )
        await state.update_data({"message_count": 0})
    else:
        item1 = InlineKeyboardButton(
            text="Да, вернуться в меню", callback_data="back_to_main"
        )

        markup = InlineKeyboardMarkup(inline_keyboard=[[item1]])
        await message.answer(f"Ответ на вопрос: {answer}")

        await message.answer(
            f"Я смогла ответить на ваш вопрос?\n"
            "Если нет, попробуйте уточнить или перефразировать вопрос",
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
    await on_startup(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    asyncio.run(main())
