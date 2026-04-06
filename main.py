import asyncio
import sqlite3
import random
import string
import re
from datetime import datetime
from typing import Optional, Dict, Set

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
)
from aiogram.client.default import DefaultBotProperties

# ========== КОНФИГ ==========
BOT_TOKEN = "8276230046:AAGI7gkFHbI80AVgP0-g55qBm7SBCw00Duw"
ADMIN_ID = 1471307057
YOUR_USERNAME = "IllyaGarant"
CHANNEL_ID = -1002377654714
CHANNEL_USERNAME = "LiarsProofs"

# ========== TG PREMIUM ЭМОДЗИ (из твоего тутора) ==========
EMOJI_LIKE = "5285430309720966085"      # 👍
EMOJI_DANGER = "5310169226856644648"    # опасность
EMOJI_SUCCESS = "5310076249404621168"   # успех
EMOJI_PRIMARY = "5285430309720966085"   # основной
EMOJI_CROWN = "5217822164362739968"     # 👑
EMOJI_STAR = "5285032475490273112"      # ⭐

def tg_emoji(emoji_id: str, fallback: str = "•") -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
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
            fee INTEGER DEFAULT 0,
            scam_proof_link TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS processed_messages (
            message_id INTEGER PRIMARY KEY,
            channel_id INTEGER,
            processed_at TEXT
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

def extract_ids_from_text(text: str) -> Set[str]:
    """Извлекает все возможные ID и username из текста"""
    ids = set()
    if not text:
        return ids
    
    # Username с @
    at_mentions = re.findall(r'@([a-zA-Z0-9_]{5,32})', text)
    for username in at_mentions:
        ids.add(username.lower())
    
    # Username без @
    plain_usernames = re.findall(r'(?<![@\w])[a-zA-Z0-9_]{5,32}(?![@\w])', text)
    for username in plain_usernames:
        if username not in ['https', 'http', 'tme', 'telegram']:
            ids.add(username.lower())
    
    # Числовые ID
    numeric_ids = re.findall(r'\b(\d{5,15})\b', text)
    for nid in numeric_ids:
        ids.add(nid)
    
    # Ссылки t.me/username
    tme_links = re.findall(r't\.me/([a-zA-Z0-9_]{5,32})', text)
    for username in tme_links:
        ids.add(username.lower())
    
    return ids

def add_scammer_from_channel(user_id: str, username: str, proof_link: str = None):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    cur.execute("SELECT user_id FROM users WHERE user_id = ? OR username = ?", (user_id, username))
    existing = cur.fetchone()
    
    if existing:
        cur.execute('''
            UPDATE users 
            SET status = 'scammer', trust_score = 0, base_date = ?, scam_proof_link = ?
            WHERE user_id = ? OR username = ?
        ''', (base_date, proof_link, user_id, username))
    else:
        cur.execute('''
            INSERT INTO users (user_id, username, status, trust_score, base_date, scam_proof_link)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, "scammer", 0, base_date, proof_link))
    
    conn.commit()
    conn.close()

def is_message_processed(message_id: int) -> bool:
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM processed_messages WHERE message_id = ?", (message_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def mark_message_processed(message_id: int):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO processed_messages (message_id, channel_id, processed_at) VALUES (?, ?, ?)",
                (message_id, CHANNEL_ID, datetime.now().isoformat()))
    conn.commit()
    conn.close()

async def parse_all_channel_messages():
    """Парсит ВСЕ сообщения из канала"""
    print(f"{tg_emoji(EMOJI_STAR, '🔄')} Начинаю полный парсинг канала {CHANNEL_USERNAME}...")
    
    added_count = 0
    offset_id = 0
    
    try:
        while True:
            try:
                messages = await bot.get_chat_history(
                    chat_id=CHANNEL_ID,
                    limit=100,
                    offset=offset_id
                )
                
                if not messages:
                    break
                
                for message in messages:
                    if is_message_processed(message.message_id):
                        continue
                    
                    full_text = (message.text or message.caption or "")
                    
                    ids = extract_ids_from_text(full_text)
                    proof_link = f"https://t.me/{CHANNEL_USERNAME}/{message.message_id}"
                    
                    for scam_id in ids:
                        if scam_id.isdigit():
                            user_id = scam_id
                            username = None
                        else:
                            user_id = f"user_{scam_id}"
                            username = scam_id
                        
                        add_scammer_from_channel(user_id, username, proof_link)
                        added_count += 1
                        print(f"{tg_emoji(EMOJI_DANGER, '⚠️')} Добавлен скамер: {scam_id}")
                    
                    mark_message_processed(message.message_id)
                
                if messages:
                    offset_id = messages[-1].message_id
                else:
                    break
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Ошибка при парсинге: {e}")
                break
        
        print(f"{tg_emoji(EMOJI_SUCCESS, '✅')} Парсинг завершён! Добавлено {added_count} скамеров")
        
    except Exception as e:
        print(f"{tg_emoji(EMOJI_DANGER, '❌')} Ошибка: {e}")

def get_user_by_identifier(identifier: str) -> Optional[Dict]:
    """Поиск пользователя по username или ID"""
    identifier = identifier.lower().replace("@", "")
    
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    
    if identifier.isdigit():
        cur.execute("SELECT * FROM users WHERE user_id = ?", (identifier,))
    else:
        cur.execute("SELECT * FROM users WHERE LOWER(username) = ?", (identifier,))
    
    row = cur.fetchone()
    conn.close()
    
    if row:
        columns = ["user_id", "username", "full_name", "trust_score", "review_code",
                   "status", "deposit", "responsible_id", "reg_date", "base_date",
                   "is_admin", "plus_count", "minus_count", "reports_filed", 
                   "reports_confirmed", "fee", "scam_proof_link"]
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
                   "is_admin", "plus_count", "minus_count", "reports_filed", 
                   "reports_confirmed", "fee", "scam_proof_link"]
        return dict(zip(columns, row))
    return None

def create_user(user_id: str, username: str = None, full_name: str = None):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    review_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute('''
        INSERT INTO users (user_id, username, full_name, trust_score, review_code, status,
                          deposit, reg_date, base_date, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, username, full_name, 0, f"R-{review_code}", "user", 0,
          datetime.now().strftime("%d %B %Y"), base_date, 0))
    conn.commit()
    conn.close()

def add_garant(user_id: str, username: str, deposit: float, fee: int = 2):
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

# ========== ИНЛАЙН КЛАВИАТУРЫ (только инлайн, без reply) ==========
main_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_STAR, '🔎')} Поиск", callback_data="menu_search"),
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_LIKE, '👤')} Профиль", callback_data="menu_profile")
    ],
    [
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '🛡')} Сделка", callback_data="menu_deal"),
        InlineKeyboardButton(text="📢 Канал", callback_data="menu_channel")
    ]
])

