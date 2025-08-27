from .config import config

from telegram.ext import (
    Updater,
    CommandHandler,
)

from . import handlers


def run_bot() -> None:
    updater = Updater(config.BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', handlers.start))

    updater.start_polling()
    updater.idle()

