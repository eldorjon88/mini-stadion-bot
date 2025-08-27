from telegram import Update
from telegram.ext import CallbackContext


def start(update: Update, context: CallbackContext):
    # check user
    update.message.reply_text("salom")
