from aiogram.dispatcher.filters import Text

from main import bot, dp
import database as db
import globals as g
from templates import Messages, Buttons
import utility

logger = g.Logger(__name__)


@dp.message_handler(Text(equals=Buttons.BTN_MAIN.value))
async def button_main(message):
    await utility.log_event(message)

    if await utility.is_admin(message):
        reply_markup = await utility.keyboard(Buttons.MN_MAIN_ADMIN.value)
    else:
        reply_markup = await utility.keyboard(Buttons.MN_MAIN_USER.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(Buttons.BTN_MAIN.value),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ACCOUNT.value))
async def button_account(message):
    await utility.log_event(message)

    if await db.get_user(message.from_user.id):
        reply_markup = await utility.keyboard(Buttons.MN_ACCOUNT_EXIST.value)
    else:
        reply_markup = await utility.keyboard(Buttons.MN_ACCOUNT_NEW.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_DURING_RACE.value))
async def button_during_race(message):
    await utility.log_event(message)

    reply_markup = await utility.keyboard(Buttons.MN_DURING_RACE.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_EVENTS.value))
async def button_events(message):
    await utility.log_event(message)

    reply_markup = await utility.keyboard(Buttons.MN_EVENTS.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )


@dp.message_handler(Text(equals=Buttons.BTN_ADMIN.value))
async def button_admin(message):
    await utility.log_event(message)

    if not await utility.is_admin(message):
        return

    reply_markup = await utility.keyboard(Buttons.MN_ADMIN.value)

    await bot.send_message(
        message.from_user.id,
        Messages.MENU_CHANGED.format(message.text),
        reply_markup=reply_markup,
        parse_mode="MarkdownV2",
    )
