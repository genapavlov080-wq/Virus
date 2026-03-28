import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import requests
import json

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8655981898:AAE6-Ija80rwYN0FQoXIfcuAsNsUosAl_z0"
ADMIN_ID = 1471307057
CARD = "5167803275649049"
CARD_SBER = "2202206340487136"
CARD_SBER_NAME = "Вазген Б."

# Канал для подписки
REQUIRED_CHANNEL_ID = -1002544275396
REQUIRED_CHANNEL_URL = "https://t.me/+P2DK2IpHKBdiZGUy"
REQUIRED_CHANNEL_NAME = "ZroglikCheat_rezelvv"

REVIEWS_CHANNEL_URL = "https://t.me/zroglikrotzivv"

# CryptoBot API
CRYPTO_TOKEN = "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"
CRYPTO_API = "https://pay.crypt.bot/api"

# Цены
PRICES = {
    "zolo": {"1": "85 грн", "3": "180 грн", "7": "325 грн", "14": "400 грн", "30": "690 грн", "60": "1000 грн"},
    "impact": {"1": "115 грн", "7": "480 грн", "30": "1170 грн"},
    "king": {"1": "100 грн", "7": "425 грн", "30": "1060 грн"},
    "inferno": {"1": "80 грн", "3": "200 грн", "7": "350 грн", "15": "530 грн", "30": "690 грн", "60": "950 грн"},
    "zolo_cis": {"1": "70 грн", "3": "150 грн", "7": "250 грн", "14": "350 грн", "30": "700 грн", "60": "900 грн"}
}

CHEAT_NAMES = {
    "zolo": "🔥 Zolo Cheat",
    "impact": "⚡ Impact VIP",
    "king": "👑 King Mod",
    "inferno": "💥 Inferno Cheat",
    "zolo_cis": "🎮 Zolo CIS Edition"
}

# --- ЭМОДЗИ ID ДЛЯ PREMIUM ---
EMOJI = {
    "catalog": "5156877291397055163",
    "profile": "5904630315946611415",
    "reviews": "5938252440926163756",
    "support": "5208539876747662991",
    "back": "5960671702059848143",
    "zolo": "5451653043089070124",
    "impact": "5276079251089547977",
    "king": "6172520285330214110",
    "inferno": "5296273418516187626",
    "zolo_cis": "5451841459009379088",
    "period": "5393330385096575682",
    "bank": "5393576224729633040",
    "sber": "5247180323120225302",
    "crypto": "5208954744818651087",
    "check": "6039486778597970865",
    "receipt": "5258205968025525531",
    "cancel": "5208480322731137426",
    "approve": "5208657859499282838",
    "lock": "5208806229144524155",
    "fire": "5208806229144524155",
    "welcome": "5208657859499282838",
    "target": "6073605466221451561",
    "money": "5890848474563352982",
    "calendar": "5413879192267805083",
    "card": "5393576224729633040",
    "photo": "5769126056262898415",
    "id_emoji": "6032693626394382504",
    "name": "5879770735999717115",
    "username": "5814247475141153332",
    "product_emoji": "6041730074376410123",
    "time": "5891211339170326418",
    "key": "6048733173171359488",
    "date": "5208474816583063829",
    "link": "5208480322731137426",
    "success": "5938252440926163756"
}

# --- ФУНКЦИЯ ДЛЯ PREMIUM ЭМОДЗИ В ТЕКСТЕ ---
def em(emoji_id, fallback_emoji):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback_emoji}</tg-emoji>'

