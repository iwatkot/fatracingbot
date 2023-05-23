import io
import os
import secrets

from enum import Enum
from re import escape, match
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters import Text
from aiocron import crontab
from PIL import Image

import folium
import validators

import globals as g
import database as db

logger = g.Logger(__name__)

bot = Bot(token=g.AppState.Bot.token)

dp = Dispatcher(bot=bot)


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

    NO_RACE = "Сегодня не проводится ни одной гонки."

    ONLY_FOR_REGISTERED = "Эта функция доступна только зарегистрированным участникам."
    ONLY_FOR_PARTICIPANTS = (
        "Эта функция доступна только участникам гонки. "
        "Вы не найдены в списке участников."
    )

    TRANSLATION_REQUEST = (
        "\n\nМы  `убедительно просим`  всех участников  `включить трансляцию геолокации`  на время гонки. "
        "Благодаря этому зрители смогут следить за положением гонщиков на "
        "карте в реальном времени. Помимо этого, в случае возникновения "
        "проблем, организаторы смогут быстрее оказать вам помощь.\n\n"
        "Большое спасибо."
    )

    TRANSLATION_TOOLTIP = (
        "Пожалуйста, убедитесь что Telegram на вашем устройстве, может  получать вашу геолокацию в  `фоновом режиме`. "
        "После этого начните трансляцию геолокации для бота.\n"
        "Бот ответит вам только на начало трансляции, затем данные будут использованы для обновления "
        "вашего положения на карте и таблице лидеров."
    )
    TRANSLATION_LIVE = (
        "Бот начал получать ваши геоданные. Убедитесь, что Telegram может получать вашу "
        "геолокацию в  `фоновом режиме`  и  `не отключайте трансляцию`  до окончания гонки. Спасибо."
    )
    TRANSLATION_NOT_LIVE = (
        "Вы прислали боту свое местоположение, но  `не включили трансляцию`  геолокации. "
        "Пожалуйста, включите трансляцию геолокации, иначе бот не сможет получать ваши данные."
    )

    NO_EVENTS = "В ближайшее время не запланировано ни одной гонки."
    RACE_INFO = (
        "`{name}`\n\nСтарт:  `{start}`\nДистанция:  `{distance} км`\n"
        "Категории:  {categories}"
    )

    PAYMENT_INSTRUCTIONS = (
        "Вы добавлены в список участников гонки.\n"
        "Пожалуйста,  `оплатите участие`  в гонке, в противном случае мы не гарантируем наличие доступного слота.\n\n"
        "Сумма к оплате:  `{price}`\nНомер телефона для СБП:  `{phone}`\n"
        "Список банков:  `{banks}`\nПолучатель:  `{cred}`\n\n"
        "Вы получите сообщение от бота, когда платеж будет подтвержден. "
        "Обратите внимание, что платежи обрабатываются в ручном режиме, подтверждение может занять некоторое время."
    )

    HELP_WITH_COORDS = (
        "Бот уже знает ваше местоположение, пожалуйста кратко сообщите что у вас случилось. "
        "Ваше сообщение с координатами будет отправлено организаторам и мы постараемся помочь вам как можно скорее."
    )

    HELP_NO_COORDS = ""  # TODO: Add text.

    SOS_MESSAGE = (
        "🚨 Поступил запрос помощи.\n\nTelegram username: {telegram_username}\n"
    )

    def format(self, *args, **kwargs):
        return escape(self.value.format(*args, **kwargs))

    def escaped(self):
        return escape(self.value)


