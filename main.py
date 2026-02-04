import asyncio
import requests
import time
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ========= НАСТРОЙКИ =========
BOT_TOKEN = "8355471659:AAFWRNlxYtww9IgEAvwIee0DlWsmExdhJOg"
CRYPTO_TOKEN = "526004:AAdTiJf7ebmFVMXm2lFxkud339PdvDgcaly"
ADMIN_ID = 5333130126

PUBLIC_CHANNEL_URL = "https://t.me/+fP9jHqTTGAVkY2Fi"
PRIVATE_CHANNEL_URL = "https://t.me/+GB0H9D7fYN1iOWYy"
PRICE_USDT = "2"

USERS_FILE = "users.txt"
PING_INTERVAL = 300  # 5 минут
# =============================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
HEADERS = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}

invoices = {}
broadcast_mode = False

# ---------- USER STORAGE ----------
def save_user(user_id: int):
    try:
        with open(USERS_FILE, "a+") as f:
            f.seek(0)
            users = set(f.read().splitlines())
            if str(user_id) not in users:
                f.write(f"{user_id}\n")
    except:
        pass

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return [int(x) for x in f.read().splitlines()]
    except:
        return []

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

admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")]
])

# ---------- CRYPTO ----------
def create_invoice(user_id):
    r = requests.post(
        "https://pay.crypt.bot/api/createInvoice",
        headers=HEADERS,
        json={
            "asset": "USDT",
            "amount": PRICE_USDT,
            "description": "Покупка приватки",
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
        "Также ты можешь купить приватку — ведь в ней я публикую такое.. 🤯",
        reply_markup=start_kb()
    )

# ---------- ПОКУПКА ----------
@dp.callback_query(F.data == "buy")
async def buy(call: CallbackQuery):
    invoice = create_invoice(call.from_user.id)
    invoices[call.from_user.id] = invoice["invoice_id"]
    await call.message.answer(
        f"💳 Оплати {PRICE_USDT} USDT\n\n{invoice['pay_url']}",
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
            "🍓 Поздравляю ты купил мою Приватку!\n\n"
            "Кидай заявку и в скорем времени я приму тебя 🍓",
            reply_markup=private_kb()
        )
        invoices.pop(call.from_user.id, None)
    else:
        await call.message.answer("⏳ Оплата ещё не прошла")
    await call.answer()

# ---------- АДМИН ----------
@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🔧 Админка", reply_markup=admin_kb)

@dp.callback_query(F.data == "broadcast")
async def bc(call: CallbackQuery):
    global broadcast_mode
    if call.from_user.id != ADMIN_ID:
        return
    broadcast_mode = True
    await call.message.answer("📢 Отправь сообщение для рассылки (текст или фото+текст)")
    await call.answer()

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
                await bot.send_photo(uid, message.photo[-1].file_id, caption=message.caption)
            else:
                await bot.send_message(uid, message.text)
            sent += 1
        except:
            pass
    broadcast_mode = False
    await message.answer(f"✅ Рассылка завершена\nПолучили: {sent}")

# ---------- HTTP KEEP-ALIVE (для Render + Ultimate/UptimeRobot) ----------
async def handle_ping(request):
    return web.Response(text="OK")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def self_ping():
    # Локальный пинг каждые 5 минут (дополнительно)
    while True:
        print("PING")
        await asyncio.sleep(PING_INTERVAL)

# ---------- RUN ----------
async def main():
    await start_web()
    asyncio.create_task(self_ping())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