# --- БАЗА ДАННЫХ ---
conn = sqlite3.connect('zroglik.db', timeout=30, check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        expiry_date TEXT,
        product_name TEXT,
        subscribed_at TEXT,
        banned INTEGER DEFAULT 0,
        ban_reason TEXT,
        last_key TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS crypto_payments (
        payment_id TEXT PRIMARY KEY,
        user_id INTEGER,
        amount REAL,
        days INTEGER,
        product TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'pending'
    )
''')
conn.commit()

# --- ИНИЦИАЛИЗАЦИЯ БОТА ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ХРАНИЛИЩА ---
waiting = {}
user_selection = {}

# --- REPLY КЛАВИАТУРА ГЛАВНОГО МЕНЮ С PREMIUM ЭМОДЗИ ---
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Каталог",
                    icon_custom_emoji_id=EMOJI["catalog"]
                )
            ],
            [
                KeyboardButton(
                    text="Мій кабінет",
                    icon_custom_emoji_id=EMOJI["profile"]
                )
            ],
            [
                KeyboardButton(
                    text="Відгуки",
                    icon_custom_emoji_id=EMOJI["reviews"]
                ),
                KeyboardButton(
                    text="Техпідтримка",
                    icon_custom_emoji_id=EMOJI["support"]
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Назад",
                    icon_custom_emoji_id=EMOJI["back"]
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# --- INLINE КЛАВИАТУРЫ ---
def get_cheats_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Zolo", callback_data="cheat_zolo", icon_custom_emoji_id=EMOJI["zolo"])],
        [InlineKeyboardButton(text="Impact VIP", callback_data="cheat_impact", icon_custom_emoji_id=EMOJI["impact"])],
        [InlineKeyboardButton(text="King Mod", callback_data="cheat_king", icon_custom_emoji_id=EMOJI["king"])],
        [InlineKeyboardButton(text="Inferno", callback_data="cheat_inferno", icon_custom_emoji_id=EMOJI["inferno"])],
        [InlineKeyboardButton(text="Zolo CIS", callback_data="cheat_zolo_cis", icon_custom_emoji_id=EMOJI["zolo_cis"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["back"])]
    ])
    return keyboard

def get_period_keyboard(cheat):
    buttons = []
    for days in PRICES[cheat].keys():
        days_text = f"{days} дн." if days != "1" else "1 день"
        buttons.append([InlineKeyboardButton(text=days_text, callback_data=f"period_{cheat}_{days}", icon_custom_emoji_id=EMOJI["period"])])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog", icon_custom_emoji_id=EMOJI["back"])])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_keyboard(cheat, days):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Укр Банк", callback_data=f"bank_{cheat}_{days}", icon_custom_emoji_id=EMOJI["bank"])],
        [InlineKeyboardButton(text="Сбербанк", callback_data=f"bank_sber_{cheat}_{days}", icon_custom_emoji_id=EMOJI["sber"])],
        [InlineKeyboardButton(text="CryptoBot", callback_data=f"crypto_{cheat}_{days}", icon_custom_emoji_id=EMOJI["crypto"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_period_{cheat}", icon_custom_emoji_id=EMOJI["back"])]
    ])
    return keyboard

def get_receipt_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я оплатив", callback_data="send_receipt", icon_custom_emoji_id=EMOJI["receipt"])],
        [InlineKeyboardButton(text="Скасувати", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["cancel"])]
    ])
    return keyboard

def get_reviews_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Канал з відгуками", url=REVIEWS_CHANNEL_URL, icon_custom_emoji_id=EMOJI["reviews"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["back"])]
    ])
    return keyboard

def get_subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ПОДПИСАТЬСЯ", url=REQUIRED_CHANNEL_URL, icon_custom_emoji_id=EMOJI["catalog"])],
        [InlineKeyboardButton(text="ПРОВЕРИТИ", callback_data="check_sub", icon_custom_emoji_id=EMOJI["check"])]
    ])
    return keyboard

def get_admin_decision_keyboard(user_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Одобрити", callback_data=f"adm_ok_{user_id}", icon_custom_emoji_id=EMOJI["approve"])],
        [InlineKeyboardButton(text="Відхилити", callback_data=f"adm_no_{user_id}", icon_custom_emoji_id=EMOJI["cancel"])]
    ])
    return keyboard

def get_crypto_payment_keyboard(pay_url, invoice_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оплатить", url=pay_url, icon_custom_emoji_id=EMOJI["crypto"])],
        [InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_crypto_{invoice_id}", icon_custom_emoji_id=EMOJI["check"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["back"])]
    ])
    return keyboard

# --- ФУНКЦИИ ---
def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        import asyncio
        result = asyncio.run_coroutine_threadsafe(
            bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id),
            asyncio.get_event_loop()
        ).result()
        return result.status in ["member", "administrator", "creator"]
    except:
        return False

def create_crypto_invoice(user_id, amount, days, product):
    url = f"{CRYPTO_API}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {
        "asset": "USDT",
        "amount": amount,
        "description": f"{CHEAT_NAMES[product]} - {days} дней",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/plutoniumfilesBot",
        "payload": f"{user_id}|{days}|{product}"
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        if r.status_code == 200 and r.json().get("ok"):
            return r.json()["result"]
    except Exception as e:
        print(f"CryptoBot error: {e}")
    return None

def check_crypto_payment(payment_id):
    url = f"{CRYPTO_API}/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    params = {"invoice_ids": payment_id}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200 and r.json().get("ok"):
            items = r.json()["result"].get("items", [])
            if items:
                return items[0]
    except Exception as e:
        print(f"Check payment error: {e}")
    return None

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        await message.answer("⛔ Ви заблоковані")
        return
    
    if not check_subscription(user_id):
        text = (f"{em(EMOJI['lock'], '🔒')} <b>Доступ обмежено!</b>\n\n"
                f"Для доступу до бота необхідно підписатися на канал:\n"
                f"📢 <b>{REQUIRED_CHANNEL_NAME}</b>\n\n"
                f"Після підписки натисніть кнопку «ПРОВЕРИТИ»")
        await message.answer(text, reply_markup=get_subscribe_keyboard())
        return
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, subscribed_at) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?))
    ''', (user_id, username, first_name, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = (f"{em(EMOJI['fire'], '🔥')} <b>ZROGLIK KEYS</b>\n\n"
            f"{em(EMOJI['welcome'], '👋')} Ласкаво просимо до ZroglikShop!\n"
            f"{em(EMOJI['target'], '🎯')} Тут ти можеш купити чити для PUBG Mobile")
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if check_subscription(user_id):
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, subscribed_at) 
            VALUES (?, ?)
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        
        text = (f"{em(EMOJI['fire'], '🔥')} <b>ZROGLIK KEYS</b>\n\n"
                f"{em(EMOJI['welcome'], '👋')} Ласкаво просимо до ZroglikShop!\n"
                f"{em(EMOJI['target'], '🎯')} Тут ти можеш купити чити для PUBG Mobile")
        
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=get_main_keyboard())
        await callback.answer("✅ Підписка підтверджена!")
    else:
        await callback.answer("❌ Ви ще не підписалися на канал!", show_alert=True)

