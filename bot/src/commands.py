from main import bot, dp
import globals as g
from templates import Messages, Buttons
import utility

logger = g.Logger(__name__)


@dp.message_handler(commands=["start"])
async def test(message):
    await utility.log_event(message)

    if await utility.is_admin(message):
        reply_markup = await utility.keyboard(Buttons.MN_MAIN_ADMIN.value)
    else:
        reply_markup = await utility.keyboard(Buttons.MN_MAIN_USER.value)

    await bot.send_message(
        message.from_user.id, Messages.START.value, reply_markup=reply_markup
    )