admin_menu_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_STAR, '🔎')} Поиск", callback_data="menu_search"),
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_LIKE, '👤')} Профиль", callback_data="menu_profile")
    ],
    [
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '🛡')} Сделка", callback_data="menu_deal"),
        InlineKeyboardButton(text="📢 Канал", callback_data="menu_channel")
    ],
    [
        InlineKeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '👑')} Панель руч.", callback_data="admin_panel")
    ]
])

search_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_LIKE, '✋')} Ввести username / ID", callback_data="search_input")],
    [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '◀️')} Назад", callback_data="back_to_menu")]
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
    waiting_search_input = State()

# ========== ОБРАБОТЧИКИ ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    user = get_user_by_id(user_id)
    
    if not user:
        create_user(user_id, message.from_user.username, message.from_user.full_name)
        user = get_user_by_id(user_id)
    
    fee_text = f" | {user['fee']}%" if user["status"] == "garant" and user.get("fee", 0) > 0 else ""
    
    kb = admin_menu_kb if user.get("is_admin") else main_menu_kb
    
    await message.answer(
        f"{tg_emoji(EMOJI_CROWN, '👤')} {message.from_user.full_name}{fee_text}\n\n"
        f"Добро пожаловать в 1Ndex Base — пространство подлинной безопасности и доверия.\n\n"
        f"{tg_emoji(EMOJI_STAR, '🔎')} Поиск пользователей\n"
        f"{tg_emoji(EMOJI_CROWN, '🛡')} Проведение сделок\n"
        f"{tg_emoji(EMOJI_SUCCESS, '✅')} Гарантия безопасности\n\n"
        f"{tg_emoji(EMOJI_DANGER, '⚠️')} База скамеров из канала @{CHANNEL_USERNAME}",
        reply_markup=kb
    )

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user = get_user_by_id(str(callback.from_user.id))
    kb = admin_menu_kb if user and user.get("is_admin") else main_menu_kb
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '👤')} Главное меню\n\n"
        f"Выберите действие:",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_search")
async def menu_search(callback: CallbackQuery):
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_STAR, '🔎')} <b>Поиск пользователя</b>\n\n"
        f"Введите username или ID пользователя для проверки.\n\n"
        f"Примеры:\n"
        f"• @username\n"
        f"• username\n"
        f"• 123456789",
        reply_markup=search_kb
    )
    await callback.answer()

