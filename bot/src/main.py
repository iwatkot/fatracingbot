import asyncio
import os

from aiogram import Bot, Dispatcher, executor

import globals as g


logger = g.Logger(__name__)

bot = Bot(token=g.AppState.Bot.token)
dp = Dispatcher(bot=bot)


async def on_startup():
    logger.info("Starting up the main module...")
    # await tr.prepare_json_tracks()
    bot_info = await bot.get_me()
    logger.info(f"Bot started. Username: {bot_info.username}, ID: {bot_info.id}.")
    g.HOUR_SHIFT = await g.get_time_shift()


async def clean_up():
    logger.debug("Cleaning up JSON and map files...")

    deleted = 0
    for filename in os.listdir(g.JSON_DIR):
        os.remove(os.path.join(g.JSON_DIR, filename))
        deleted += 1

    logger.debug(f"Deleted {deleted} files from {g.JSON_DIR}.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    loop.run_until_complete(clean_up())
    executor.start_polling(dp)
