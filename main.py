import asyncio
import sqlite3
import random
import string
from datetime import datetime
from typing import Optional, Dict, Tuple

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, 
    InlineKeyboardButton, CallbackQuery, Message
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== КОНФИГ ==========
BOT_TOKEN = "8276230046:AAGI7gkFHbI80AVgP0-g55qBm7SBCw00Duw"  # Замени на свой токен от @BotFather
ADMIN_ID = 1471307057  # Твой Telegram ID

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    
    # Пользователи
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            trust_score REAL DEFAULT 0,
            review_code TEXT,
            status TEXT DEFAULT 'user',
            deposit REAL DEFAULT 0,
            responsible_id TEXT,
            reg_date TEXT,
            base_date TEXT,
            is_admin INTEGER DEFAULT 0,
            plus_count INTEGER DEFAULT 0,
            minus_count INTEGER DEFAULT 0,
            reports_filed INTEGER DEFAULT 0,
            reports_confirmed INTEGER DEFAULT 0
        )
    ''')
    
    # Сделки
    cur.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            buyer_id TEXT,
            seller_id TEXT,
            guarantor_id TEXT,
            amount REAL,
            currency TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    
    # Репорты
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT,
            to_id TEXT,
            reason TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    
    # Репутация
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reputation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT,
            to_id TEXT,
            rating INTEGER,
            created_at TEXT
        )
    ''')
    
    # Добавляем админа если нет
    cur.execute("SELECT * FROM users WHERE user_id = ?", (str(ADMIN_ID),))
    if not cur.fetchone():
        cur.execute('''
            INSERT INTO users (user_id, username, status, is_admin, base_date, reg_date, trust_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (str(ADMIN_ID), "admin", "garant", 1, datetime.now().strftime("%d.%m.%Y %H:%M"), 
              datetime.now().strftime("%d %B %Y"), 100))
    
    conn.commit()
    conn.close()

def get_user(user_id: str) -> Optional[Dict]:
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = ["user_id", "username", "full_name", "trust_score", "review_code", 
                   "status", "deposit", "responsible_id", "reg_date", "base_date", 
                   "is_admin", "plus_count", "minus_count", "reports_filed", "reports_confirmed"]
        return dict(zip(columns, row))
    return None

def create_user(user_id: str, username: str = None, full_name: str = None):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    review_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute('''
        INSERT INTO users (user_id, username, full_name, trust_score, review_code, status, 
                          deposit, reg_date, base_date, is_admin, plus_count, minus_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, 0, f"R-{review_code}", "user", 0, 
          datetime.now().strftime("%d %B %Y"), base_date, 0, 0, 0))
    conn.commit()
    conn.close()

def update_user_status(user_id: str, status: str, deposit: float = 0, responsible_id: str = None):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = ?, deposit = ?, responsible_id = ? WHERE user_id = ?", 
                (status, deposit, responsible_id, user_id))
    conn.commit()
    conn.close()

def add_scammer(user_id: str, username: str = None):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO users (user_id, username, status, trust_score, base_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, "scammer", 0, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()

# ========== КНОПКИ (с твоими ID) ==========
def main_menu_keyboard(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="🔎 Поиск")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🛡 Сделка")],
        [KeyboardButton(text="📢 Канал")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Панель руч.")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Инлайн кнопки с твоими ID
search_numbers_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1", callback_data="search_num_5874960879434338403"),
     InlineKeyboardButton(text="2", callback_data="search_num_5877465816030515018"),
     InlineKeyboardButton(text="3", callback_data="search_num_5883964170268840032")],
    [InlineKeyboardButton(text="4", callback_data="search_num_5951584964305755220"),
     InlineKeyboardButton(text="5", callback_data="search_num_5879585266426973039"),
     InlineKeyboardButton(text="6", callback_data="search_num_5886666250158870040")],
    [InlineKeyboardButton(text="7", callback_data="search_num_5870734657384877785")],
    [InlineKeyboardButton(text="✅ Выбрать пользователя", callback_data="select_user")],
    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
])

# ========== СОСТОЯНИЯ ДЛЯ СДЕЛКИ ==========
class DealStates(StatesGroup):
    waiting_partner = State()
    waiting_amount = State()
    waiting_currency = State()
    waiting_guarantor = State()

# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    
    if not user:
        create_user(user_id, message.from_user.username, message.from_user.full_name)
        user = get_user(user_id)
    
    status_map = {"user": "👤 Пользователь", "garant": "✋ Рученик", "scammer": "🔴 Скамер"}
    status_text = status_map.get(user["status"], "👤 Пользователь")
    
    fee_text = f" | {int(user['deposit'])}%" if user["status"] == "garant" and user["deposit"] > 0 else ""
    
    await message.answer(
        f"👤 {message.from_user.full_name}{fee_text}\n\n"
        f"Добро пожаловать в 1Ndex Base — пространство подлинной безопасности и доверия.\n\n"
        f"🔎 Поиск пользователей\n"
        f"🛡 Проведение сделок\n"
        f"✅ Гарантия безопасности",
        reply_markup=main_menu_keyboard(user.get("is_admin", 0))
    )

@dp.message(F.text == "🔎 Поиск")
async def search_menu(message: Message):
    await message.answer(
        "🔎 Поиск пользователя\n\n"
        "Доступные способы поиска\n\n"
        "🔗 @username — тег с собачкой\n"
        "👤 username — тег без собачки\n"
        "#️⃣ 123456789 — числовой ID\n"
        "🌐 t.me/username — ссылка на профиль\n"
        "💬 Пересланное сообщение\n"
        "✋ Кнопка «Выбрать» ниже",
        reply_markup=search_numbers_kb
    )

@dp.callback_query(F.data.startswith("search_num_"))
async def search_number(callback: CallbackQuery):
    num_id = callback.data.split("_")[2]
    await callback.answer(f"Вы выбрали номер {num_id}", show_alert=True)

@dp.callback_query(F.data == "select_user")
async def select_user_prompt(callback: CallbackQuery):
    await callback.message.answer("✋ Отправьте username или перешлите сообщение пользователя")
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user_id = str(message.from_user.id)
    user = get_user(user_id)
    
    if not user:
        await message.answer("❌ Ошибка. Напишите /start")
        return
    
    status_map = {"user": "👤 Пользователь", "garant": "✋ Рученик", "scammer": "🔴 Скамер"}
    status_text = status_map.get(user["status"], "👤 Пользователь")
    
    trust_emoji = "📈" if user["trust_score"] >= 50 else "📉"
    
    await message.answer(
        f"👤 Ваш профиль\n\n"
        f"{trust_emoji} Trust Score: {user['trust_score']}%\n"
        f"#️⃣ Код отзывов: {user['review_code']}\n"
        f"🛡 Статус: {status_text}\n"
        f"📅 В сети с: {user['reg_date']}\n\n"
        f"📊 Репутация\n"
        f"➕ Получено: +{user['plus_count']} / -{user['minus_count']}\n"
        f"🚫 Оставлено: +0 / -0\n\n"
        f"❗ Репорты\n"
        f"⬆️ Подано: {user['reports_filed']}\n"
        f"✅ Подтверждено: {user['reports_confirmed']}"
    )

@dp.message(F.text == "🛡 Сделка")
async def create_deal(message: Message, state: FSMContext):
    await message.answer(
        "🛡 Создание сделки\n\n"
        "Шаг 1 из 4\n\n"
        "👤 С кем вы хотите провести сделку?\n\n"
        "Введите username пользователя (например: @username)"
    )
    await state.set_state(DealStates.waiting_partner)

@dp.message(DealStates.waiting_partner)
async def deal_step_partner(message: Message, state: FSMContext):
    partner = message.text.strip()
    await state.update_data(partner=partner)
    await message.answer(
        f"🛡 Создание сделки\n\n"
        f"Шаг 2 из 4\n\n"
        f"👤 Партнёр: {partner}\n\n"
        f"💰 Введите сумму сделки:"
    )
    await state.set_state(DealStates.waiting_amount)

@dp.message(DealStates.waiting_amount)
async def deal_step_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        await state.update_data(amount=amount)
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="RUB", callback_data="cur_RUB"),
             InlineKeyboardButton(text="USD", callback_data="cur_USD"),
             InlineKeyboardButton(text="USDT", callback_data="cur_USDT")],
            [InlineKeyboardButton(text="TON", callback_data="cur_TON"),
             InlineKeyboardButton(text="UAH", callback_data="cur_UAH")]
        ])
        
        data = await state.get_data()
        await message.answer(
            f"🛡 Создание сделки\n\n"
            f"Шаг 3 из 4\n\n"
            f"👤 Партнёр: {data['partner']}\n"
            f"💰 Сумма: {amount:.2f}\n\n"
            f"💳 Выберите валюту:",
            reply_markup=kb
        )
        await state.set_state(DealStates.waiting_currency)
    except:
        await message.answer("❌ Введите число (например: 500 или 500.50)")

