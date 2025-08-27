from telegram.ext import (
    Updater,
    CommandHandler,
)

from .config import config
from .database import engine, Base
from . import handlers

Base.metadata.create_all(engine)


def run_bot() -> None:
    updater = Updater(config.BOT_TOKEN)

    dispatcher = updater.dispatcher



    dispatcher.add_handler(CommandHandler('start', handlers.start))

    updater.start_polling()
    updater.idle()

