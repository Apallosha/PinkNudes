import asyncio
import requests
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8355471659:AAFWRNlxYtww9IgEAvwIee0DlWsmExdhJOg"
CRYPTO_TOKEN = "526004:AAdTiJf7ebmFVMXm2lFxkud339PdvDgcaly"

ADMIN_ID = 5333130126
PRICE_USDT = "2"

PUBLIC_CHANNEL_URL = "https://t.me/+fP9jHqTTGAVkY2Fi"
PRIVATE_CHANNEL_URL = "https://t.me/+GB0H9D7fYN1iOWYy"

USERS_FILE = "users.txt"
# ============================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
HEADERS = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}

invoices = {}
broadcast_mode = False

# ---------- FILE INIT ----------
if not os.path.exists(USERS_FILE):
    open(USERS_FILE, "w").close()

def save_user(user_id: int):
    with open(USERS_FILE, "r+") as f:
        users = set(f.read().splitlines())
        if str(user_id) not in users:
            f.write(f"{user_id}\n")

def load_users():
    with open(USERS_FILE, "r") as f:
        return [int(x) for x in f.read().splitlines() if x.strip()]

# ---------- КНОПКИ ----------
def start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="PinkNudes 🍓", url=PUBLIC_CHANNEL_URL)],
        [InlineKeyboardButton(text="Купить Приватку 🍓", callback_data="buy")]
    ])

def pay_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Проверить оплату", callback_data="check")]
    ])

def private_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍓 Перейти в приватку", url=PRIVATE_CHANNEL_URL)]
    ])

# ---------- CRYPTO ----------
def create_invoice(user_id):
    r = requests.post(
        "https://pay.crypt.bot/api/createInvoice",
        headers=HEADERS,
        json={
            "asset": "USDT",
            "amount": PRICE_USDT,
            "description": "Доступ к приватному каналу",
            "payload": str(user_id)
        }
    )
    return r.json()["result"]

def check_invoice(invoice_id):
    r = requests.get(
        "https://pay.crypt.bot/api/getInvoices",
        headers=HEADERS,
        params={"invoice_ids": invoice_id}
    )
    return r.json()["result"]["items"][0]["status"]

# ---------- START ----------
@dp.message(Command("start"))
async def start(message: Message):
    save_user(message.from_user.id)
    await message.answer(
        "Привет! Это Бот-переходник канала PinkNudes 🍓\n\n"
        "В моем канале много интересного контента 🍒\n"
        "Также ты можешь купить приватку в ней я публикую такое.. 🔞",
        reply_markup=start_kb()
    )

# ---------- ПОКУПКА ----------
@dp.callback_query(F.data == "buy")
async def buy(call: CallbackQuery):
    invoice = create_invoice(call.from_user.id)
    invoices[call.from_user.id] = invoice["invoice_id"]
    await call.message.answer(
        f"💳 Оплати {PRICE_USDT} USDT через CryptoBot\n\n{invoice['pay_url']}",
        reply_markup=pay_kb()
    )
    await call.answer()

@dp.callback_query(F.data == "check")
async def check(call: CallbackQuery):
    invoice_id = invoices.get(call.from_user.id)
    if not invoice_id:
        await call.message.answer("❌ Счёт не найден")
        return

    status = check_invoice(invoice_id)
    if status == "paid":
        await call.message.answer(
            "🍓 Поздравляю, ты купил мою Приватку!\n\n"
            "Кидай заявку и в скорем времени я приму тебя 🍓",
            reply_markup=private_kb()
        )
        invoices.pop(call.from_user.id, None)
    else:
        await call.message.answer("⏳ Оплата ещё не прошла")

    await call.answer()

# ---------- АДМИН / РАССЫЛКА ----------
@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await message.answer(
        f"🔧 Админка\n\n"
        f"👥 Пользователей: {len(users)}\n\n"
        f"Для рассылки:\n/send"
    )

@dp.message(Command("send"))
async def send_cmd(message: Message):
    global broadcast_mode
    if message.from_user.id != ADMIN_ID:
        return

    users = load_users()
    if not users:
        await message.answer("❌ users.txt пуст. Никто не нажал /start")
        return

    broadcast_mode = True
    await message.answer(
        f"📢 Рассылка\nНайдено пользователей: {len(users)}\n\n"
        "Отправь СЛЕДУЮЩЕЕ сообщение:\n"
        "• текст\n"
        "• или фото + текст"
    )

@dp.message()
async def broadcast_handler(message: Message):
    global broadcast_mode
    if message.from_user.id != ADMIN_ID or not broadcast_mode:
        return

    users = load_users()
    sent = 0

    for uid in users:
        try:
            if message.photo:
                await bot.send_photo(
                    uid,
                    message.photo[-1].file_id,
                    caption=message.caption
                )
            else:
                await bot.send_message(uid, message.text)
            sent += 1
        except Exception as e:
            print(f"FAIL {uid}: {e}")

    broadcast_mode = False
    await message.answer(f"✅ Рассылка завершена\nПолучили: {sent}")

# ---------- KEEP ALIVE (Render) ----------
async def handle_ping(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

# ---------- RUN ----------
async def main():
    await start_web()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
