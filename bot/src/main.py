import asyncio
import json
import secrets

from datetime import datetime, timedelta
from re import escape, match

from aiogram import Bot, Dispatcher, executor
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import globals as g
import database as db
import track as tr
from templates import Buttons, Messages


logger = g.Logger(__name__)

bot = Bot(token=g.AppState.Bot.token)
dp = Dispatcher(bot=bot)

# region # ? commands


@dp.message_handler(commands=["start"])
async def start(message):
    await log_event(message)

    if await is_admin(message):
        reply_markup = await keyboard(Buttons.MN_MAIN_ADMIN.value)
    else:
        reply_markup = await keyboard(Buttons.MN_MAIN_USER.value)

    await bot.send_message(
        message.from_user.id, Messages.START.value, reply_markup=reply_markup
    )


# endregion


# region # ? menu
@dp.message_handler(Text(equals=Buttons.BTN_MAIN.value))
async def button_main(message):
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
async def button_account(message):
    await log_event(message)

    if await db.get_user(message.from_user.id):
        reply_markup = await keyboard(Buttons.MN_ACCOUNT_EXIST.value)
    else:
        reply_markup = await keyboard(Buttons.MN_ACCOUNT_NEW.value)

    await bot.send_message(
        message.from_user.id,
        "Вы перешли в личный кабинет.",
        reply_markup=reply_markup,
    )


@dp.message_handler(Text(equals=Buttons.BTN_DURING_RACE.value))
async def button_during_race(message):
    await log_event(message)

    reply_markup = await keyboard(Buttons.MN_DURING_RACE.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_EVENTS.value))
async def button_events(message):
    await log_event(message)

    reply_markup = await keyboard(Buttons.MN_EVENTS.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ADMIN.value))
async def button_admin(message):
    await log_event(message)

    if not await is_admin(message):
        return

    reply_markup = await keyboard(Buttons.MN_ADMIN.value)

    await bot.send_message(
        message.from_user.id,
        "Вы перешли в меню администратора.",
        reply_markup=reply_markup,
    )


# endregion


# region # * account

################################
##### * Button handlers * ######
################################


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_NEW.value))
async def button_account_new(message):
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
async def button_account_info(message):
    await log_event(message)

    user = await db.get_user(message.from_user.id)
    if not user:
        return

    reply = escape("Ваши данные:\n\n") + Messages.USER_INFO.format(
        first_name=user.first_name,
        last_name=user.last_name,
        gender=user.gender,
        birthday=user.birthday.strftime("%d.%m.%Y"),
        email=user.email or "не указан",
        phone=user.phone or "не указан",
    )

    await bot.send_message(
        message.from_user.id,
        reply,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_EDIT.value))
async def button_account_edit(message):
    await log_event(message)

    user = await db.get_user(message.from_user.id)
    if not user:
        return

    buttons = {
        "user_edit_first_name": user.first_name,
        "user_edit_last_name": user.last_name,
        "user_edit_birthday": user.birthday.strftime("%d.%m.%Y"),
        "user_edit_email": user.email or "указать email",
        "user_edit_phone": user.phone or "указать телефон",
    }

    reply_markup = await keyboard(buttons)
    reply = escape("Выберите поле для редактирования:\n\n")

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


################################
#### * Callback handlers * #####
################################


@dp.callback_query_handler(text_contains="user_edit_")
async def callback_user_edit(callback_query):
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


################################
### * Registered handlers * ####
################################


async def register(message):
    await log_event(message)

    user = g.AppState.user_data.get(message.from_user.id)

    if message.text == Buttons.BTN_CANCEL.value:
        dp.message_handlers.unregister(register)

        g.AppState.user_data.pop(message.from_user.id, None)

        await bot.send_message(message.from_user.id, Messages.REG_CANCELLED.value)
        await button_account(message)

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
            await button_account(message)

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
        elif await is_email(message.text) is not True:
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


async def edit_user(message):
    await log_event(message)

    if message.text == Buttons.BTN_CANCEL.value:
        dp.message_handlers.unregister(edit_user)

        await bot.send_message(message.from_user.id, Messages.EDIT_CANCELLED.value)
        await button_account(message)

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
        if await is_email(message.text) is True:
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
        await button_account(message)
    else:
        await bot.send_message(message.from_user.id, reply, parse_mode="MarkdownV2")


# endregion


# region # * events


