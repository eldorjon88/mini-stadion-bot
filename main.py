from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

import asyncio
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
ADMIN_CHAT_ID = 123456789

START_HOUR = 10
END_HOUR = 23


def db():
    conn = sqlite3.connect("stadion.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE,
        name TEXT,
        phone TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,          -- YYYY-MM-DD
        time TEXT,          -- HH:MM
        status TEXT DEFAULT 'new', -- new, paid, canceled
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, time), -- bitta slotga bitta band qilish
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

def get_user_by_tg(tg_id: int):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, name, phone FROM users WHERE tg_id = ?", (tg_id,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(tg_id: int, name: str, phone: str):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users(tg_id, name, phone) VALUES(?,?,?)", (tg_id, name, phone))
    conn.commit()
    conn.close()

def get_busy_times(date_str: str):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT time FROM bookings WHERE date = ? AND status != 'canceled'", (date_str,))
    times = [r[0] for r in c.fetchall()]
    conn.close()
    return set(times)

def create_booking(user_id: int, date_str: str, time_str: str):
    conn = db()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO bookings(user_id, date, time, status) VALUES(?,?,?, 'new')",
            (user_id, date_str, time_str)
        )
        conn.commit()
        bid = c.lastrowid
    except sqlite3.IntegrityError:
        bid = None
    conn.close()
    return bid

def mark_paid(booking_id: int):
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE bookings SET status = 'paid' WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()

def user_bookings(user_id: int, limit: int = 10):
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT id, date, time, status
        FROM bookings WHERE user_id = ?
        ORDER BY date DESC, time DESC
        LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows


class RegStates(StatesGroup):
    name = State()
    phone = State()

class BookStates(StatesGroup):
    picking_date = State()
    picking_time = State()
    confirming = State()
    paying = State()


def main_menu_kb():
    kb = [
        [KeyboardButton(text="Vaqt"), KeyboardButton(text="Profil")],
        [KeyboardButton(text="Yordam")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Kontaktni yuborish", request_contact=True)]],
        resize_keyboard=True
    )

def dates_kb(days: int = 7):
    today = datetime.now().date()
    rows = []
    row = []
    for i in range(days):
        d = today + timedelta(days=i)
        text = d.strftime("%d.%m (%a)")
        cb = f"date:{d.isoformat()}"
        row.append(InlineKeyboardButton(text=text, callback_data=cb))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Menu", callback_data="to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def times_kb(date_str: str):
    busy = get_busy_times(date_str)
    rows = []
    row = []
    for hour in range(START_HOUR, END_HOUR + 1):
        t = f"{hour:02d}:00"
        taken = t in busy
        label = f"{t} {'❌' if taken else ''}"
        cb = f"time:{date_str}:{t}" if not taken else f"busy:{date_str}:{t}"
        row.append(InlineKeyboardButton(text=label, callback_data=cb))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Sanaga qaytish", callback_data="back_dates")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_kb(date_str: str, time_str: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm:{date_str}:{time_str}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_booking")]
    ])

def payment_kb(booking_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="To'lov qilindi ✅", callback_data=f"paid:{booking_id}")],
        [InlineKeyboardButton(text="⬅️ Menu", callback_data="to_menu")]
    ])


from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    init_db()
    u = get_user_by_tg(message.from_user.id)
    if u is None or not u[1] or not u[2]:
        await state.set_state(RegStates.name)
        await message.answer(
            "Assalomu alaykum! Mini stadion botiga xush kelibsiz.\n"
            "Iltimos, ismingizni yuboring."
        )
    else:
        await message.answer(
            "Asosiy menyu:",
            reply_markup=main_menu_kb()
        )