class Buttons(Enum):
    # * Context buttons.
    BTN_CANCEL = "Отмена"
    BTN_SKIP = "Пропустить"
    BTN_CONFIRM = "Подтвердить"
    BTN_GENDER_M = "Мужской"
    BTN_GENDER_F = "Женский"
    GENDERS = [BTN_GENDER_M, BTN_GENDER_F]

    # * Main menu buttons.
    BTN_ACCOUNT = "Личный кабинет"
    BTN_DURING_RACE = "Во время гонки"
    BTN_EVENTS = "Мероприятия"
    BTN_INFO = "Информация"
    BTN_MAIN = "Главное меню"
    BTN_ADMIN = "Администрирование"

    # * Account menu buttons.
    BTN_ACCOUNT_NEW = "Регистрация"
    BTN_ACCOUNT_INFO = "Мои данные"
    BTN_ACCOUNT_EDIT = "Редактировать"

    # * During race menu buttons.
    BTN_TRANSLATION = "Трансляция геолокации"
    BTN_LEADERBOARD = "Таблица лидеров"
    BTN_YOUR_STATUS = "Ваши показатели"
    BTN_NEED_HELP = "Мне нужна помощь"

    # * Events menu buttons.
    UPCOMING_EVENTS = "Предстоящие гонки"

    # * Main menus.
    MN_MAIN_USER = [BTN_ACCOUNT, BTN_DURING_RACE, BTN_EVENTS, BTN_INFO, BTN_ADMIN]
    MN_MAIN_ADMIN = [
        BTN_ACCOUNT,
        BTN_DURING_RACE,
        BTN_EVENTS,
        BTN_INFO,
        BTN_ADMIN,
        BTN_ADMIN,
    ]

    # * Account menus.
    MN_ACCOUNT_NEW = [BTN_ACCOUNT_NEW, BTN_MAIN]
    MN_ACCOUNT_EXIST = [BTN_ACCOUNT_INFO, BTN_ACCOUNT_EDIT, BTN_MAIN]
    MN_REG = [BTN_CANCEL, BTN_SKIP]
    MN_REG_GENDER = [BTN_GENDER_M, BTN_GENDER_F, BTN_CANCEL]
    MN_REG_CONFIRM = [BTN_CONFIRM, BTN_CANCEL]

    # * During race menu.
    MN_DURING_RACE = [
        BTN_TRANSLATION,
        BTN_LEADERBOARD,
        BTN_YOUR_STATUS,
        BTN_NEED_HELP,
        BTN_MAIN,
    ]

    # * Events menu.
    MN_EVENTS = [UPCOMING_EVENTS, BTN_MAIN]


#####################################
##### * Handlers for /commands ######
#####################################


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


#####################################
#### * Handlers for menu buttons ####
#####################################


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


@dp.message_handler(Text(equals=Buttons.BTN_DURING_RACE.value))
async def button_during_race(message: types.Message()):
    await log_event(message)

    reply_markup = await keyboard(Buttons.MN_DURING_RACE.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_EVENTS.value))