@dp.message_handler(
    Text(equals=[Buttons.UPCOMING_EVENTS.value, Buttons.ADMIN_UPCOMING_EVENTS.value])
)
async def button_upcoming_events(message):
    await log_event(message)

    events = await db.get_upcoming_races()

    if not events:
        await bot.send_message(message.from_user.id, Messages.NO_EVENTS.value)
        return

    reply = escape("Ближайшие гонки:\n\n")

    events_data = {}

    for event in events:
        start_time = await add_hour_shift(event.start)
        date = start_time.strftime("%d.%m.%Y")

        text = f"{date} - {event.name}"

        if message.text == Buttons.ADMIN_UPCOMING_EVENTS.value and await is_admin(
            message
        ):
            callback_data = f"race_admin_info_{event.name}"
        else:
            callback_data = f"race_info_{event.name}"
        events_data[callback_data] = text

    reply_markup = await keyboard(events_data)

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


# endregion


# region # * race


# region # * location

################################
##### * Button handlers * ######
################################


@dp.message_handler(Text(equals=Buttons.BTN_TRANSLATION.value))
async def button_translation(message):
    await log_event(message)

    race = await db.get_race_by_date()

    if not race:
        await bot.send_message(message.from_user.id, Messages.NO_RACE.value)
        return

    start_time = await add_hour_shift(race.start)
    start_time = start_time.strftime("%H:%M")

    reply = escape(
        f"Сегодня проводится гонка  `{race.name}`\n\n"
        f"Старт:  `{start_time}` \nДистанция:  `{race.distance} км`"
    )

    user = await db.get_user(message.from_user.id)
    if not user:
        await bot.send_message(message.from_user.id, Messages.ONLY_FOR_REGISTERED.value)
        return

    if user not in race.participants:
        await bot.send_message(
            message.from_user.id, Messages.ONLY_FOR_PARTICIPANTS.value
        )
        return

    reply += Messages.TRANSLATION_REQUEST.escaped()
    reply_markup = await keyboard({"location_translation": "Трансляция геолокации"})

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


@dp.message_handler(Text(equals=Buttons.BTN_NEED_HELP.value))
async def button_need_help(message):
    await log_event(message)

    coords = g.AppState.Race.location_data.get(message.from_user.id)

    if not coords:
        # TODO: ask for location with registered next handler
        return

    await bot.send_message(
        message.from_user.id,
        Messages.HELP_WITH_COORDS.value,
    )

    dp.register_message_handler(send_sos_message)


################################
#### * Callback handlers * #####
################################


