from re import escape

from aiogram.dispatcher.filters import Text

from main import bot, dp
import database as db
import globals as g
from templates import Messages, Buttons
import utility

logger = g.Logger(__name__)


@dp.message_handler(
    Text(equals=[Buttons.UPCOMING_EVENTS.value, Buttons.ADMIN_UPCOMING_EVENTS.value])
)
async def button_upcoming_events(message):
    await utility.log_event(message)

    events = await db.get_upcoming_races()

    if not events:
        await bot.send_message(message.from_user.id, Messages.NO_EVENTS.value)
        return

    reply = escape("Ближайшие гонки:\n\n")

    events_data = {}

    for event in events:
        start_time = await utility.add_hour_shift(event.start)
        date = start_time.strftime("%d.%m.%Y")

        text = f"{date} - {event.name}"

        if (
            message.text == Buttons.ADMIN_UPCOMING_EVENTS.value
            and await utility.is_admin(message)
        ):
            callback_data = f"race_admin_info_{event.name}"
        else:
            callback_data = f"race_info_{event.name}"
        events_data[callback_data] = text

    reply_markup = await utility.keyboard(events_data)

    await bot.send_message(
        message.from_user.id, reply, parse_mode="MarkdownV2", reply_markup=reply_markup
    )
