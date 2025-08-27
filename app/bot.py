from telegram.ext import (
    Updater,
    CommandHandler,
    ConversationHandler,
    MessageHandler, Filters,
)

from .config import config, register_states
from .database import engine, Base
from . import handlers

Base.metadata.create_all(engine)


def run_bot() -> None:
    updater = Updater(config.BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', handlers.start))

    register_conversion_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text("Ro'yxatdan o'tish"), handlers.ask_name)],
        states={
            register_states.NAME: [MessageHandler(Filters.text, handlers.set_name)],
            register_states.CONTACT: [MessageHandler(Filters.contact, handlers.set_contact)],
            register_states.CONFIRM: [
                MessageHandler(Filters.text("Tasdiqlash"), handlers.save_user),
                MessageHandler(Filters.text("Tahrirlash"), handlers.ask_name),
            ]
        },
        fallbacks=[]
    )
    dispatcher.add_handler(register_conversion_handler)

    updater.start_polling()
    updater.idle()

