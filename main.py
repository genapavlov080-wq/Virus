import asyncio
import sqlite3
import random
import string
from datetime import datetime
from typing import Optional, Dict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton, CallbackQuery, Message
)

# ========== КОНФИГ ==========
BOT_TOKEN = "8276230046:AAGI7gkFHbI80AVgP0-g55qBm7SBCw00Duw"
ADMIN_ID = 1471307057  # Твой ID
YOUR_USERNAME = "IllyaGarant"  # Твой юзернейм

# ========== TG PREMIUM ЭМОДЗИ ==========
# ID эмодзи (можно менять)
EMOJI_CROWN = "5217822164362739968"      # 👑
EMOJI_THUMBS_UP = "5285430309720966085"  # 👍
EMOJI_DANGER = "5310169226856644648"     # ⚠️
EMOJI_SUCCESS = "5310076249404621168"    # ✅
EMOJI_STAR = "5285032475490273112"       # ⭐

def tg_emoji(emoji_id: str, fallback: str = "•") -> str:
    """Возвращает HTML-тег для TG Premium эмодзи"""
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    
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
            reports_confirmed INTEGER DEFAULT 0,
            fee INTEGER DEFAULT 0
        )
    ''')
    
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
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reputation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id TEXT,
            to_id TEXT,
            rating INTEGER,
            created_at TEXT
        )
    ''')
    
    # Добавляем админа (тебя)
    cur.execute("SELECT * FROM users WHERE user_id = ?", (str(ADMIN_ID),))
    if not cur.fetchone():
        cur.execute('''
            INSERT INTO users (user_id, username, status, is_admin, base_date, reg_date, trust_score, deposit, fee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(ADMIN_ID), YOUR_USERNAME, "garant", 1, 
              datetime.now().strftime("%d.%m.%Y %H:%M"),
              datetime.now().strftime("%d %B %Y"), 32.5, 13, 2))
    
    conn.commit()
    conn.close()

def get_user_by_username(username: str) -> Optional[Dict]:
    """Поиск пользователя по username (без @)"""
    username = username.lower().replace("@", "")
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = ["user_id", "username", "full_name", "trust_score", "review_code",
                   "status", "deposit", "responsible_id", "reg_date", "base_date",
                   "is_admin", "plus_count", "minus_count", "reports_filed", "reports_confirmed", "fee"]
        return dict(zip(columns, row))
    return None

def get_user_by_id(user_id: str) -> Optional[Dict]:
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        columns = ["user_id", "username", "full_name", "trust_score", "review_code",
                   "status", "deposit", "responsible_id", "reg_date", "base_date",
                   "is_admin", "plus_count", "minus_count", "reports_filed", "reports_confirmed", "fee"]
        return dict(zip(columns, row))
    return None

def create_user(user_id: str, username: str = None, full_name: str = None):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    review_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute('''
        INSERT INTO users (user_id, username, full_name, trust_score, review_code, status, 
                          deposit, reg_date, base_date, is_admin, plus_count, minus_count, fee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, 0, f"R-{review_code}", "user", 0, 
          datetime.now().strftime("%d %B %Y"), base_date, 0, 0, 0, 0))
    conn.commit()
    conn.close()

def add_garant(user_id: str, username: str, deposit: float, fee: int = 2):
    """Добавить рученика с депозитом"""
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    review_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute('''
        INSERT OR REPLACE INTO users (user_id, username, status, deposit, responsible_id, 
                                      trust_score, review_code, base_date, reg_date, fee, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, "garant", deposit, str(ADMIN_ID), 32.5, f"R-{review_code}", 
          base_date, datetime.now().strftime("%d %B %Y"), fee, 0))
    conn.commit()
    conn.close()

def add_scammer(user_id: str, username: str):
    """Добавить скамера"""
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute('''
        INSERT OR REPLACE INTO users (user_id, username, status, trust_score, base_date, 
                                      plus_count, minus_count, deposit, fee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, "scammer", 0, base_date, 0, 0, 0, 0))
    conn.commit()
    conn.close()

# ========== КЛАВИАТУРЫ С TG PREMIUM ЭМОДЗИ ==========
def main_menu_keyboard(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text=f"{tg_emoji(EMOJI_STAR, '🔎')} Поиск")],
        [KeyboardButton(text=f"{tg_emoji(EMOJI_THUMBS_UP, '👤')} Профиль")],
        [KeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '🛡')} Сделка")],
        [KeyboardButton(text="📢 Канал")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '👑')} Панель руч.")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Инлайн кнопки с эмодзи