@dp.message(F.text == "Каталог")
async def handle_catalog(message: types.Message):
    text = f"{em(EMOJI['target'], '🎯')} <b>PUBG Mobile</b>\nВиберіть чит:"
    await message.answer(text, reply_markup=get_cheats_keyboard())

@dp.message(F.text == "Мій кабінет")
async def handle_profile(message: types.Message):
    user_id = message.from_user.id
    
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        await message.answer("⛔ Ви заблоковані")
        return
    
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    time_left = "Немає активної підписки"
    product = "Немає"
    last_key = "Немає"
    expiry_display = "Немає"
    
    if user and user['expiry_date']:
        try:
            expiry = datetime.strptime(user['expiry_date'], '%Y-%m-%d %H:%M:%S')
            diff = expiry - datetime.now()
            if diff.total_seconds() > 0:
                days = diff.days
                hours = diff.seconds // 3600
                time_left = f"{days} дн. {hours} год." if days > 0 else f"{hours} год."
                product = user['product_name'] if user['product_name'] else "Немає"
                last_key = user['last_key'] if user['last_key'] else "Немає"
                expiry_display = expiry.strftime('%d.%m.%Y %H:%M')
            else:
                time_left = "❌ Закінчилась"
        except:
            pass
    
    user_name = user['first_name'] if user and user['first_name'] else str(user_id)
    user_username = user['username'] if user and user['username'] else "Немає"
    
    text = (f"{em(EMOJI['profile'], '👤')} <b>МІЙ КАБІНЕТ</b>\n\n"
            f"{em(EMOJI['id_emoji'], '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
            f"{em(EMOJI['name'], '📛')} <b>Ім'я:</b> {user_name}\n"
            f"{em(EMOJI['username'], '🔖')} <b>Username:</b> @{user_username}\n"
            f"{em(EMOJI['product_emoji'], '📦')} <b>Товар:</b> {product}\n"
            f"{em(EMOJI['time'], '⏳')} <b>Залишилось:</b> {time_left}\n"
            f"{em(EMOJI['key'], '🔑')} <b>Ваш ключ:</b> <code>{last_key}</code>\n"
            f"{em(EMOJI['date'], '📅')} <b>Діє до:</b> {expiry_display}")
    
    await message.answer(text, reply_markup=get_back_keyboard())

