from enum import Enum
from re import escape, match
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import Text

import folium
import validators

import globals as g
import database as db

logger = g.Logger(__name__)

bot = Bot(token=g.AppState.Bot.token)

dp = Dispatcher(bot=bot)

latitude = 36.6277
longitude = 31.765989

m = folium.Map(location=[latitude, longitude], zoom_start=13)


class Messages(Enum):
    START = (
        "Привет! Это официальный Telegram бот FATRACING.\n"
        "Он позволяет регистрироваться на гонки, а также получать информацию о них.\n"
        "Помимо этого с помощью бота вы можете получить доступ к своим "
        "результатам на состоявшихся мероприятиях.\n\n"
        "Пожалуйста, воспользуйтесь меню для регистрации, если вы этого еще не сделали. Это займет всего минуту."
    )

    MENU_CHANGED = "Вы перешли в раздел  `{}`"

    REG_FIRST_NAME = "Пожалуйста, введите ваше имя. Это обязательное поле."
    REG_LAST_NAME = "Пожалуйста, введите вашу фамилию. Это обязательное поле."
    REG_GENDER = "Пожалуйста, укажите ваш пол. Это обязательное поле."
    REG_BIRTHDAY = "Пожалуйста, введите вашу дату рождения в формате `ДД.ММ.ГГГГ`. Это обязательное поле."
    REG_EMAIL = "Пожалуйста, введите вашу электронную почту. Это необязательное поле."
    REG_PHONE = "Пожалуйста, введите ваш номер телефона в формате `+7XXXXXXXXXX`. Это необязательное поле."

    REG_CANCELLED = "Регистрация отменена."
    REG_SUCCESS = "Регистрация успешно завершена. Спасибо!"
    WRONG_GENDER = "Неверный формат. Пожалуйста, введите ваш пол."
    WRONG_EMAIL = "Неверный формат. Пожалуйста, введите вашу электронную почту."
    WRONG_NAME = "Неверный формат. Пожалуйста, введите ваше имя."
    WRONG_BIRTHDAY = "Неверный формат. Пожалуйста, введите вашу дату рождения."
    WRONG_PHONE = "Неверный формат. Пожалуйста, введите ваш номер телефона."

    USER_INFO = (
        "`Имя:` {first_name}\n`Фамилия:` {last_name}\n"
        "`Пол:` {gender}\n`Дата рождения:` {birthday}\n"
        "`Email:` {email}\n`Телефон:` {phone}\n"
    )

    EDIT_CANCELLED = "Редактирование отменено."
    EDIT_SUCCESS = "Редактирование успешно завершено."

    def format(self, *args, **kwargs):
        return escape(self.value.format(*args, **kwargs))

    def escaped(self):
        return escape(self.value)


class Buttons(Enum):
    BTN_CANCEL = "Отмена"
    BTN_SKIP = "Пропустить"
    BTN_CONFIRM = "Подтвердить"

    BTN_ACCOUNT = "Личный кабинет"
    BTN_EVENTS = "Мероприятия"
    BTN_INFO = "Информация"
    BTN_MAIN = "Главное меню"
    BTN_ADMIN = "Администрирование"

    BTN_ACCOUNT_NEW = "Регистрация"
    BTN_ACCOUNT_INFO = "Мои данные"
    BTN_ACCOUNT_EDIT = "Редактировать"

    BTN_GENDER_M = "Мужской"
    BTN_GENDER_F = "Женский"
    GENDERS = [BTN_GENDER_M, BTN_GENDER_F]

    MN_MAIN_USER = [BTN_ACCOUNT, BTN_EVENTS, BTN_INFO, BTN_ADMIN]
    MN_MAIN_ADMIN = [BTN_ACCOUNT, BTN_EVENTS, BTN_INFO, BTN_ADMIN, BTN_ADMIN]

    MN_ACCOUNT_NEW = [BTN_ACCOUNT_NEW, BTN_MAIN]
    MN_ACCOUNT_EXIST = [BTN_ACCOUNT_INFO, BTN_ACCOUNT_EDIT, BTN_MAIN]

    MN_REG = [BTN_CANCEL, BTN_SKIP]
    MN_REG_GENDER = [BTN_GENDER_M, BTN_GENDER_F, BTN_CANCEL]
    MN_REG_CONFIRM = [BTN_CONFIRM, BTN_CANCEL]


@dp.message_handler(commands=["start"])
async def test(message: types.Message):
    await log_event(message)

    if await is_admin(message):
        reply_markup = await keyboard(Buttons.MN_MAIN_ADMIN.value)
    else:
        reply_markup = await keyboard(Buttons.MN_MAIN_USER.value)

    await bot.send_message(
        message.from_user.id, Messages.START.value, reply_markup=reply_markup
    )


@dp.message_handler(Text(equals=Buttons.BTN_MAIN.value))
async def button_main(message: types.Message):
    await log_event(message)

    if await is_admin(message):
        reply_markup = await keyboard(Buttons.MN_MAIN_ADMIN.value)
    else:
        reply_markup = await keyboard(Buttons.MN_MAIN_USER.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(Buttons.BTN_MAIN.value),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT.value))
