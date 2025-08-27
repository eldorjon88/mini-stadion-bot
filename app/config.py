import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")


class RegisterStates:
    NAME = 0
    CONTACT = 1
    CONFIRM = 2


class BookStadionStates:
    DATE = 0
    TIME = 1
    CONFIRM = 2
    PAYMENT = 3


config = Config()
register_states = RegisterStates()
booking_stadion_states = BookStadionStates()