@dp.callback_query(F.data == "search_input")
async def search_input_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(f"{tg_emoji(EMOJI_LIKE, '✋')} Отправьте username или ID пользователя:")
    await state.set_state(AdminStates.waiting_search_input)
    await callback.answer()

@dp.message(AdminStates.waiting_search_input)
async def process_search(message: Message, state: FSMContext):
    search_text = message.text.strip()
    await state.clear()
    
    user = get_user_by_identifier(search_text)
    
    if not user:
        await message.answer(
            f"{tg_emoji(EMOJI_DANGER, '❌')} <b>Пользователь не найден в базе</b>\n\n"
            f"👤 {search_text} — не найден в 1Ndex.\n\n"
            f"{tg_emoji(EMOJI_STAR, '📢')} База обновляется из канала @{CHANNEL_USERNAME}"
        )
        return
    
    if user["status"] == "scammer":
        proof_text = f"\n\n📎 Пруф: {user['scam_proof_link']}" if user.get('scam_proof_link') else ""
        await message.answer(
            f"{tg_emoji(EMOJI_DANGER, '🔴')} <b>ВНИМАНИЕ! SCAMMER!</b>\n\n"
            f"👤 {user['full_name'] or user['username']} - @{user['username']} | ID: {user['user_id']}\n\n"
            f"👻 @{user['username']} — является мошенником. Ни в коем случае не проводите с ним сделку.\n\n"
            f"📈 TrustScore: 0%\n\n"
            f"⏰ В Telegram с: ~ {user['reg_date']}\n"
            f"📅 В базе с: {user['base_date']}{proof_text}"
        )
    elif user["status"] == "garant":
        await message.answer(
            f"{tg_emoji(EMOJI_CROWN, '👤')} {user['username']} | {user.get('fee', 2)}% - Link | "
            f"Теги: @{user['username']} | ID: {user['user_id']}\n\n"
            f"👻 @{user['username']} — рученик. Депозит: ${user['deposit']}.\n\n"
            f"➕ {user['plus_count']} | 🚫 {user['minus_count']} | 👁 {user['reports_filed']} | "
            f"📈 {user['trust_score']}% | 💎 ${user['deposit']}\n\n"
            f"⏰ В Telegram с: ~ {user['reg_date']}\n"
            f"📅 В базе с: {user['base_date']}"
        )
    else:
        await message.answer(
            f"{tg_emoji(EMOJI_LIKE, '👤')} {user['username']} - Link | Теги: @{user['username']} | ID: {user['user_id']}\n\n"
            f"👻 @{user['username']} — обычный пользователь.\n\n"
            f"➕ {user['plus_count']} | 🚫 {user['minus_count']} | 👁 {user['reports_filed']} | 📈 {user['trust_score']}%\n\n"
            f"⏰ В Telegram с: ~ {user['reg_date']}\n"
            f"📅 В базе с: {user['base_date']}"
        )

@dp.callback_query(F.data == "menu_profile")
async def menu_profile(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    user = get_user_by_id(user_id)
    
    if not user:
        await callback.answer("Ошибка", show_alert=True)
        return
    
    status_map = {
        "user": f"{tg_emoji(EMOJI_LIKE, '👤')} Пользователь",
        "garant": f"{tg_emoji(EMOJI_CROWN, '✋')} Рученик",
        "scammer": f"{tg_emoji(EMOJI_DANGER, '🔴')} Скамер"
    }
    status_text = status_map.get(user["status"], f"{tg_emoji(EMOJI_LIKE, '👤')} Пользователь")
    
    await callback.message.edit_text(
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
        f"✅ Подтверждено: {user['reports_confirmed']}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '◀️')} Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "menu_deal")
async def menu_deal(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Создание сделки</b>\n\n"
        f"Шаг 1 из 4\n\n"
        f"👤 Введите username партнёра (например: @username):"
    )
    await state.set_state(DealStates.waiting_partner)
    await callback.answer()

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
            [
                InlineKeyboardButton(text="RUB", callback_data="cur_RUB"),
                InlineKeyboardButton(text="USD", callback_data="cur_USD"),
                InlineKeyboardButton(text="USDT", callback_data="cur_USDT")
            ],
            [
                InlineKeyboardButton(text="TON", callback_data="cur_TON"),
                InlineKeyboardButton(text="UAH", callback_data="cur_UAH")
            ],
            [
                InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '❌')} Отмена", callback_data="cancel_deal")
            ]
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
    except ValueError:
        await message.answer(f"{tg_emoji(EMOJI_DANGER, '❌')} Введите число (например: 500 или 500.50)")