async def button_account(message: types.Message):
    await log_event(message)

    if await db.get_user(message.from_user.id):
        reply_markup = await keyboard(Buttons.MN_ACCOUNT_EXIST.value)
    else:
        reply_markup = await keyboard(Buttons.MN_ACCOUNT_NEW.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_NEW.value))
async def button_account_new(message: types.Message):
    await log_event(message)

    if await db.get_user(message.from_user.id):
        return

    reply_markup = await keyboard([Buttons.BTN_CANCEL.value])

    await bot.send_message(
        message.from_user.id,
        Messages.REG_FIRST_NAME.escaped(),
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )

    dp.register_message_handler(register)


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_INFO.value))
async def button_account_info(message: types.Message):
    await log_event(message)

    user = await get_user_json(message.from_user.id)
    if not user:
        return

    reply = escape("Ваши данные:\n\n") + Messages.USER_INFO.format(**user)

    await bot.send_message(
        message.from_user.id,
        reply,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_EDIT.value))
async def button_account_edit(message: types.Message):
    await log_event(message)

    user = await get_user_json(message.from_user.id)
    if not user:
        return

    buttons = {}

    for key, value in user.items():
        if key == "telegram_id":
            continue
        if value is None:
            if key == "email":
                value = "указать email"
            elif key == "phone":
                value = "указать телефон"
        key = f"user_edit_{key}"
        buttons[key] = value

    reply_markup = await keyboard(buttons)
    reply = escape("Выберите поле для редактирования:\n\n")

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def first_location(message: types.Message):
    # the user's location is in message.location
    user_location = message.location

    # Check if it's a live location
    if message.location.live_period:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=f"FIRST = LIVE: Your location is {user_location.latitude}, {user_location.longitude}",
        )
    else:
        await message.reply(
            f"NOT LIVE: Your location is {user_location.latitude}, {user_location.longitude}"
        )


@dp.edited_message_handler(content_types=types.ContentType.LOCATION)
async def edited_location(message: types.Message):
    user_location = message.location

    if message.location.live_period:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=f"EDITED = LIVE: Your location is {user_location.latitude}, {user_location.longitude}",
        )

        coords = [user_location.latitude, user_location.longitude]
        save_map(coords)


def save_map(coords):
    folium.Marker(coords, popup="ya pidoras").add_to(m)
    m.save("map.html")


# Callback handlers.


@dp.callback_query_handler(text_contains="user_edit_")
async def callback_user_edit(callback_query: types.CallbackQuery):
    await log_event(callback_query)

    query = callback_query.data
    reply_markup = await keyboard([Buttons.BTN_CANCEL.value])

    if query.endswith("first_name"):
        reply = Messages.REG_FIRST_NAME.escaped()
        field = "first_name"
    elif query.endswith("last_name"):
        reply = Messages.REG_LAST_NAME.escaped()
        field = "last_name"
    elif query.endswith("gender"):
        reply = Messages.REG_GENDER.escaped()
        reply_markup = await keyboard(Buttons.GENDERS.value)
        field = "gender"
    elif query.endswith("birthday"):
        reply = Messages.REG_BIRTHDAY.escaped()
        field = "birthday"
    elif query.endswith("email"):
        reply = Messages.REG_EMAIL.escaped()
        field = "email"
    elif query.endswith("phone"):
        reply = Messages.REG_PHONE.escaped()
        field = "phone"
    else:
        return

    g.AppState.user_edit_field = field
    dp.register_message_handler(edit_user)

    await bot.send_message(
        callback_query.from_user.id,
        reply,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )


# Registered handlers.


async def edit_user(message: types.Message):
    await log_event(message)

    if message.text == Buttons.BTN_CANCEL.value:
        dp.message_handlers.unregister(edit_user)

        await bot.send_message(message.from_user.id, Messages.EDIT_CANCELLED.value)
        await button_main(message)

        return

    unregister_handler = False
    field = g.AppState.user_edit_field

    if field == "first_name":
        if message.text.isalpha():
            unregister_handler = True
            value = message.text
        else:
            reply = Messages.WRONG_NAME.escaped()
    elif field == "last_name":
        if message.text.isalpha():
            unregister_handler = True
            value = message.text
        else:
            reply = Messages.WRONG_NAME.escaped()
    elif field == "gender":
        if message.text in Buttons.GENDERS.value:
            unregister_handler = True
            value = message.text
        else:
            reply = Messages.WRONG_GENDER.escaped()
    elif field == "birthday":
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y").date()
            value = date
            unregister_handler = True
        except ValueError:
            reply = Messages.WRONG_BIRTHDAY.escaped()
    elif field == "email":
        if validators.email(message.text) is True:
            unregister_handler = True
            value = message.text
        else:
            reply = Messages.WRONG_EMAIL.escaped()
    elif field == "phone":
        if await is_phone_number(message.text):
            unregister_handler = True
            value = message.text
        else:
            reply = Messages.WRONG_PHONE.escaped()

    if unregister_handler:
        dp.message_handlers.unregister(edit_user)

        await db.update_user(message.from_user.id, **{field: value})

        await bot.send_message(message.from_user.id, Messages.EDIT_SUCCESS.value)
        await button_main(message)
    else:
        await bot.send_message(message.from_user.id, reply, parse_mode="MarkdownV2")