@dp.message(F.text == "Відгуки")
async def handle_reviews(message: types.Message):
    text = f"{em(EMOJI['reviews'], '⭐')} <b>Наші відгуки</b>"
    await message.answer(text, reply_markup=get_reviews_keyboard())

@dp.message(F.text == "Техпідтримка")
async def handle_support(message: types.Message):
    text = f"{em(EMOJI['support'], '🎮')} <b>Технічна підтримка</b>\n\nЗв'яжіться з нами: @ZrogIikCheat"
    await message.answer(text, reply_markup=get_back_keyboard())

@dp.message(F.text == "Назад")
async def handle_back(message: types.Message):
    await cmd_start(message)

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await cmd_start(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery):
    text = f"{em(EMOJI['target'], '🎯')} <b>PUBG Mobile</b>\nВиберіть чит:"
    await callback.message.edit_text(text, reply_markup=get_cheats_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("back_to_period_"))
async def back_to_period(callback: types.CallbackQuery):
    cheat = callback.data.split("_")[3]
    desc = f"{CHEAT_NAMES[cheat]}\n\n"
    desc += f"{em(EMOJI['money'], '💰')} <b>Ціни:</b>\n"
    
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        desc += f"├ {days_text}: {em(EMOJI['money'], '💰')} {price}\n"
    
    desc += f"\n{em(EMOJI['period'], '💳')} <b>Виберіть період:</b>"
    
    await callback.message.edit_text(desc, reply_markup=get_period_keyboard(cheat))
    await callback.answer()

@dp.callback_query(F.data.startswith("cheat_"))
async def show_cheat(callback: types.CallbackQuery):
    cheat = callback.data.split("_")[1]
    desc = f"{CHEAT_NAMES[cheat]}\n\n"
    desc += f"{em(EMOJI['money'], '💰')} <b>Ціни:</b>\n"
    
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        desc += f"├ {days_text}: {em(EMOJI['money'], '💰')} {price}\n"
    
    desc += f"\n{em(EMOJI['period'], '💳')} <b>Виберіть період:</b>"
    
    await callback.message.edit_text(desc, reply_markup=get_period_keyboard(cheat))
    await callback.answer()

