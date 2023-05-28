import json
from re import escape
from datetime import datetime, timedelta

from aiogram.dispatcher.filters import Text

from main import bot, dp, clean_up
import database as db
import globals as g
from templates import Messages, Buttons
from menu import button_admin
import utility

logger = g.Logger(__name__)

################################
##### * Button handlers * ######
################################


@dp.message_handler(Text(equals=Buttons.BTN_MANAGE_RACE.value))
async def button_manage_race(message):
    await utility.log_event(message)

    if not await utility.is_admin(message):
        return

    race = await db.get_race_by_date()
    if not race:
        await bot.send_message(
            message.from_user.id,
            Messages.NO_RACE.value,
        )
        return

    start_time = await utility.add_hour_shift(race.start)
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

    reply_markup = await utility.keyboard(buttons)

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


@dp.message_handler(Text(equals=Buttons.BTN_MANAGE_EVENTS.value))
async def button_admin_events(message):
    await utility.log_event(message)

    if not await utility.is_admin(message):
        return

    reply_markup = await utility.keyboard(Buttons.MN_ADMIN_EVENTS.value)

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
    await utility.log_event(callback_query)

    if not await utility.is_admin(callback_query):
        return

    race = g.AppState.Race.info

    if not race:
        await bot.send_message(callback_query.from_user.id, "Нет активной гонки.")
        return

    reply_markup = await utility.keyboard([Buttons.BTN_COMPLETE.value])

    await bot.send_message(
        callback_query.from_user.id,
        Messages.ADMIN_TIMEKEEPING_INIT.escaped(),
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )

    dp.register_message_handler(timekeeping)


@dp.callback_query_handler(text_contains="race_start_init_")
async def callback_race_start_init(callback_query):
    await utility.log_event(callback_query)

    if not await utility.is_admin(callback_query):
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
    await utility.log_event(callback_query)

    if not await utility.is_admin(callback_query):
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

    await clean_up()


@dp.callback_query_handler(text_contains="race_admin_info_")
async def callback_race_admin_info(callback_query):
    await utility.log_event(callback_query)

    if not await utility.is_admin(callback_query):
        return

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    start_time = await utility.add_hour_shift(race.start)
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

    reply_markup = await utility.keyboard(buttons)

    await bot.send_message(
        callback_query.from_user.id,
        reply,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(text_contains="race_open_registration_")
async def race_open_registration(callback_query):
    await utility.log_event(callback_query)

    if not await utility.is_admin(callback_query):
        return

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    await db.open_registration(race)

    await bot.send_message(callback_query.from_user.id, "Регистрация открыта.")


@dp.callback_query_handler(text_contains="race_close_registration_")
async def race_close_registration(callback_query):
    await utility.log_event(callback_query)

    if not await utility.is_admin(callback_query):
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
    await utility.log_event(message)

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