async def button_events(message: types.Message):
    await log_event(message)

    reply_markup = await keyboard(Buttons.MN_EVENTS.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


#####################################
#### * Account buttons handlers #####
#####################################


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

    for key, value in user.items():
        if not value:
            user[key] = "не указан"
        if key == "birthday":
            user[key] = value.strftime("%d.%m.%Y")

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

        if key == "birthday":
            value = value.strftime("%d.%m.%Y")

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


#####################################
## * During race buttons handlers ###
#####################################


@dp.message_handler(Text(equals=Buttons.BTN_TRANSLATION.value))
async def button_translation(message: types.Message):
    await log_event(message)

    race = await db.get_race_by_date()

    if not race:
        await bot.send_message(message.from_user.id, Messages.NO_RACE.value)
        return

    reply = escape(
        f"Сегодня проводится гонка  `{race.name}`\n\n"
        f"Старт:  `{datetime.strftime(race.start, '%H:%M')}` \nДистанция:  `{race.distance} км`"
    )

    #####################################
    #### ! UNCOMMENT AFTER TDS RACE #####
    #####################################
    # user = await db.get_user(message.from_user.id)
    # if not user:
    #    await bot.send_message(message.from_user.id, Messages.ONLY_FOR_REGISTERED.value)
    #    return
    #
    # if user not in race.participants:
    #    await bot.send_message(
    #        message.from_user.id, Messages.ONLY_FOR_PARTICIPANTS.value
    #    )
    #    return
    #####################################
    ### ! ENDBLOCK UNCOMMENT AFTER TDS ##
    #####################################

    reply += Messages.TRANSLATION_REQUEST.escaped()
    reply_markup = await keyboard({"location_translation": "Трансляция геолокации"})

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


@dp.message_handler(Text(equals=Buttons.BTN_NEED_HELP.value))
async def button_need_help(message: types.Message):
    await log_event(message)

    coords = g.AppState.location_data.get(message.from_user.id)

    if not coords:
        # TODO: ask for location with registered next handler
        return

    await bot.send_message(
        message.from_user.id,
        Messages.HELP_WITH_COORDS.value,
    )

    dp.register_message_handler(send_sos_message)


#####################################
##### * Events buttons handlers #####
#####################################


@dp.message_handler(Text(equals=Buttons.UPCOMING_EVENTS.value))
async def button_upcoming_events(message: types.Message):
    await log_event(message)

    events = await db.get_upcoming_races()

    if not events:
        await bot.send_message(message.from_user.id, Messages.NO_EVENTS.value)
        return

    reply = escape("Ближайшие гонки:\n\n")

    events_data = {}

    for event in events:
        event = event.to_mongo()
        date = event["start"].strftime("%d.%m.%Y")
        text = f"{date} - {event['name']}"
        callback_data = f"race_info_{event['name']}"
        events_data[callback_data] = text

    reply_markup = await keyboard(events_data)

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


#####################################
####### * Location handlers #########
#####################################


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def translation_started(message: types.Message):
    if message.location.live_period:
        logger.info(f"User {message.from_user.id} started live location translation.")

        await bot.send_message(
            chat_id=message.from_user.id,
            text=Messages.TRANSLATION_LIVE.escaped(),
            parse_mode="MarkdownV2",
        )
    else:
        logger.warning(f"User {message.from_user.id} sent NOT live location.")

        await bot.send_message(
            chat_id=message.from_user.id,
            text=Messages.TRANSLATION_NOT_LIVE.escaped(),
            parse_mode="MarkdownV2",
        )


@dp.edited_message_handler(content_types=types.ContentType.LOCATION)
async def translation(message: types.Message):
    if not message.location.live_period:
        return

    logger.info(
        f"User {message.from_user.id} sent live location. "
        f"Lat: {message.location.latitude}, Lon: {message.location.longitude}"
    )

    g.AppState.location_data[message.from_user.id] = [
        message.location.latitude,
        message.location.longitude,
    ]

    logger.debug(
        f"Saved location data for user {message.from_user.id} in global state."
    )


#####################################
######## * Crontab handlers #########
#####################################

LAT = 36.6277
LON = 31.765989


@crontab(g.MAP_TICKRATE)
async def map_update():
    logger.debug("Crontab rule started...")

    #####################################
    #### ? How to clear global state? ###
    #####################################

    if not g.AppState.location_data:
        return

    #####################################
    ### ! MOSTLY FOR DEBUGGING PURPOSE ##
    #####################################

    m = folium.Map(location=[LAT, LON], zoom_start=13)
    for telegram_id, coords in g.AppState.location_data.items():
        folium.Marker(coords, popup=telegram_id).add_to(m)

    logger.debug(f"Map created, added {len(g.AppState.location_data)} markers.")

    img_data = m._to_png(5)
    img = Image.open(io.BytesIO(img_data))

    img_path = os.path.join(g.TMP_DIR, "map.png")

    img.save(img_path)

    logger.debug(f"Map image saved to {img_path}, trying to send...")

    photo = InputFile(img_path)

    await bot.send_photo(g.DEBUG_CHAT_ID, photo)


#####################################
######## * Callback handlers ########
#####################################


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


@dp.callback_query_handler(text_contains="location_translation")
async def callback_location_translation(callback_query: types.CallbackQuery):
    await log_event(callback_query)

    await bot.send_message(
        callback_query.from_user.id,
        Messages.TRANSLATION_TOOLTIP.escaped(),
        parse_mode="MarkdownV2",
    )


@dp.callback_query_handler(text_contains="race_info_")
async def callback_race_info(callback_query: types.CallbackQuery):
    await log_event(callback_query)

    race_name = callback_query.data.rsplit("_", 1)[-1]
    race = await db.get_upcoming_race_by_name(race_name)

    race_json = race.to_mongo()

    race_json["start"] = race_json["start"].strftime("%d.%m.%Y %H:%M")
    race_json["categories"] = ", ".join(race_json["categories"])

    reply = Messages.RACE_INFO.format(**race_json)

    user = await db.get_user(callback_query.from_user.id)

    if user in race.participants:
        payment = await db.get_payment(callback_query.message.from_user.id, race)

        if not payment:
            text = " | оплата не подтверждена"
        elif not payment.verified:
            text = " | оплата не подтверждена"
        else:
            text = " | оплата подтверждена"

        button = {secrets.token_hex(10): "Вы зарегестрированы" + text}
    elif race.registration_open:
        button = {
            f"race_choose_category_{race_name}": f"Регистрация на гонку ({race.price}₽)"
        }
    else:
        button = {secrets.token_hex(10): "Регистрация закрыта"}

    reply_markup = await keyboard(button)

    await bot.send_message(
        callback_query.from_user.id,
        reply,
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )


@dp.callback_query_handler(text_contains="race_choose_category_")
async def callback_race_choose_category(callback_query: types.CallbackQuery):
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
async def callback_race_register(callback_query: types.CallbackQuery):
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


#####################################
####### * Registered handlers #######
#####################################


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


async def send_sos_message(message: types.Message):
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

    latitude, longitude = g.AppState.location_data.get(message.from_user.id)

    await bot.send_location(g.TEAM_CHAT_ID, latitude, longitude)


#####################################
######## * Utility functions ########
#####################################


async def get_user_json(telegram_id):
    user = await db.get_user(telegram_id)
    if not user:
        return

    user = user.to_mongo()
    user["email"] = user.get("email")
    user["phone"] = user.get("phone")
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