@dp.callback_query(F.data.startswith("period_"))
async def select_period(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    cheat = parts[1]
    days = parts[2]
    
    user_selection[callback.from_user.id] = {"cheat": cheat, "days": days}
    price = PRICES[cheat][days]
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n"
    desc += f"{em(EMOJI['calendar'], '📅')} {days} дн.\n"
    desc += f"{em(EMOJI['money'], '💰')} {price}\n\n"
    desc += f"{em(EMOJI['card'], '💳')} <b>Виберіть спосіб оплати:</b>"
    
    await callback.message.edit_text(desc, reply_markup=get_payment_keyboard(cheat, days))
    await callback.answer()

@dp.callback_query(F.data.startswith("bank_"))
async def bank_payment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    cheat = parts[1]
    days = parts[2]
    
    waiting[f"{callback.from_user.id}_product"] = cheat
    waiting[f"{callback.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    
    text = (f"{em(EMOJI['bank'], '💳')} <b>Оплата банківською карткою</b>\n\n"
            f"{em(EMOJI['money'], '💰')} <b>Сума:</b> {price}\n"
            f"{em(EMOJI['bank'], '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
            f"{em(EMOJI['cancel'], '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em(EMOJI['photo'], '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    
    await callback.message.edit_text(text, reply_markup=get_receipt_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("bank_sber_"))
async def sber_payment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    cheat = parts[2]
    days = parts[3]
    
    waiting[f"{callback.from_user.id}_product"] = cheat
    waiting[f"{callback.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    
    text = (f"{em(EMOJI['sber'], '🏦')} <b>Оплата Сбербанк</b>\n\n"
            f"{em(EMOJI['money'], '💰')} <b>Сума:</b> {price}\n"
            f"{em(EMOJI['sber'], '💳')} <b>Карта:</b> <code>{CARD_SBER}</code>\n"
            f"{em(EMOJI['name'], '👤')} <b>Отримувач:</b> {CARD_SBER_NAME}\n"
            f"{em(EMOJI['cancel'], '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em(EMOJI['photo'], '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    
    await callback.message.edit_text(text, reply_markup=get_receipt_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("crypto_"))
async def crypto_payment(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    cheat = parts[1]
    days = parts[2]
    user_id = callback.from_user.id
    
    price_str = PRICES[cheat][days].replace(" грн", "")
    amount = round(int(price_str) / 43, 2)
    
    invoice = create_crypto_invoice(user_id, amount, days, cheat)
    if not invoice:
        await callback.message.edit_text("❌ Ошибка создания платежа")
        return
    
    cursor.execute('''
        INSERT INTO crypto_payments (payment_id, user_id, amount, days, product, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(invoice["invoice_id"]), user_id, amount, days, cheat, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = (f"{em(EMOJI['crypto'], '💎')} <b>Оплата через CryptoBot</b>\n\n"
            f"{em(EMOJI['money'], '💰')} <b>Сума:</b> {amount}$\n"
            f"{em(EMOJI['calendar'], '📅')} <b>Тариф:</b> {days} дней")
    
    await callback.message.edit_text(text, reply_markup=get_crypto_payment_keyboard(invoice["pay_url"], invoice["invoice_id"]))
    await callback.answer()

@dp.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto(callback: types.CallbackQuery):
    payment_id = int(callback.data.replace("check_crypto_", ""))
    user_id = callback.from_user.id
    
    payment = check_crypto_payment(payment_id)
    
    if payment and payment.get("status") == "paid":
        res = cursor.execute('SELECT product, days FROM crypto_payments WHERE payment_id = ?', (str(payment_id),)).fetchone()
        if res:
            product, days = res
            expiry = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, CHEAT_NAMES[product], user_id))
            cursor.execute('UPDATE crypto_payments SET status = "paid" WHERE payment_id = ?', (str(payment_id),))
            conn.commit()
            
            text = (f"{em(EMOJI['success'], '✅')} <b>Оплата подтверждена!</b>\n\n"
                    f"{em(EMOJI['calendar'], '📅')} <b>Подписка до:</b> {expiry}")
            
            await callback.message.edit_text(text)
            await bot.send_message(ADMIN_ID, f"{em(EMOJI['money'], '💰')} <b>Новый крипто-платёж</b>\n👤 {user_id}\n📅 {days} дней\n💎 {CHEAT_NAMES[product]}")
            await callback.answer("✅ Оплата подтверждена!")
    else:
        await callback.answer("⏳ Платёж ещё не подтверждён", show_alert=True)

@dp.callback_query(F.data == "send_receipt")
async def send_receipt(callback: types.CallbackQuery):
    waiting[f"{callback.from_user.id}_waiting"] = "receipt"
    text = f"{em(EMOJI['photo'], '📸')} <b>Надішліть скріншот чека</b> (одним фото)"
    await callback.message.edit_text(text)
    await callback.answer()

@dp.message(F.photo)
async def handle_receipt_photo(message: types.Message):
    user_id = message.from_user.id
    if waiting.get(f"{user_id}_waiting") == "receipt":
        waiting[f"{user_id}_waiting"] = None
        product = waiting.get(f"{user_id}_product", "Unknown")
        days = waiting.get(f"{user_id}_days", "0")
        
        photo = message.photo[-1].file_id
        
        await bot.send_photo(
            ADMIN_ID,
            photo,
            caption=f"🔔 <b>Чек від {user_id}</b>\n📦 Товар: {product}\n⏳ Тариф: {days} днів",
            reply_markup=get_admin_decision_keyboard(user_id)
        )
        await message.answer(f"✅ Чек відправлено адміністратору! Очікуйте підтвердження.")

# --- АДМИН-ОБРАБОТЧИКИ ---
@dp.callback_query(F.data.startswith("adm_ok_"))
async def admin_approve(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    product = waiting.get(f"{target_id}_product", "Unknown")
    days = waiting.get(f"{target_id}_days", "0")
    
    waiting[f"admin_{callback.from_user.id}_target"] = target_id
    waiting[f"admin_{callback.from_user.id}_product"] = product
    waiting[f"admin_{callback.from_user.id}_days"] = days
    waiting[f"admin_{callback.from_user.id}_state"] = "waiting_file"
    
    await callback.message.answer(f"📎 <b>Надішліть файл з читом</b> (або текст з інструкцією)")
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_no_"))
async def admin_reject(callback: types.CallbackQuery):
    target_id = int(callback.data.split("_")[2])
    try:
        await bot.send_message(target_id, f"❌ Ваша оплата була відхилена адміністратором.")
    except:
        pass
    await callback.message.answer(f"❌ Відхилено")
    await callback.answer()

@dp.message(F.document | F.text)
async def admin_file_or_key(message: types.Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    state = waiting.get(f"admin_{user_id}_state")
    target_id = waiting.get(f"admin_{user_id}_target")
    
    if state == "waiting_file" and target_id:
        file_id = None
        file_text = None
        
        if message.document:
            file_id = message.document.file_id
        elif message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_text = message.text
        
        waiting[f"admin_{user_id}_file"] = file_id
        waiting[f"admin_{user_id}_file_text"] = file_text
        waiting[f"admin_{user_id}_state"] = "waiting_key"
        
        await message.answer(f"🔑 <b>Введіть ключ активації</b>")
    
    elif state == "waiting_key" and target_id:
        key = message.text
        
        product = waiting.get(f"admin_{user_id}_product", "Unknown")
        days = int(waiting.get(f"admin_{user_id}_days", "0"))
        file_id = waiting.get(f"admin_{user_id}_file")
        file_text = waiting.get(f"admin_{user_id}_file_text")
        
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        product_name = CHEAT_NAMES.get(product, "Zroglik")
        expiry_display = datetime.strptime(expiry_date, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
        
        existing = cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (target_id,)).fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE users SET 
                    expiry_date = ?, 
                    product_name = ?, 
                    last_key = ?,
                    banned = 0,
                    ban_reason = NULL
                WHERE user_id = ?
            ''', (expiry_date, product_name, key, target_id))
        else:
            cursor.execute('''
                INSERT INTO users (user_id, expiry_date, product_name, subscribed_at, banned, last_key) 
                VALUES (?, ?, ?, ?, 0, ?)
            ''', (target_id, expiry_date, product_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), key))
        
        conn.commit()
        
        user_text = (f"{em(EMOJI['success'], '✅')} <b>Замовлення активовано!</b>\n\n"
                     f"{em(EMOJI['date'], '📅')} <b>Діє до:</b> {expiry_display}\n"
                     f"{em(EMOJI['key'], '🔑')} <b>Ключ:</b> <code>{key}</code>\n\n"
                     f"{em(EMOJI['welcome'], '💜')} Дякуємо за покупку в ZroglikShop!")
        
        try:
            if file_id:
                await bot.send_document(target_id, file_id, caption=user_text)
            elif file_text:
                await bot.send_message(target_id, user_text + f"\n\n📝 {file_text}")
            else:
                await bot.send_message(target_id, user_text)
            
            await message.answer(f"✅ <b>Ключ видано!</b>\n"
                                f"👤 Користувач: {target_id}\n"
                                f"📦 Товар: {product_name}\n"
                                f"📅 {days} дн. до {expiry_display}\n"
                                f"🔑 Ключ: <code>{key}</code>")
            
        except Exception as e:
            await message.answer(f"❌ Помилка: {e}")
        
        # Очищаем временные данные
        for k in list(waiting.keys()):
            if k.startswith(f"admin_{user_id}_"):
                del waiting[k]
        if waiting.get(f"{target_id}_product"):
            del waiting[f"{target_id}_product"]
        if waiting.get(f"{target_id}_days"):
            del waiting[f"{target_id}_days"]
        if waiting.get(f"{target_id}_waiting"):
            del waiting[f"{target_id}_waiting"]

# --- АДМИН-КОМАНДЫ ---
@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("❌ /ban [id] [причина]")
        return
    
    try:
        target_id = int(args[1])
        reason = args[2] if len(args) > 2 else "Нарушение правил"
        
        cursor.execute('UPDATE users SET banned = 1, ban_reason = ? WHERE user_id = ?', (reason, target_id))
        conn.commit()
        
        try:
            await bot.send_message(target_id, f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
        except:
            pass
        
        await message.answer(f"✅ Пользователь {target_id} забанен")
    except:
        await message.answer("❌ Неверный формат ID")

@dp.message(Command("unban"))
async def unban_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ /unban [id]")
        return
    
    try:
        target_id = int(args[1])
        cursor.execute('UPDATE users SET banned = 0, ban_reason = NULL WHERE user_id = ?', (target_id,))
        conn.commit()
        
        try:
            await bot.send_message(target_id, f"✅ <b>Вы разблокированы</b>")
        except:
            pass
        
        await message.answer(f"✅ Пользователь {target_id} разблокирован")
    except:
        await message.answer("❌ Неверный формат ID")

@dp.message(Command("users"))
async def users_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    
    await message.answer(
        f"👥 <b>Статистика користувачів:</b>\n\n"
        f"📊 Всього: {total}\n"
        f"✅ Активних: {active}\n"
        f"⛔ Забанено: {banned}"
    )

@dp.message(Command("broadcast"))
async def broadcast_start(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    waiting[f"{message.from_user.id}_broadcast"] = "waiting"
    await message.answer(f"📢 <b>Надішліть повідомлення для розсилки</b>")

@dp.message(F.text)
async def handle_broadcast_text(message: types.Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    if waiting.get(f"{user_id}_broadcast") == "waiting":
        waiting[f"{user_id}_broadcast"] = None
        users = cursor.execute('SELECT user_id FROM users WHERE banned = 0').fetchall()
        
        if not users:
            await message.answer("📭 Немає користувачів")
            return
        
        sent = 0
        for u in users:
            try:
                await bot.send_message(u['user_id'], message.text)
                sent += 1
            except:
                pass
            await asyncio.sleep(0.05)
        
        await message.answer(f"✅ Розсилка завершена!\nВідправлено: {sent}")

@dp.message(Command("cancel"))
async def cancel_operation(message: types.Message):
    user_id = message.from_user.id
    
    if waiting.get(f"{user_id}_waiting"):
        waiting[f"{user_id}_waiting"] = None
        await message.answer("✅ Операцію скасовано")
    
    if waiting.get(f"admin_{user_id}_state"):
        for k in list(waiting.keys()):
            if k.startswith(f"admin_{user_id}_"):
                del waiting[k]
        await message.answer("✅ Операцію скасовано")

# --- ЗАПУСК ---
async def main():
    print("🚀 Запуск ZroglikShop Bot на aiogram")
    print("👑 Адмін ID:", ADMIN_ID)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