@dp.message(RegStates.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(RegStates.phone)
    await message.answer("Endi telefon raqamingizni yuboring.", reply_markup=contact_kb())

@dp.message(RegStates.phone, F.contact)
async def reg_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    data = await state.get_data()
    create_user(message.from_user.id, data["name"], phone)
    await state.clear()
    await message.answer("Ro'yxatdan o'tish yakunlandi ✅", reply_markup=main_menu_kb())

@dp.message(RegStates.phone)
async def reg_phone_text(message: Message, state: FSMContext):
    phone = message.text.strip()
    data = await state.get_data()
    create_user(message.from_user.id, data["name"], phone)
    await state.clear()
    await message.answer("Ro'yxatdan o'tish yakunlandi ✅", reply_markup=main_menu_kb())


@dp.message(F.text == "Vaqt")
async def go_book(message: Message, state: FSMContext):
    user = get_user_by_tg(message.from_user.id)
    if user is None:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return
    await state.set_state(BookStates.picking_date)
    await message.answer("Sana tanlang (7 kun ichida):", reply_markup=None)
    await message.answer("Quyidagidan tanlang:", reply_markup=None, reply_markup_inline=dates_kb())

async def send_dates(message: Message):
    await message.answer("Sana tanlang (7 kun ichida):", reply_markup=dates_kb())

@dp.message(F.text == "Profil")
async def profile(message: Message):
    u = get_user_by_tg(message.from_user.id)
    if u is None:
        await message.answer("Avval ro'yxatdan o'ting: /start")
        return
    uid, name, phone = u
    bks = user_bookings(uid, limit=10)
    if bks:
        lines = [f"• #{bid} — <b>{d}</b> {t}  <i>{st}</i>" for (bid, d, t, st) in bks]
        text = "\n".join(lines)
    else:
        text = "Sizda hali band qilingan vaqtlar yo'q."
    await message.answer(
        f" <b>Profil</b>\n"
        f"Ism: <b>{name}</b>\n"
        f"Telefon: <b>{phone}</b>\n\n"
        f"Oxirgi bandlar:\n{text}"
    )

@dp.message(F.text == "Yordam")
async def help_(message: Message):
    await message.answer(
        "Yordam:\n"
        "• Vaqt — o'yin vaqtini band qilish\n"
        "• Profil — ma'lumotlar va bandlar\n"
        "Savol bo'lsa, /start dan qayta boshlang."
    )
@dp.callback_query(F.data == "to_menu")
async def cb_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await call.answer()

@dp.message(BookStates.picking_date)
async def fallback_date_message(message: Message):
    await send_dates(message)

@dp.callback_query(BookStates.picking_date, F.data.startswith("date:"))
async def pick_date(call: CallbackQuery, state: FSMContext):
    date_str = call.data.split(":", 1)[1]
    await state.update_data(date=date_str)
    await state.set_state(BookStates.picking_time)
    await call.message.edit_text(f"Sana: <b>{date_str}</b>\n\nSoatni tanlang:")
    await call.message.edit_reply_markup(reply_markup=times_kb(date_str))
    await call.answer()

@dp.callback_query(BookStates.picking_time, F.data == "back_dates")
async def back_to_dates(call: CallbackQuery, state: FSMContext):
    await state.set_state(BookStates.picking_date)
    await call.message.edit_text("Sana tanlang (7 kun ichida):")
    await call.message.edit_reply_markup(reply_markup=dates_kb())
    await call.answer()

@dp.callback_query(BookStates.picking_time, F.data.startswith("busy:"))
async def busy_slot(call: CallbackQuery):
    await call.answer("Bu vaqt allaqachon band ❌", show_alert=True)

@dp.callback_query(BookStates.picking_time, F.data.startswith("time:"))
async def pick_time(call: CallbackQuery, state: FSMContext):
    _, date_str, time_str = call.data.split(":")
    await state.update_data(time=time_str)
    await state.set_state(BookStates.confirming)
    await call.message.edit_text(
        f"Tanlangan sana: <b>{date_str}</b>\n"
        f"Tanlangan vaqt: <b>{time_str}</b>\n\n"
        f"Tasdiqlaysizmi?"
    )
    await call.message.edit_reply_markup(reply_markup=confirm_kb(date_str, time_str))
    await call.answer()

@dp.callback_query(BookStates.confirming, F.data == "cancel_booking")
async def cancel_booking(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Bekor qilindi. Menyu:")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await call.answer()

@dp.callback_query(BookStates.confirming, F.data.startswith("confirm:"))
async def confirm_booking(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    date_str = data.get("date")
    time_str = data.get("time")
    user_row = get_user_by_tg(call.from_user.id)
    if not user_row:
        await call.answer("Avval /start", show_alert=True)
        return
    user_id = user_row[0]
    booking_id = create_booking(user_id, date_str, time_str)
    if booking_id is None:
        await call.message.edit_text("Uzr, bu vaqt hozirgina band qilindi. Boshqa vaqtni tanlang.")
        await call.message.edit_reply_markup(reply_markup=times_kb(date_str))
        await state.set_state(BookStates.picking_time)
        await call.answer()
        return

    await state.set_state(BookStates.paying)
    await call.message.edit_text(
        f"Band qilish yaratildi! #{booking_id}\n"
        f"Eldorjon Turamurodov 4916 9903 2048 8445"
        f"Sana: <b>{date_str}</b>\nVaqt: <b>{time_str}</b>\n\n"
        f"Tolovni tasdiqlang."
    )
    await call.message.edit_reply_markup(reply_markup=payment_kb(booking_id))
    await call.answer()

@dp.callback_query(BookStates.paying, F.data.startswith("paid:"))
async def paid_click(call: CallbackQuery, state: FSMContext):
    booking_id = int(call.data.split(":")[1])
    mark_paid(booking_id)

    u = get_user_by_tg(call.from_user.id)
    uid, name, phone = u
    conn = db()
    c = conn.cursor()
    c.execute("SELECT date, time FROM bookings WHERE id = ?", (booking_id,))
    row = c.fetchone()
    conn.close()
    date_str, time_str = row

    admin_text = (
        f"<b>Yangi to'lov</b>\n"
        f"Booking ID: <b>#{booking_id}</b>\n"
        f"Sana/Vaqt: <b>{date_str} {time_str}</b>\n"
        f"Foydalanuvchi: <b>{name}</b> (tel: {phone})\n"
        f"TG: @{call.from_user.username or '—'} | id: {call.from_user.id}"
    )
    try:
        await bot.send_message(ADMIN_CHAT_ID, admin_text)
    except Exception:
        pass

    await call.message.edit_text(
        f"To'lov tasdiqlandi! #{booking_id}\n"
        f"Ko'rishguncha! Menyudan davom etishingiz mumkin."
    )
    await call.message.edit_reply_markup(reply_markup=None)
    await state.clear()
    await call.message.answer("Asosiy menyu:", reply_markup=main_menu_kb())
    await call.answer()

@dp.message()
async def fallthrough(message: Message):
    await message.answer("Menyudan tanlang yoki /start bosing.", reply_markup=main_menu_kb())


async def main():
    init_db()
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
