import secrets
from re import escape

from aiogram.dispatcher.filters import Text

from main import bot, dp
import database as db
import globals as g
from templates import Messages, Buttons
import utility

logger = g.Logger(__name__)

################################
##### * Button handlers * ######
################################


@dp.message_handler(Text(equals=Buttons.BTN_TRANSLATION.value))
async def button_translation(message):
    await utility.log_event(message)

    race = await db.get_race_by_date()

    if not race:
        await bot.send_message(message.from_user.id, Messages.NO_RACE.value)
        return

    start_time = await utility.add_hour_shift(race.start)
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
    reply_markup = await utility.keyboard(
        {"location_translation": "Трансляция геолокации"}
    )

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


@dp.message_handler(Text(equals=Buttons.BTN_NEED_HELP.value))
async def button_need_help(message):
    await utility.log_event(message)

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
    await utility.log_event(callback_query)

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

    reply_markup = await utility.keyboard(buttons)

    await bot.send_message(
        callback_query.from_user.id,
        reply,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(text_contains="race_location_")
async def callback_race_location(callback_query):
    await utility.log_event(callback_query)

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    latitude, longitude = race.location

    await bot.send_location(callback_query.from_user.id, latitude, longitude)


@dp.callback_query_handler(text_contains="race_choose_category_")
async def callback_race_choose_category(callback_query):
    await utility.log_event(callback_query)

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    user = await db.get_user(callback_query.from_user.id)

    if not (race and user):
        return

    gender_code = user.gender[0].lower()
    categories = [ct for ct in race.categories if ct.lower().startswith(gender_code)]
    buttons = {f"race_register_{race_name};{ct}": ct for ct in categories}

    reply_markup = await utility.keyboard(buttons)
    reply = "Пожалуйста, выберите вашу категорию:"

    await bot.send_message(
        callback_query.from_user.id, reply, reply_markup=reply_markup
    )


@dp.callback_query_handler(text_contains="race_register_")
async def callback_race_register(callback_query):
    await utility.log_event(callback_query)

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