@dp.callback_query_handler(text_contains="race_info_")
async def callback_race_info(callback_query):
    await log_event(callback_query)

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    start_time = await add_hour_shift(race.start)
    start = start_time.strftime("%d.%m.%Y %H:%M")

    reply = Messages.RACE_INFO.format(
        name=race.name,
        start=start,
        distance=race.distance,
        categories=", ".join(race.categories),
    )

    user = await db.get_user(callback_query.from_user.id)

    if user in race.participants:
        payment = await db.get_payment(callback_query.message.from_user.id, race)

        if not payment:
            text = " | оплата не подтверждена"
        elif not payment.verified:
            text = " | оплата не подтверждена"
        else:
            text = " | оплата подтверждена"

        buttons = {secrets.token_hex(10): "Вы зарегестрированы" + text}
    elif race.registration_open:
        buttons = {
            f"race_choose_category_{race_name}": f"Регистрация на гонку ({race.price}₽)"
        }
    else:
        buttons = {secrets.token_hex(10): "Регистрация закрыта"}

    buttons[f"race_location_{race_name}"] = "Место старта"

    reply_markup = await keyboard(buttons)

    await bot.send_message(
        callback_query.from_user.id,
        reply,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(text_contains="race_location_")
async def callback_race_location(callback_query):
    await log_event(callback_query)

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    latitude, longitude = race.location

    await bot.send_location(callback_query.from_user.id, latitude, longitude)


@dp.callback_query_handler(text_contains="race_choose_category_")
async def callback_race_choose_category(callback_query):
    await log_event(callback_query)

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    user = await db.get_user(callback_query.from_user.id)

    if not (race and user):
        return

    gender_code = user.gender[0].lower()
    categories = [ct for ct in race.categories if ct.lower().startswith(gender_code)]
    buttons = {f"race_register_{race_name};{ct}": ct for ct in categories}

    reply_markup = await keyboard(buttons)
    reply = "Пожалуйста, выберите вашу категорию:"

    await bot.send_message(
        callback_query.from_user.id, reply, reply_markup=reply_markup
    )


@dp.callback_query_handler(text_contains="race_register_")
async def callback_race_register(callback_query):
    await log_event(callback_query)

    race_and_category_names = callback_query.data.rsplit("_", 1)[-1]
    race_name, category = race_and_category_names.split(";")

    race = await db.get_upcoming_race_by_name(race_name)

    if await db.register_to_race(callback_query.from_user.id, race_name, category):
        reply = Messages.PAYMENT_INSTRUCTIONS.format(
            price=race.price,
            phone=g.SBP_PHONE,
            banks=g.SBP_BANKS,
            cred=g.SBP_CRED,
        )

        await bot.send_message(
            callback_query.from_user.id,
            reply,
            parse_mode="MarkdownV2",
        )

    else:
        await bot.send_message(callback_query.from_user.id, "Что-то пошло не так...")


################################
### * Registered handlers * ####
################################


async def send_sos_message(message):
    telegram_username = message.from_user.username
    telegram_username = (
        f"@{telegram_username}" if telegram_username else "скрыт или не указан"
    )
    sos = Messages.SOS_MESSAGE.format(telegram_username=telegram_username)

    dp.message_handlers.unregister(send_sos_message)

    user = await db.get_user(message.from_user.id)

    if user:
        sos += (
            f"Имя:  `{user.first_name}`\nФамилия:  `{user.last_name}`\n"
            f"Телефон:  `{user.phone}`\n"
        )

    sos += f"\nСообщение: {message.text}"

    await bot.send_message(g.TEAM_CHAT_ID, sos, parse_mode="MarkdownV2")

    latitude, longitude = g.AppState.Race.location_data.get(message.from_user.id)

    await bot.send_location(g.TEAM_CHAT_ID, latitude, longitude)


# endregion


# region # ! admin

################################
##### * Button handlers * ######
################################


@dp.message_handler(Text(equals=Buttons.BTN_MANAGE_RACE.value))
async def button_manage_race(message):
    await log_event(message)

    if not await is_admin(message):
        return

    race = await db.get_race_by_date()
    if not race:
        await bot.send_message(
            message.from_user.id,
            Messages.NO_RACE.value,
        )
        return

    start_time = await add_hour_shift(race.start)
    start = start_time.strftime("%d.%m.%Y %H:%M")

    reply = Messages.RACE_INFO.format(
        name=race.name,
        start=start,
        distance=race.distance,
        categories=", ".join(race.categories),
    )

    buttons = {
        f"race_start_init_{race.name}": "Гонка началась",
        f"race_timekeeping_init_{race.name}": "Фиксация результатов",
        f"race_end_init_{race.name}": "Гонка завершена",
    }

    reply_markup = await keyboard(buttons)

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


@dp.message_handler(Text(equals=Buttons.BTN_MANAGE_EVENTS.value))
async def button_admin_events(message):
    await log_event(message)

    if not await is_admin(message):
        return

    reply_markup = await keyboard(Buttons.MN_ADMIN_EVENTS.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


################################
#### * Callback handlers * #####
################################


@dp.callback_query_handler(text_contains="race_timekeeping_init_")
async def callback_race_timepeeking_init(callback_query):
    await log_event(callback_query)

    if not await is_admin(callback_query):
        return

    race = g.AppState.Race.info

    if not race:
        await bot.send_message(callback_query.from_user.id, "Нет активной гонки.")
        return

    reply_markup = await keyboard([Buttons.BTN_COMPLETE.value])

    await bot.send_message(
        callback_query.from_user.id,
        Messages.ADMIN_TIMEKEEPING_INIT.escaped(),
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )

    dp.register_message_handler(timekeeping)


@dp.callback_query_handler(text_contains="race_start_init_")
async def callback_race_start_init(callback_query):
    await log_event(callback_query)

    if not await is_admin(callback_query):
        return

    race = await db.get_race_by_date()

    g.AppState.Race.info = race
    g.AppState.Race.ongoing = True
    start_time = int(datetime.now().timestamp())
    g.AppState.Race.start_time = start_time

    logger.info(f"Race with name {race.name} started at epoch time: {start_time}.")

    json_race_info = {
        "name": race.name,
        "code": race.code,
        "ongoing": True,
        "start_time": start_time,
    }

    with open(g.JSON_RACE_INFO, "w") as f:
        json.dump(json_race_info, f)

    logger.info(f"JSON race info is saved in {g.JSON_RACE_INFO}.")

    await bot.send_message(
        callback_query.from_user.id, Messages.ADMIN_RACE_STARTED.value
    )


@dp.callback_query_handler(text_contains="race_end_init_")
async def callback_race_end_init(callback_query):
    await log_event(callback_query)

    if not await is_admin(callback_query):
        return

    if not (g.AppState.Race.info and g.AppState.Race.ongoing):
        await bot.send_message(
            callback_query.from_user.id,
            Messages.ADMIN_NO_ACTIVE_RACE.value,
        )

    else:
        g.AppState.Race.ongoing = False
        g.AppState.Race.info = None

        await bot.send_message(
            callback_query.from_user.id,
            Messages.ADMIN_RACE_END.value,
        )


@dp.callback_query_handler(text_contains="race_admin_info_")
async def callback_race_admin_info(callback_query):
    await log_event(callback_query)

    if not await is_admin(callback_query):
        return

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    start_time = await add_hour_shift(race.start)
    start = start_time.strftime("%d.%m.%Y %H:%M")

    reply = Messages.RACE_INFO.format(
        name=race.name,
        start=start,
        distance=race.distance,
        categories=", ".join(race.categories),
    )

    status = race.registration_open

    if status:
        buttons = {
            f"race_close_registration_{race_name}": "Закрыть регистрацию",
        }
    else:
        buttons = {f"race_open_registration_{race_name}": "Открыть регистрацию"}

    reply_markup = await keyboard(buttons)

    await bot.send_message(
        callback_query.from_user.id,
        reply,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(text_contains="race_open_registration_")
async def race_open_registration(callback_query):
    await log_event(callback_query)

    if not await is_admin(callback_query):
        return

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    await db.open_registration(race)

    await bot.send_message(callback_query.from_user.id, "Регистрация открыта.")


@dp.callback_query_handler(text_contains="race_close_registration_")
async def race_close_registration(callback_query):
    await log_event(callback_query)

    if not await is_admin(callback_query):
        return

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    race_number_data = await db.close_registration(race)

    reply = "Регистрация закрыта.\nКоличество участников:\n"

    for category, race_numbers in race_number_data.items():
        reply += f"\n`{category}` : {len(race_numbers)}"

    reply = escape(reply)

    await bot.send_message(callback_query.from_user.id, reply, parse_mode="MarkdownV2")


################################
### * Registered handlers * ####
################################


async def timekeeping(message):
    await log_event(message)

    if message.text == Buttons.BTN_COMPLETE.value:
        dp.message_handlers.unregister(timekeeping)
        await button_admin(message)
        return

    try:
        race_number = int(message.text)
    except ValueError:
        logger.error(f"Can't get int race number from {message.text}.")
        return

    finish_time = int(datetime.now().timestamp())
    time_diff = finish_time - g.AppState.Race.start_time
    race_time = timedelta(seconds=time_diff)

    logger.info(
        f"Finish epoch time: {finish_time}, time difference in seconds: {time_diff}, "
        f"race time in human readable: {race_time}."
    )

    race = g.AppState.Race.info

    participant_data = await db.get_participant_by_race_number(race, race_number)

    if not participant_data:
        logger.warning(f"Can't find participant with race number: {race_number}.")

        race_entry = {
            "race_number": race_number,
            "race_time": race_time,
        }
        await bot.send_message(
            message.from_user.id,
            (
                "Участник не найден, результат будет сохранен только с номером. "
                f"Номер: {race_number}\nВремя: {race_time}"
            ),
        )
    else:
        participant, category = participant_data
        full_name = f"{participant.last_name} {participant.first_name}"

        logger.info(f"Found participant: {full_name} with race number: {race_number}.")

        race_entry = {
            "race_number": race_number,
            "race_time": race_time,
            "full_name": full_name,
            "category": category,
        }

        await bot.send_message(
            message.from_user.id,
            (
                f"Имя: {full_name}\nНомер: {race_number}\nКатегория: {category}\nВремя: {race_time}"
            ),
        )

        for telegram_id, user_info in g.AppState.Race.location_data.items():
            if user_info["race_number"] == race_number:
                g.AppState.Race.location_data.pop(telegram_id)
                logger.info(
                    f"User with telegram id {telegram_id} and race number {race_number} removed from location data."
                )
                break

    g.AppState.Race.finishers.append(race_entry)

    logger.info(f"Added participant with race number {race_number} to finishers list.")


# endregion


# region # ? utility


async def is_finished(race_number):
    return any(
        finisher.get("race_number") == race_number
        for finisher in g.AppState.Race.finishers
    )


async def add_hour_shift(utc_time):
    local_time = utc_time + timedelta(hours=g.HOUR_SHIFT)

    return local_time


async def is_phone_number(phone: str):
    pattern = r"^\+7\d{10}$"
    res = match(pattern, phone)
    return res is not None


async def is_email(email: str):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    res = match(pattern, email)
    return res is not None


async def keyboard(buttons: list | dict):
    if isinstance(buttons, list):
        keyboard = ReplyKeyboardMarkup(
            resize_keyboard=True,
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


# endregion


async def on_startup():
    logger.info("Starting up the main module...")
    await tr.prepare_json_tracks()
    bot_info = await bot.get_me()
    logger.info(f"Bot started. Username: {bot_info.username}, ID: {bot_info.id}.")
    g.HOUR_SHIFT = await g.get_time_shift()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    executor.start_polling(dp)