search_numbers_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1", callback_data="search_num_1"),
     InlineKeyboardButton(text="2", callback_data="search_num_2"),
     InlineKeyboardButton(text="3", callback_data="search_num_3")],
    [InlineKeyboardButton(text="4", callback_data="search_num_4"),
     InlineKeyboardButton(text="5", callback_data="search_num_5"),
     InlineKeyboardButton(text="6", callback_data="search_num_6")],
    [InlineKeyboardButton(text="7", callback_data="search_num_7")],
    [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_SUCCESS, '✅')} Выбрать пользователя", 
                          callback_data="select_user")],
    [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '◀️')} Назад", 
                          callback_data="back_to_menu")]
])

# ========== СОСТОЯНИЯ ==========
class DealStates(StatesGroup):
    waiting_partner = State()
    waiting_amount = State()
    waiting_currency = State()
    waiting_guarantor = State()

class AdminStates(StatesGroup):
    waiting_garant_username = State()
    waiting_garant_deposit = State()
    waiting_scammer_username = State()

# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    user = get_user_by_id(user_id)
    
    if not user:
        create_user(user_id, message.from_user.username, message.from_user.full_name)
        user = get_user_by_id(user_id)
    
    fee_text = f" | {user['fee']}%" if user["status"] == "garant" and user.get("fee", 0) > 0 else ""
    
    await message.answer(
        f"{tg_emoji(EMOJI_CROWN, '👤')} {message.from_user.full_name}{fee_text}\n\n"
        f"Добро пожаловать в 1Ndex Base — пространство подлинной безопасности и доверия.\n\n"
        f"{tg_emoji(EMOJI_STAR, '🔎')} Поиск пользователей\n"
        f"{tg_emoji(EMOJI_CROWN, '🛡')} Проведение сделок\n"
        f"{tg_emoji(EMOJI_SUCCESS, '✅')} Гарантия безопасности",
        reply_markup=main_menu_keyboard(user.get("is_admin", 0))
    )

@dp.message(F.text.contains("Поиск"))
async def search_menu(message: Message):
    await message.answer(
        f"{tg_emoji(EMOJI_STAR, '🔎')} <b>Поиск пользователя</b>\n\n"
        f"Доступные способы поиска\n\n"
        f"🔗 @username — тег с собачкой\n"
        f"👤 username — тег без собачки\n"
        f"#️⃣ 123456789 — числовой ID\n"
        f"🌐 t.me/username — ссылка на профиль\n"
        f"💬 Пересланное сообщение\n"
        f"{tg_emoji(EMOJI_THUMBS_UP, '✋')} Кнопка «Выбрать» ниже",
        reply_markup=search_numbers_kb
    )

@dp.message(F.text.contains("Профиль"))
async def profile(message: Message):
    user_id = str(message.from_user.id)
    user = get_user_by_id(user_id)
    
    if not user:
        await message.answer("❌ Ошибка. Напишите /start")
        return
    
    status_map = {"user": f"{tg_emoji(EMOJI_THUMBS_UP, '👤')} Пользователь", 
                  "garant": f"{tg_emoji(EMOJI_CROWN, '✋')} Рученик", 
                  "scammer": f"{tg_emoji(EMOJI_DANGER, '🔴')} Скамер"}
    status_text = status_map.get(user["status"], f"{tg_emoji(EMOJI_THUMBS_UP, '👤')} Пользователь")
    
    await message.answer(
        f"{tg_emoji(EMOJI_CROWN, '👤')} <b>Ваш профиль</b>\n\n"
        f"📈 Trust Score: {user['trust_score']}%\n"
        f"#️⃣ Код отзывов: {user['review_code']}\n"
        f"🛡 Статус: {status_text}\n"
        f"📅 В сети с: {user['reg_date']}\n\n"
        f"<b>📊 Репутация</b>\n"
        f"➕ Получено: +{user['plus_count']} / -{user['minus_count']}\n"
        f"🚫 Оставлено: +0 / -0\n\n"
        f"<b>❗ Репорты</b>\n"
        f"⬆️ Подано: {user['reports_filed']}\n"
        f"✅ Подтверждено: {user['reports_confirmed']}"
    )

@dp.message(F.text.contains("Сделка"))
async def create_deal(message: Message, state: FSMContext):
    await message.answer(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Создание сделки</b>\n\n"
        f"Шаг 1 из 4\n\n"
        f"👤 С кем вы хотите провести сделку?\n\n"
        f"Введите username пользователя (например: @username)"
    )
    await state.set_state(DealStates.waiting_partner)

