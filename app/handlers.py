from telegram import (
    Update,
    ReplyKeyboardMarkup, KeyboardButton,
)
from telegram.ext import CallbackContext
from sqlalchemy.orm import Session

from .database import LocalSession
from .models import User


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    update.message.reply_text("Assalomu alaykum,\n\n" \
    "Bu bot orqali mini futbol stadion band qilishingiz mumkin.")

    with LocalSession() as session:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        if user:
            send_menu(update, context)
        else:
            send_register_message(update, context)


def send_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot.send_message(
        chat_id=user.id,
        text="Bosh menu",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("Stadion band qilish")],
                [
                    KeyboardButton("Yordam"),
                    KeyboardButton("Profilim"),
                ]
            ],
            resize_keyboard=True
        )
    )


def send_register_message(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot.send_message(
        chat_id=user.id,
        text="Botdan foydalanish uchun ro'yxatdan o'ting",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("Ro'yxatdan o'tish")],
            ],
            resize_keyboard=True
        )
    )