@dp.callback_query(DealStates.waiting_currency, F.data.startswith("cur_"))
async def deal_step_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    
    data = await state.get_data()
    
    # Получаем список гарантов
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username FROM users WHERE status = 'garant' LIMIT 5")
    guarants = cur.fetchall()
    conn.close()
    
    builder = InlineKeyboardBuilder()
    for g_id, g_username in guarants:
        builder.add(InlineKeyboardButton(text=f"👑 @{g_username}", callback_data=f"guar_{g_id}"))
    builder.adjust(1)
    builder.add(InlineKeyboardButton(text="◀️ Отмена", callback_data="cancel_deal"))
    
    await callback.message.edit_text(
        f"🛡 Создание сделки\n\n"
        f"Шаг 4 из 4\n\n"
        f"👤 Партнёр: {data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {currency}\n\n"
        f"🛡 Выберите гаранта:",
        reply_markup=builder.as_markup()
    )
    await state.set_state(DealStates.waiting_guarantor)
    await callback.answer()

@dp.callback_query(DealStates.waiting_guarantor, F.data.startswith("guar_"))
async def deal_select_guarantor(callback: CallbackQuery, state: FSMContext):
    guarantor_id = callback.data.split("_")[1]
    data = await state.get_data()
    
    deal_id = ''.join(random.choices(string.digits, k=10))
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO deals (deal_id, buyer_id, seller_id, guarantor_id, amount, currency, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (deal_id, str(callback.from_user.id), data['partner'].replace("@", ""), 
          guarantor_id, data['amount'], data['currency'], "waiting", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(
        f"🛡 Сделка создана!\n\n"
        f"👤 Партнёр: {data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {data['currency']}\n"
        f"🛡 Гарант: @{guarantor_id}\n\n"
        f"⏳ Ожидание подтверждения гаранта..."
    )
    
    # Уведомляем гаранта
    await bot.send_message(
        int(guarantor_id),
        f"🛡 Новая сделка!\n\n"
        f"👤 Покупатель: @{callback.from_user.username or callback.from_user.id}\n"
        f"👤 Продавец: {data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {data['currency']}\n\n"
        f"Принять / отклонить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{deal_id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{deal_id}")]
        ])
    )
    
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel_deal")
async def cancel_deal(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Сделка отменена")
    await callback.answer()

@dp.callback_query(F.data.startswith("accept_"))
async def accept_deal(callback: CallbackQuery):
    deal_id = callback.data.split("_")[1]
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("UPDATE deals SET status = 'active' WHERE deal_id = ?", (deal_id,))
    cur.execute("SELECT buyer_id, seller_id, amount, currency FROM deals WHERE deal_id = ?", (deal_id,))
    deal = cur.fetchone()
    conn.commit()
    conn.close()
    
    if deal:
        await bot.send_message(int(deal[0]), f"✅ Гарант принял сделку!\nСумма: {deal[2]} {deal[3]}")
        await callback.message.edit_text(f"✅ Сделка #{deal_id} принята")
    await callback.answer()

@dp.message(F.text == "👑 Панель руч.")
async def admin_panel(message: Message):
    user = get_user(str(message.from_user.id))
    if not user or not user.get("is_admin"):
        await message.answer("❌ Нет доступа")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить рученика", callback_data="add_garant")],
        [InlineKeyboardButton(text="🔴 Добавить скамера", callback_data="add_scammer")],
        [InlineKeyboardButton(text="📋 Список ручеников", callback_data="list_garants")]
    ])
    await message.answer("🛡 Панель управления", reply_markup=kb)

@dp.callback_query(F.data == "add_garant")
async def add_garant_prompt(callback: CallbackQuery):
    await callback.message.answer("➕ Введите username рученика (например: @garant):")
    await callback.answer()

@dp.message(lambda msg: msg.text and msg.text.startswith("@") and msg.chat.id == ADMIN_ID)
async def process_add_garant(message: Message):
    username = message.text.replace("@", "")
    user_id = f"user_{username}"  # В реальном боте нужно получить реальный ID через getChat
    
    update_user_status(user_id, "garant", 13.0, str(ADMIN_ID))
    await message.answer(f"✅ @{username} добавлен как рученик с депозитом $13")

@dp.callback_query(F.data == "add_scammer")
async def add_scammer_prompt(callback: CallbackQuery):
    await callback.message.answer("🔴 Введите username скамера (например: @scammer):")
    await callback.answer()

@dp.message(F.text == "📢 Канал")
async def channel(message: Message):
    await message.answer("📢 Наш канал: https://t.me/your_channel")

async def main():
    init_db()
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
