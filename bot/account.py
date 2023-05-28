from re import escape
from datetime import datetime

from aiogram.dispatcher.filters import Text

from main import bot, dp
import database as db
import globals as g
from templates import Messages, Buttons
from menu import button_account
import utility

logger = g.Logger(__name__)


################################
##### * Button handlers * ######
################################


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_NEW.value))
async def button_account_new(message):
    await utility.log_event(message)

    if await db.get_user(message.from_user.id):
        return

    reply_markup = await utility.keyboard([Buttons.BTN_CANCEL.value])

    await bot.send_message(
        message.from_user.id,
        Messages.REG_FIRST_NAME.escaped(),
        parse_mode="MarkdownV2",
        reply_markup=reply_markup,
    )

    dp.register_message_handler(register)


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT_INFO.value))
async def button_account_info(message):
    await utility.log_event(message)

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
    await utility.log_event(message)

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

    reply_markup = await utility.keyboard(buttons)
    reply = escape("Выберите поле для редактирования:\n\n")

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )


################################
#### * Callback handlers * #####
################################


@dp.callback_query_handler(text_contains="user_edit_")
async def callback_user_edit(callback_query):
    await utility.log_event(callback_query)

    query = callback_query.data
    reply_markup = await utility.keyboard([Buttons.BTN_CANCEL.value])

    if query.endswith("first_name"):
        reply = Messages.REG_FIRST_NAME.escaped()
        field = "first_name"
    elif query.endswith("last_name"):
        reply = Messages.REG_LAST_NAME.escaped()
        field = "last_name"
    elif query.endswith("gender"):
        reply = Messages.REG_GENDER.escaped()
        reply_markup = await utility.keyboard(Buttons.GENDERS.value)
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
    await utility.log_event(message)

    user = g.AppState.user_data.get(message.from_user.id)

    if message.text == Buttons.BTN_CANCEL.value:
        dp.message_handlers.unregister(register)

        g.AppState.user_data.pop(message.from_user.id, None)

        await bot.send_message(message.from_user.id, Messages.REG_CANCELLED.value)
        await button_account(message)

        return

    if not user:
        reply_markup = await utility.keyboard([Buttons.BTN_CANCEL.value])

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

        elif await utility.is_phone_number(message.text) is not True:
            show_preview = False
            reply = Messages.WRONG_PHONE.escaped()
            reply_markup = await utility.keyboard(Buttons.MN_REG.value)
        else:
            show_preview = True
            user["phone"] = message.text

        if show_preview:
            reply = escape(
                "Проверьте правильность введенных данных:\n\n"
            ) + Messages.USER_INFO.format(**user)

            reply_markup = await utility.keyboard(Buttons.MN_REG_CONFIRM.value)

    elif "birthday" in user:
        reply = Messages.REG_PHONE.escaped()
        reply_markup = await utility.keyboard(Buttons.MN_REG.value)

        if message.text == Buttons.BTN_SKIP.value:
            user["email"] = None
        elif await utility.is_email(message.text) is not True:
            reply = Messages.WRONG_EMAIL.escaped()
        else:
            user["email"] = message.text
    elif "gender" in user:
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y").date()
            user["birthday"] = date
            reply = Messages.REG_EMAIL.escaped()
            reply_markup = await utility.keyboard(Buttons.MN_REG.value)
        except ValueError:
            reply = Messages.WRONG_BIRTHDAY.escaped()
            reply_markup = await utility.keyboard([Buttons.BTN_CANCEL.value])

    elif "last_name" in user:
        if message.text not in Buttons.GENDERS.value:
            reply = Messages.WRONG_GENDER.escaped()
            reply_markup = await utility.keyboard(Buttons.MN_REG_GENDER.value)
        else:
            reply = Messages.REG_BIRTHDAY.escaped()
            reply_markup = await utility.keyboard([Buttons.BTN_CANCEL.value])
            user["gender"] = message.text
    elif "first_name" in user:
        if message.text.isalpha():
            user["last_name"] = message.text
            reply = Messages.REG_GENDER.escaped()
            reply_markup = await utility.keyboard(Buttons.MN_REG_GENDER.value)
        else:
            reply = Messages.WRONG_NAME.escaped()
            reply_markup = await utility.keyboard([Buttons.BTN_CANCEL.value])

    await bot.send_message(
        message.from_user.id, reply, reply_markup=reply_markup, parse_mode="MarkdownV2"
    )


async def edit_user(message):
    await utility.log_event(message)

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
        if await utility.is_email(message.text) is True:
            unregister_handler = True
            value = message.text
        else:
            reply = Messages.WRONG_EMAIL.escaped()
    elif field == "phone":
        if await utility.is_phone_number(message.text):
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