@dp.message(DealStates.waiting_partner)
async def deal_step_partner(message: Message, state: FSMContext):
    partner_input = message.text.strip().replace("@", "")
    await state.update_data(partner=partner_input)
    await message.answer(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Создание сделки</b>\n\n"
        f"Шаг 2 из 4\n\n"
        f"👤 Партнёр: @{partner_input}\n\n"
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
            f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Создание сделки</b>\n\n"
            f"Шаг 3 из 4\n\n"
            f"👤 Партнёр: @{data['partner']}\n"
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
    
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, deposit, fee FROM users WHERE status = 'garant' LIMIT 10")
    guarants = cur.fetchall()
    conn.close()
    
    builder = InlineKeyboardBuilder()
    for g_id, g_username, deposit, fee in guarants:
        builder.add(InlineKeyboardButton(
            text=f"{tg_emoji(EMOJI_CROWN, '👑')} @{g_username} | {fee}% | ${deposit}", 
            callback_data=f"guar_{g_id}"
        ))
    builder.adjust(1)
    builder.add(InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '❌')} Отмена", callback_data="cancel_deal"))
    
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Создание сделки</b>\n\n"
        f"Шаг 4 из 4\n\n"
        f"👤 Партнёр: @{data['partner']}\n"
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
    ''', (deal_id, str(callback.from_user.id), data['partner'], 
          guarantor_id, data['amount'], data['currency'], "waiting", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Сделка создана!</b>\n\n"
        f"👤 Партнёр: @{data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {data['currency']}\n"
        f"🛡 Гарант: @{guarantor_id}\n\n"
        f"⏳ Ожидание подтверждения гаранта..."
    )
    
    await bot.send_message(
        int(guarantor_id),
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Новая сделка!</b>\n\n"
        f"👤 Покупатель: @{callback.from_user.username or callback.from_user.id}\n"
        f"👤 Продавец: @{data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {data['currency']}\n\n"
        f"Принять / отклонить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_SUCCESS, '✅')} Принять", callback_data=f"accept_{deal_id}"),
             InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '❌')} Отклонить", callback_data=f"reject_{deal_id}")]
        ])
    )
    
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "cancel_deal")
async def cancel_deal(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(f"{tg_emoji(EMOJI_DANGER, '❌')} Сделка отменена")
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
        await bot.send_message(int(deal[0]), f"{tg_emoji(EMOJI_SUCCESS, '✅')} Гарант принял сделку!\nСумма: {deal[2]} {deal[3]}")
        await callback.message.edit_text(f"{tg_emoji(EMOJI_SUCCESS, '✅')} Сделка #{deal_id} принята")
    await callback.answer()

@dp.message(F.text.contains("Панель руч"))
async def admin_panel(message: Message):
    user = get_user_by_id(str(message.from_user.id))
    if not user or not user.get("is_admin"):
        await message.answer(f"{tg_emoji(EMOJI_DANGER, '❌')} Нет доступа")
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '➕')} Добавить рученика", callback_data="add_garant")],
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '🔴')} Добавить скамера", callback_data="add_scammer")],
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_STAR, '📋')} Список ручеников", callback_data="list_garants")]
    ])
    await message.answer(f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Панель управления</b>", reply_markup=kb)

@dp.callback_query(F.data == "add_garant")
async def add_garant_username(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(f"{tg_emoji(EMOJI_CROWN, '➕')} Введите <b>username</b> рученика (например: @garant):")
    await state.set_state(AdminStates.waiting_garant_username)
    await callback.answer()

@dp.message(AdminStates.waiting_garant_username)
async def add_garant_deposit_prompt(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    await state.update_data(garant_username=username)
    await message.answer(f"{tg_emoji(EMOJI_CROWN, '💰')} Введите <b>сумму депозита</b> для @{username} (например: 50):")
    await state.set_state(AdminStates.waiting_garant_deposit)

@dp.message(AdminStates.waiting_garant_deposit)
async def add_garant_save(message: Message, state: FSMContext):
    try:
        deposit = float(message.text.replace(",", "."))
        data = await state.get_data()
        username = data['garant_username']
        
        # Здесь нужно получить реальный user_id, пока временный
        temp_id = f"garant_{username}"
        add_garant(temp_id, username, deposit, 2)
        
        await message.answer(
            f"{tg_emoji(EMOJI_SUCCESS, '✅')} <b>Рученик добавлен!</b>\n\n"
            f"👤 @{username}\n"
            f"💰 Депозит: ${deposit}\n"
            f"📊 Комиссия: 2%"
        )
        await state.clear()
    except:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "add_scammer")
async def add_scammer_username(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(f"{tg_emoji(EMOJI_DANGER, '🔴')} Введите <b>username</b> скамера (например: @scammer):")
    await state.set_state(AdminStates.waiting_scammer_username)
    await callback.answer()

@dp.message(AdminStates.waiting_scammer_username)
async def add_scammer_save(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    temp_id = f"scammer_{username}"
    add_scammer(temp_id, username)
    
     await message.answer(
        f"{tg_emoji(EMOJI_DANGER, '🔴')} <b>Скамер добавлен!</b>\n\n"
        f"👤 @{username}\n"
        f"⚠️ Будьте осторожны!"
    )
    await state.clear()

@dp.callback_query(F.data == "list_garants")
async def list_garants(callback: CallbackQuery):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT username, deposit, fee FROM users WHERE status = 'garant'")
    garants = cur.fetchall()
    conn.close()
    
    if not garants:
        await callback.message.answer("📋 Список ручеников пуст")
    else:
        text = f"{tg_emoji(EMOJI_CROWN, '👑')} <b>Список ручеников</b>\n\n"
        for g in garants:
            text += f"• @{g[0]} | {g[2]}% | ${g[1]}\n"
        await callback.message.answer(text)
    await callback.answer()

@dp.message(F.text.contains("Канал"))
async def channel(message: Message):
    await message.answer("📢 Наш канал: https://t.me/your_channel")

@dp.callback_query(F.data == "select_user")
async def select_user_prompt(callback: CallbackQuery):
    await callback.message.answer("✋ Отправьте username или перешлите сообщение пользователя")
    await callback.answer()

@dp.callback_query(F.data.startswith("search_num_"))
async def search_number(callback: CallbackQuery):
    num = callback.data.split("_")[2]
    await callback.answer(f"Вы выбрали номер {num}", show_alert=True)

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()

@dp.message(F.text)
async def search_user(message: Message):
    """Поиск пользователя по username в БД"""
    search_text = message.text.strip().replace("@", "").lower()
    
    user = get_user_by_username(search_text)
    
    if not user:
        await message.answer(
            f"{tg_emoji(EMOJI_DANGER, '❌')} <b>Пользователь не найден в базе</b>\n\n"
            f"👤 @{search_text} — не найден в 1Ndex. Рекомендуется быть осторожным."
        )
        return
    
    # Формируем вывод в зависимости от статуса
    if user["status"] == "scammer":
        await message.answer(
            f"{tg_emoji(EMOJI_DANGER, '🔴')} <b>ВНИМАНИЕ! SCAMMER!</b>\n\n"
            f"👤 {user['full_name'] or user['username']} - @{user['username']} | ID: {user['user_id']}\n\n"
            f"👻 @{user['username']} — является мошенником. Ни в коем случае не проводите с ним сделку.\n\n"
            f"📈 TrustScore: 0%\n\n"
            f"⏰ В Telegram с: ~ {user['reg_date']}\n"
            f"📅 В базе с: {user['base_date']}"
        )
    elif user["status"] == "garant":
        await message.answer(
            f"{tg_emoji(EMOJI_CROWN, '👤')} {user['username']} | {user.get('fee', 2)}% - Link | Теги: @{user['username']} | ID: {user['user_id']}\n\n"
            f"👻 @{user['username']} — рученик. Ответственное лицо — Нажми. Депозит: ${user['deposit']}.\n\n"
            f"➕ {user['plus_count']} | 🚫 {user['minus_count']} | 👁 {user['reports_filed']} | 📈 {user['trust_score']}% | 💎 ${user['deposit']}\n\n"
            f"⏰ В Telegram с: ~ {user['reg_date']}\n"
            f"📅 В базе с: {user['base_date']}\n\n"
            f"🛡 Ответственные лица:\n"
            f"👑 деля (@delya) — $13"
        )
    else:
        await message.answer(
            f"{tg_emoji(EMOJI_THUMBS_UP, '👤')} {user['username']} - Link | Теги: @{user['username']} | ID: {user['user_id']}\n\n"
            f"👻 @{user['username']} — обычный пользователь, не найден в 1ndex. Рекомендуется быть осторожным и использовать услуги проверенных гарантов - /mm.\n\n"
            f"➕ {user['plus_count']} | 🚫 {user['minus_count']} | 👁 {user['reports_filed']} | 📈 {user['trust_score']}%\n\n"
            f"⏰ В Telegram с: ~ {user['reg_date']}\n"
            f"📅 В базе с: {user['base_date']}"
        )

async def main():
    init_db()
    print(f"{tg_emoji(EMOJI_SUCCESS, '✅')} Бот Spectra | Verify Bot запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
