from telegram import (
    Update,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import CallbackContext
from sqlalchemy.orm import Session

from .database import LocalSession
from .models import User
from .config import register_states


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


def ask_name(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Ismingiz?",
        reply_markup=ReplyKeyboardRemove()
    )

    return register_states.NAME


def set_name(update: Update, context: CallbackContext):
    name = update.message.text.title()

    context.user_data['name'] = name

    update.message.reply_text(
        "Telefon raqamingizni yuboring?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("Yuborish", request_contact=True)]
            ],
            resize_keyboard=True
        )
    )

    return register_states.CONTACT


def set_contact(update: Update, context: CallbackContext):
    contact = update.message.contact
    context.user_data['contact'] = contact.phone_number

    user_data = context.user_data

    text = "Ro'yxatdan o'tish uchun malumotlaringizni tasdiqlang!\n\n" \
    f"Ismingiz: {user_data['name']}\n" \
    f"Telefon raqamingiz: {user_data['contact']}"

    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton("Tasdiqlash"), KeyboardButton("Tahrirlash")]
            ],
            resize_keyboard=True
        )
    )

    return register_states.CONFIRM


def save_user(update: Update, context: CallbackContext):
    user_data = context.user_data
    
    with LocalSession() as session:
        user = User(
            telegram_id=update.effective_user.id,
            name=user_data['name'],
            contact=user_data['contact']
        )
        session.add(user)
        session.commit()

    context.user_data.clear()

    update.message.reply_text(
        "Siz muvaffaqiyatli ro'yxatdan o'tdingiz.",
        reply_markup=ReplyKeyboardRemove()
    )

    # TODO: redirect menu