async def register(message: types.Message):
    await log_event(message)

    user = g.AppState.user_data.get(message.from_user.id)

    if message.text == Buttons.BTN_CANCEL.value:
        dp.message_handlers.unregister(register)

        g.AppState.user_data.pop(message.from_user.id, None)

        await bot.send_message(message.from_user.id, Messages.REG_CANCELLED.value)
        await button_main(message)

        return

    if not user:
        reply_markup = await keyboard([Buttons.BTN_CANCEL.value])

        if message.text.isalpha():
            g.AppState.user_data[message.from_user.id] = {"first_name": message.text}
            reply = Messages.REG_LAST_NAME.escaped()
        else:
            reply = Messages.WRONG_NAME.escaped()

    elif "phone" in user:
        if message.text == Buttons.BTN_CONFIRM.value:
            user["telegram_id"] = message.from_user.id
            await db.new_user(**user)

            await bot.send_message(message.from_user.id, Messages.REG_SUCCESS.value)
            await button_main(message)

            return

    elif "email" in user:
        if message.text == Buttons.BTN_SKIP.value:
            show_preview = True
            user["phone"] = None

        elif await is_phone_number(message.text) is not True:
            show_preview = False
            reply = Messages.WRONG_PHONE.escaped()
            reply_markup = await keyboard(Buttons.MN_REG.value)
        else:
            show_preview = True
            user["phone"] = message.text

        if show_preview:
            reply = escape(
                "Проверьте правильность введенных данных:\n\n"
            ) + Messages.USER_INFO.format(**user)

            reply_markup = await keyboard(Buttons.MN_REG_CONFIRM.value)

    elif "birthday" in user:
        reply = Messages.REG_PHONE.escaped()
        reply_markup = await keyboard(Buttons.MN_REG.value)

        if message.text == Buttons.BTN_SKIP.value:
            user["email"] = None
        elif validators.email(message.text) is not True:
            reply = Messages.WRONG_EMAIL.escaped()
        else:
            user["email"] = message.text
    elif "gender" in user:
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y").date()
            user["birthday"] = date
            reply = Messages.REG_EMAIL.escaped()
            reply_markup = await keyboard(Buttons.MN_REG.value)
        except ValueError:
            reply = Messages.WRONG_BIRTHDAY.escaped()
            reply_markup = await keyboard([Buttons.BTN_CANCEL.value])

    elif "last_name" in user:
        if message.text not in Buttons.GENDERS.value:
            reply = Messages.WRONG_GENDER.escaped()
            reply_markup = await keyboard(Buttons.MN_REG_GENDER.value)
        else:
            reply = Messages.REG_BIRTHDAY.escaped()
            reply_markup = await keyboard([Buttons.BTN_CANCEL.value])
            user["gender"] = message.text
    elif "first_name" in user:
        if message.text.isalpha():
            user["last_name"] = message.text
            reply = Messages.REG_GENDER.escaped()
            reply_markup = await keyboard(Buttons.MN_REG_GENDER.value)
        else:
            reply = Messages.WRONG_NAME.escaped()
            reply_markup = await keyboard([Buttons.BTN_CANCEL.value])

    await bot.send_message(
        message.from_user.id, reply, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


# Utility functions.


async def get_user_json(telegram_id):
    user = await db.get_user(telegram_id)
    if not user:
        return

    user = user.to_mongo()
    user["email"] = user.get("email")
    user["phone"] = user.get("phone")
    user["birthday"] = user.get("birthday").strftime("%Y-%m-%d")
    user.pop("_id")

    return user


async def is_phone_number(phone: str):
    pattern = r"^\+7\d{10}$"
    res = match(pattern, phone)
    return res is not None


async def keyboard(buttons: list | dict):
    if isinstance(buttons, list):
        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
            row_width=2,
        )
        for button in buttons:
            keyboard.add(KeyboardButton(button))

    elif isinstance(buttons, dict):
        keyboard = InlineKeyboardMarkup(
            row_width=2,
        )
        for callback_data, text in buttons.items():
            keyboard.add(InlineKeyboardButton(callback_data=callback_data, text=text))

    return keyboard


async def is_admin(data: dict):
    return data.from_user.id in g.AppState.Bot.admins


async def log_event(data: dict):
    try:
        logger.debug(
            f"Message from {data.from_user.username} with telegram ID {data.from_user.id}: {data.text}"
        )
    except AttributeError:
        logger.debug(
            f"Callback from {data.from_user.username} with telegram ID {data.from_user.id}: {data.data}"
        )


if __name__ == "__main__":
    executor.start_polling(dp)
