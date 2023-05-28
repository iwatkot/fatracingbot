from aiogram import types

from main import bot, dp
import database as db
import globals as g
from templates import Messages
import utility

logger = g.Logger(__name__)

################################
#### * Location handlers * #####
################################


@dp.message_handler(content_types=types.ContentType.LOCATION)
async def translation_started(message):
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
async def translation(message):
    if not message.location.live_period:
        return

    coordinates = [message.location.latitude, message.location.longitude]

    logger.debug(
        f"Received live coordinates from telegram id {message.from_user.id}: {coordinates}."
    )

    race = g.AppState.Race.info

    if not race:
        logger.debug(
            "Live coordinates received, but there's no active race at the moment."
        )
        return

    if not g.AppState.Race.location_data.get(message.from_user.id):
        logger.debug(
            f"User {message.from_user.id} is not in location_data, will create it."
        )

        user = await db.get_user(message.from_user.id)
        if not user:
            logger.warning(
                f"Can't find the user with telegram id {message.from_user.id} in database."
            )
            return

        try:
            category, race_number = await db.get_participant_info(
                race, message.from_user.id
            )
        except Exception:
            logger.warning(
                f"Can't find the user {user.first_name} {user.last_name} in participants list."
            )
            return

        if await utility.is_finished(race_number):
            logger.debug(
                f"User {message.from_user.id} already finished, will not save coordinates."
            )
            return

        user_info = {
            "full_name": f"{user.last_name} {user.first_name}",
            "category": category,
            "race_number": race_number,
            "coordinates": coordinates,
        }

        g.AppState.Race.location_data[message.from_user.id] = user_info

        logger.debug(f"User info saved in global state: {user_info}.")
    else:
        user_info = g.AppState.Race.location_data[message.from_user.id]
        race_number = user_info["race_number"]

        if await utility.is_finished(race_number):
            logger.debug(
                f"User {message.from_user.id} already finished, will not save coordinates."
            )
            return

        logger.debug(
            f"User {message.from_user.id} is in location_data, will update coordinates."
        )

        g.AppState.Race.location_data[message.from_user.id]["coordinates"] = coordinates


################################
#### * Callback handlers * #####
################################


@dp.callback_query_handler(text_contains="location_translation")
async def callback_location_translation(callback_query):
    await utility.log_event(callback_query)

    await bot.send_message(
        callback_query.from_user.id,
        Messages.TRANSLATION_TOOLTIP.escaped(),
        parse_mode="MarkdownV2",
    )