@dp.callback_query(DealStates.waiting_currency, F.data.startswith("cur_"))
async def deal_step_currency(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    
    data = await state.get_data()
    
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username, deposit, fee FROM users WHERE status = 'garant'")
    guarants = cur.fetchall()
    conn.close()
    
    builder = []
    for g_id, g_username, deposit, fee in guarants:
        builder.append([InlineKeyboardButton(
            text=f"{tg_emoji(EMOJI_CROWN, '👑')} @{g_username} | {fee}% | ${deposit}",
            callback_data=f"guar_{g_id}"
        )])
    builder.append([InlineKeyboardButton(
        text=f"{tg_emoji(EMOJI_DANGER, '❌')} Отмена",
        callback_data="cancel_deal"
    )])
    
    kb = InlineKeyboardMarkup(inline_keyboard=builder)
    
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Создание сделки</b>\n\n"
        f"Шаг 4 из 4\n\n"
        f"👤 Партнёр: @{data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {currency}\n\n"
        f"🛡 Выберите гаранта:",
        reply_markup=kb
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
    
    # Узнаем username гаранта
    guarantor_user = get_user_by_id(guarantor_id)
    guarantor_name = f"@{guarantor_user['username']}" if guarantor_user and guarantor_user.get('username') else guarantor_id
    
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Сделка создана!</b>\n\n"
        f"👤 Партнёр: @{data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {data['currency']}\n"
        f"🛡 Гарант: {guarantor_name}\n\n"
        f"⏳ Ожидание подтверждения гаранта..."
    )
    
    # Уведомление гаранту
    accept_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{tg_emoji(EMOJI_SUCCESS, '✅')} Принять", callback_data=f"accept_{deal_id}"),
            InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '❌')} Отклонить", callback_data=f"reject_{deal_id}")
        ]
    ])
    
    await bot.send_message(
        int(guarantor_id),
        f"{tg_emoji(EMOJI_CROWN, '🛡')} <b>Новая сделка!</b>\n\n"
        f"👤 Покупатель: @{callback.from_user.username or callback.from_user.id}\n"
        f"👤 Продавец: @{data['partner']}\n"
        f"💰 Сумма: {data['amount']:.2f} {data['currency']}\n\n"
        f"Нажмите «Принять» чтобы подтвердить сделку:",
        reply_markup=accept_kb
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
        buyer_id, seller_id, amount, currency = deal
        await bot.send_message(
            int(buyer_id),
            f"{tg_emoji(EMOJI_SUCCESS, '✅')} <b>Сделка подтверждена!</b>\n\n"
            f"👤 Продавец: @{seller_id}\n"
            f"💰 Сумма: {amount:.2f} {currency}\n\n"
            f"Можете приступать к обмену."
        )
        await callback.message.edit_text(f"{tg_emoji(EMOJI_SUCCESS, '✅')} Сделка #{deal_id} принята")
    await callback.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject_deal(callback: CallbackQuery):
    deal_id = callback.data.split("_")[1]
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("UPDATE deals SET status = 'rejected' WHERE deal_id = ?", (deal_id,))
    cur.execute("SELECT buyer_id FROM deals WHERE deal_id = ?", (deal_id,))
    deal = cur.fetchone()
    conn.commit()
    conn.close()
    
    if deal:
        buyer_id = deal[0]
        await bot.send_message(
            int(buyer_id),
            f"{tg_emoji(EMOJI_DANGER, '❌')} <b>Сделка отклонена</b>\n\n"
            f"Гарант отклонил вашу сделку."
        )
        await callback.message.edit_text(f"{tg_emoji(EMOJI_DANGER, '❌')} Сделка #{deal_id} отклонена")
    await callback.answer()

@dp.callback_query(F.data == "menu_channel")
async def menu_channel(callback: CallbackQuery):
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_STAR, '📢')} <b>Наши ресурсы</b>\n\n"
        f"🔗 Канал с пруфами: https://t.me/{CHANNEL_USERNAME}\n"
        f"🤖 Бот для проверки: @{bot.username}\n\n"
        f"{tg_emoji(EMOJI_DANGER, '⚠️')} Все скамеры автоматически добавляются из канала!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '◀️')} Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    user = get_user_by_id(str(callback.from_user.id))
    if not user or not user.get("is_admin"):
        await callback.answer(f"{tg_emoji(EMOJI_DANGER, '❌')} Нет доступа", show_alert=True)
        return
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_CROWN, '➕')} Добавить рученика", callback_data="admin_add_garant")],
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '🔴')} Добавить скамера", callback_data="admin_add_scammer")],
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_STAR, '📋')} Список ручеников", callback_data="admin_list_garants")],
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_STAR, '🔄')} Перепарсить канал", callback_data="admin_reparse")],
        [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '◀️')} Назад", callback_data="back_to_menu")]
    ])
    
    await callback.message.edit_text(
        f"{tg_emoji(EMOJI_CROWN, '👑')} <b>Панель управления</b>\n\n"
        f"Выберите действие:",
        reply_markup=kb
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_add_garant")
async def admin_add_garant(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(f"{tg_emoji(EMOJI_CROWN, '➕')} Введите username рученика (например: @garant):")
    await state.set_state(AdminStates.waiting_garant_username)
    await callback.answer()

@dp.message(AdminStates.waiting_garant_username)
async def add_garant_deposit_prompt(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    await state.update_data(garant_username=username)
    await message.answer(f"{tg_emoji(EMOJI_CROWN, '💰')} Введите сумму депозита для @{username} (например: 50):")
    await state.set_state(AdminStates.waiting_garant_deposit)

@dp.message(AdminStates.waiting_garant_deposit)
async def add_garant_save(message: Message, state: FSMContext):
    try:
        deposit = float(message.text.replace(",", "."))
        data = await state.get_data()
        username = data['garant_username']
        
        temp_id = f"garant_{username}"
        add_garant(temp_id, username, deposit, 2)
        
        await message.answer(
            f"{tg_emoji(EMOJI_SUCCESS, '✅')} <b>Рученик добавлен!</b>\n\n"
            f"👤 @{username}\n"
            f"💰 Депозит: ${deposit}\n"
            f"📊 Комиссия: 2%"
        )
        await state.clear()
    except ValueError:
        await message.answer(f"{tg_emoji(EMOJI_DANGER, '❌')} Введите число!")

@dp.callback_query(F.data == "admin_add_scammer")
async def admin_add_scammer(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(f"{tg_emoji(EMOJI_DANGER, '🔴')} Введите username скамера (например: @scammer):")
    await state.set_state(AdminStates.waiting_scammer_username)
    await callback.answer()

@dp.message(AdminStates.waiting_scammer_username)
async def add_scammer_save(message: Message, state: FSMContext):
    username = message.text.strip().replace("@", "")
    temp_id = f"scammer_{username}"
    
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    base_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    cur.execute('''
        INSERT OR REPLACE INTO users (user_id, username, status, trust_score, base_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (temp_id, username, "scammer", 0, base_date))
    conn.commit()
    conn.close()
    
    await message.answer(
        f"{tg_emoji(EMOJI_DANGER, '🔴')} <b>Скамер добавлен!</b>\n\n"
        f"👤 @{username}\n"
        f"⚠️ Будьте осторожны!"
    )
    await state.clear()

@dp.callback_query(F.data == "admin_list_garants")
async def admin_list_garants(callback: CallbackQuery):
    conn = sqlite3.connect("spectra.db")
    cur = conn.cursor()
    cur.execute("SELECT username, deposit, fee FROM users WHERE status = 'garant'")
    garants = cur.fetchall()
    conn.close()
    
    if not garants:
        text = f"{tg_emoji(EMOJI_DANGER, '📋')} Список ручеников пуст"
    else:
        text = f"{tg_emoji(EMOJI_CROWN, '👑')} <b>Список ручеников</b>\n\n"
        for g in garants:
            text += f"• @{g[0]} | {g[2]}% | ${g[1]}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{tg_emoji(EMOJI_DANGER, '◀️')} Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_reparse")
async def admin_reparse(callback: CallbackQuery):
    user = get_user_by_id(str(callback.from_user.id))
    if not user or not user.get("is_admin"):
        await callback.answer(f"{tg_emoji(EMOJI_DANGER, '❌')} Нет доступа", show_alert=True)
        return
    
    await callback.message.answer(f"{tg_emoji(EMOJI_STAR, '🔄')} Начинаю перепарсинг канала...")
    await parse_all_channel_messages()
    await callback.message.answer(f"{tg_emoji(EMOJI_SUCCESS, '✅')} Перепарсинг завершён!")
    await callback.answer()

async def main():
    init_db()
    print(f"{tg_emoji(EMOJI_SUCCESS, '✅')} Бот Spectra | Verify Bot запущен!")
    
    # Запускаем парсинг канала в фоне
    asyncio.create_task(parse_all_channel_messages())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
