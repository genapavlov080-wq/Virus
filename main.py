import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import requests

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8655981898:AAE6-Ija80rwYN0FQoXIfcuAsNsUosAl_z0"
ADMIN_ID = 1471307057
CARD = "5167803275649049"
CARD_SBER = "2202206340487136"
CARD_SBER_NAME = "Вазген Б."

# Premium эмодзи ID
EMOJI = {
    "catalog": "5156877291397055163",
    "profile": "5904630315946611415",
    "reviews": "5938252440926163756",
    "support": "5208539876747662991",
    "back": "5960671702059848143",
    "admin": "6030445631921721471",
    "stats": "6032693626394382504",
    "broadcast": "5208539876747662991",
    "ban": "5208480322731137426",
    "unban": "5208657859499282838",
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
    "fire": "5208806229144524155",
    "welcome": "5208657859499282838",
    "target": "6073605466221451561",
    "money": "5890848474563352982",
    "calendar": "5413879192267805083",
    "card": "5393576224729633040",
    "photo": "5769126056262898415",
    "key": "6048733173171359488",
    "date": "5208474816583063829",
    "success": "5938252440926163756",
    "id_emoji": "6032693626394382504",
    "name": "5879770735999717115",
    "username": "5814247475141153332",
    "product_emoji": "6041730074376410123",
    "time": "5891211339170326418"
}

def em(emoji_id, fallback):
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# Цены
PRICES = {
    "zolo": {"1": "85 грн", "3": "180 грн", "7": "325 грн", "14": "400 грн", "30": "690 грн", "60": "1000 грн"},
    "impact": {"1": "115 грн", "7": "480 грн", "30": "1170 грн"},
    "king": {"1": "100 грн", "7": "425 грн", "30": "1060 грн"},
    "inferno": {"1": "80 грн", "3": "200 грн", "7": "350 грн", "15": "530 грн", "30": "690 грн", "60": "950 грн"},
    "zolo_cis": {"1": "70 грн", "3": "150 грн", "7": "250 грн", "14": "350 грн", "30": "700 грн", "60": "900 грн"}
}

CHEAT_NAMES = {
    "zolo": "Zolo Cheat",
    "impact": "Impact VIP",
    "king": "King Mod",
    "inferno": "Inferno Cheat",
    "zolo_cis": "Zolo CIS Edition"
}

# Фото
MAIN_PHOTO = "https://files.catbox.moe/6n69h6.jpg"
CHEAT_PHOTOS = {
    "zolo": "https://files.catbox.moe/opz3nu.png",
    "impact": "https://files.catbox.moe/9ztxkj.png",
    "king": "https://files.catbox.moe/vyhlec.png",
    "inferno": "https://files.catbox.moe/5vtpq1.png",
    "zolo_cis": "https://files.catbox.moe/deicc2.png"
}

# ========== БАЗА ДАННЫХ ==========
conn = sqlite3.connect('zroglik.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        expiry_date TEXT,
        product_name TEXT,
        banned INTEGER DEFAULT 0,
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

# ========== БОТ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

waiting = {}

# ========== REPLY КЛАВИАТУРЫ ==========
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Каталог", icon_custom_emoji_id=EMOJI["catalog"])],
        [KeyboardButton(text="Мій кабінет", icon_custom_emoji_id=EMOJI["profile"])],
        [KeyboardButton(text="Відгуки", icon_custom_emoji_id=EMOJI["reviews"]), KeyboardButton(text="Техпідтримка", icon_custom_emoji_id=EMOJI["support"])]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Статистика", icon_custom_emoji_id=EMOJI["stats"])],
        [KeyboardButton(text="Розсилка", icon_custom_emoji_id=EMOJI["broadcast"])],
        [KeyboardButton(text="Забанити", icon_custom_emoji_id=EMOJI["ban"]), KeyboardButton(text="Розбанити", icon_custom_emoji_id=EMOJI["unban"])],
        [KeyboardButton(text="Назад", icon_custom_emoji_id=EMOJI["back"])]
    ],
    resize_keyboard=True
)

back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Назад", icon_custom_emoji_id=EMOJI["back"])]],
    resize_keyboard=True
)

# ========== INLINE КЛАВИАТУРЫ ==========
def get_cheats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Zolo", callback_data="cheat_zolo", icon_custom_emoji_id=EMOJI["zolo"])],
        [InlineKeyboardButton(text="Impact VIP", callback_data="cheat_impact", icon_custom_emoji_id=EMOJI["impact"])],
        [InlineKeyboardButton(text="King Mod", callback_data="cheat_king", icon_custom_emoji_id=EMOJI["king"])],
        [InlineKeyboardButton(text="Inferno", callback_data="cheat_inferno", icon_custom_emoji_id=EMOJI["inferno"])],
        [InlineKeyboardButton(text="Zolo CIS", callback_data="cheat_zolo_cis", icon_custom_emoji_id=EMOJI["zolo_cis"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["back"])]
    ])

def get_period_kb(cheat):
    buttons = []
    for days in PRICES[cheat].keys():
        days_text = f"{days} дн." if days != "1" else "1 день"
        buttons.append([InlineKeyboardButton(text=f"{days_text} - {PRICES[cheat][days]}", callback_data=f"period_{cheat}_{days}", icon_custom_emoji_id=EMOJI["period"])])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog", icon_custom_emoji_id=EMOJI["back"])])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_kb(cheat, days):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Укр Банк", callback_data=f"bank_{cheat}_{days}", icon_custom_emoji_id=EMOJI["bank"])],
        [InlineKeyboardButton(text="Сбербанк", callback_data=f"bank_sber_{cheat}_{days}", icon_custom_emoji_id=EMOJI["sber"])],
        [InlineKeyboardButton(text="CryptoBot", callback_data=f"crypto_{cheat}_{days}", icon_custom_emoji_id=EMOJI["crypto"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_period_{cheat}", icon_custom_emoji_id=EMOJI["back"])]
    ])

def get_receipt_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Я оплатив", callback_data="send_receipt", icon_custom_emoji_id=EMOJI["receipt"])],
        [InlineKeyboardButton(text="Скасувати", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["cancel"])]
    ])

def get_reviews_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Канал з відгуками", url="https://t.me/zroglikrotzivv", icon_custom_emoji_id=EMOJI["reviews"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["back"])]
    ])

def get_admin_decision_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Одобрити", callback_data=f"adm_ok_{user_id}", icon_custom_emoji_id=EMOJI["approve"])],
        [InlineKeyboardButton(text="Відхилити", callback_data=f"adm_no_{user_id}", icon_custom_emoji_id=EMOJI["cancel"])]
    ])

def get_crypto_payment_kb(pay_url, invoice_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Оплатить", url=pay_url, icon_custom_emoji_id=EMOJI["crypto"])],
        [InlineKeyboardButton(text="Проверить оплату", callback_data=f"check_crypto_{invoice_id}", icon_custom_emoji_id=EMOJI["check"])],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu", icon_custom_emoji_id=EMOJI["back"])]
    ])

def get_subscribe_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ПОДПИСАТЬСЯ", url="https://t.me/+P2DK2IpHKBdiZGUy", icon_custom_emoji_id=EMOJI["catalog"])],
        [InlineKeyboardButton(text="ПРОВЕРИТИ", callback_data="check_sub", icon_custom_emoji_id=EMOJI["check"])]
    ])

# ========== ФУНКЦИИ ==========
def check_subscription(user_id):
    return True

def create_crypto_invoice(user_id, amount, days, product):
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"}
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
    except:
        pass
    return None

def check_crypto_payment(payment_id):
    url = "https://pay.crypt.bot/api/getInvoices"
    headers = {"Crypto-Pay-API-Token": "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"}
    params = {"invoice_ids": payment_id}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code == 200 and r.json().get("ok"):
            items = r.json()["result"].get("items", [])
            if items:
                return items[0]
    except:
        pass
    return None

# ========== ОБРАБОТЧИКИ ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', (user_id, username, first_name))
    conn.commit()
    
    text = (f"{em(EMOJI['fire'], '🔥')} <b>ZROGLIK KEYS</b>\n\n"
            f"{em(EMOJI['welcome'], '👋')} Ласкаво просимо до ZroglikShop!\n"
            f"{em(EMOJI['target'], '🎯')} Тут ти можеш купити чити для PUBG Mobile")
    
    if user_id == ADMIN_ID:
        await message.answer_photo(MAIN_PHOTO, caption=text, reply_markup=admin_kb, parse_mode="HTML")
    else:
        await message.answer_photo(MAIN_PHOTO, caption=text, reply_markup=main_kb, parse_mode="HTML")

@dp.message(F.text == "Каталог")
async def catalog(message: types.Message):
    text = f"{em(EMOJI['target'], '🎯')} <b>PUBG Mobile</b>\nВиберіть чит:"
    await message.answer(text, reply_markup=get_cheats_kb(), parse_mode="HTML")

@dp.message(F.text == "Мій кабінет")
async def profile(message: types.Message):
    user_id = message.from_user.id
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if user and user[3]:
        expiry = datetime.strptime(user[3], '%Y-%m-%d %H:%M:%S')
        diff = expiry - datetime.now()
        if diff.total_seconds() > 0:
            time_left = f"{diff.days} дн. {diff.seconds//3600} год."
            product = user[4] or "Немає"
            key = user[6] or "Немає"
            expiry_display = expiry.strftime('%d.%m.%Y %H:%M')
        else:
            time_left = "❌ Закінчилась"
            product = user[4] or "Немає"
            key = user[6] or "Немає"
            expiry_display = "Немає"
    else:
        time_left = "Немає підписки"
        product = "Немає"
        key = "Немає"
        expiry_display = "Немає"
    
    text = (f"{em(EMOJI['profile'], '👤')} <b>МІЙ КАБІНЕТ</b>\n\n"
            f"{em(EMOJI['id_emoji'], '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
            f"{em(EMOJI['name'], '📛')} <b>Ім'я:</b> {message.from_user.first_name}\n"
            f"{em(EMOJI['username'], '🔖')} <b>Username:</b> @{message.from_user.username or 'Немає'}\n"
            f"{em(EMOJI['product_emoji'], '📦')} <b>Товар:</b> {product}\n"
            f"{em(EMOJI['time'], '⏳')} <b>Залишилось:</b> {time_left}\n"
            f"{em(EMOJI['key'], '🔑')} <b>Ключ:</b> <code>{key}</code>\n"
            f"{em(EMOJI['date'], '📅')} <b>Діє до:</b> {expiry_display}")
    
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message(F.text == "Відгуки")
async def reviews(message: types.Message):
    text = f"{em(EMOJI['reviews'], '⭐')} <b>Наші відгуки</b>"
    await message.answer(text, reply_markup=get_reviews_kb(), parse_mode="HTML")

@dp.message(F.text == "Техпідтримка")
async def support(message: types.Message):
    text = f"{em(EMOJI['support'], '🎮')} <b>Технічна підтримка</b>\n\nЗв'яжіться з нами: @ZrogIikCheat"
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message(F.text == "Назад")
async def back(message: types.Message):
    user_id = message.from_user.id
    text = (f"{em(EMOJI['fire'], '🔥')} <b>ZROGLIK KEYS</b>\n\n"
            f"{em(EMOJI['welcome'], '👋')} Ласкаво просимо до ZroglikShop!\n"
            f"{em(EMOJI['target'], '🎯')} Тут ти можеш купити чити для PUBG Mobile")
    
    if user_id == ADMIN_ID:
        await message.answer_photo(MAIN_PHOTO, caption=text, reply_markup=admin_kb, parse_mode="HTML")
    else:
        await message.answer_photo(MAIN_PHOTO, caption=text, reply_markup=main_kb, parse_mode="HTML")

# ========== INLINE ОБРАБОТЧИКИ ==========
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.delete()
    await cmd_start(call.message)
    await call.answer()

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(call: types.CallbackQuery):
    text = f"{em(EMOJI['target'], '🎯')} <b>PUBG Mobile</b>\nВиберіть чит:"
    await call.message.edit_text(text, reply_markup=get_cheats_kb(), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("back_to_period_"))
async def back_to_period(call: types.CallbackQuery):
    cheat = call.data.split("_")[3]
    photo = CHEAT_PHOTOS.get(cheat)
    desc = f"{CHEAT_NAMES[cheat]}\n\n{em(EMOJI['money'], '💰')} <b>Ціни:</b>\n"
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        desc += f"├ {days_text}: {em(EMOJI['money'], '💰')} {price}\n"
    desc += f"\n{em(EMOJI['period'], '💳')} <b>Виберіть період:</b>"
    
    if photo:
        await call.message.delete()
        await call.message.answer_photo(photo, caption=desc, reply_markup=get_period_kb(cheat), parse_mode="HTML")
    else:
        await call.message.edit_text(desc, reply_markup=get_period_kb(cheat), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("cheat_"))
async def show_cheat(call: types.CallbackQuery):
    cheat = call.data.split("_")[1]
    photo = CHEAT_PHOTOS.get(cheat)
    desc = f"{CHEAT_NAMES[cheat]}\n\n{em(EMOJI['money'], '💰')} <b>Ціни:</b>\n"
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        desc += f"├ {days_text}: {em(EMOJI['money'], '💰')} {price}\n"
    desc += f"\n{em(EMOJI['period'], '💳')} <b>Виберіть період:</b>"
    
    if photo:
        await call.message.delete()
        await call.message.answer_photo(photo, caption=desc, reply_markup=get_period_kb(cheat), parse_mode="HTML")
    else:
        await call.message.edit_text(desc, reply_markup=get_period_kb(cheat), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("period_"))
async def select_period(call: types.CallbackQuery):
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    waiting[f"{call.from_user.id}_cheat"] = cheat
    waiting[f"{call.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    desc = f"{CHEAT_NAMES[cheat]}\n\n{em(EMOJI['calendar'], '📅')} {days} дн.\n{em(EMOJI['money'], '💰')} {price}\n\n{em(EMOJI['card'], '💳')} <b>Виберіть спосіб оплати:</b>"
    await call.message.edit_text(desc, reply_markup=get_payment_kb(cheat, days), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("bank_"))
async def bank_payment(call: types.CallbackQuery):
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    waiting[f"{call.from_user.id}_cheat"] = cheat
    waiting[f"{call.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    text = (f"{em(EMOJI['bank'], '💳')} <b>Оплата банківською карткою</b>\n\n"
            f"{em(EMOJI['money'], '💰')} <b>Сума:</b> {price}\n"
            f"{em(EMOJI['bank'], '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
            f"{em(EMOJI['cancel'], '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em(EMOJI['photo'], '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    await call.message.edit_text(text, reply_markup=get_receipt_kb(), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("bank_sber_"))
async def sber_payment(call: types.CallbackQuery):
    parts = call.data.split("_")
    cheat = parts[2]
    days = parts[3]
    waiting[f"{call.from_user.id}_cheat"] = cheat
    waiting[f"{call.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    text = (f"{em(EMOJI['sber'], '🏦')} <b>Оплата Сбербанк</b>\n\n"
            f"{em(EMOJI['money'], '💰')} <b>Сума:</b> {price}\n"
            f"{em(EMOJI['sber'], '💳')} <b>Карта:</b> <code>{CARD_SBER}</code>\n"
            f"{em(EMOJI['name'], '👤')} <b>Отримувач:</b> {CARD_SBER_NAME}\n"
            f"{em(EMOJI['cancel'], '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em(EMOJI['photo'], '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    await call.message.edit_text(text, reply_markup=get_receipt_kb(), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("crypto_"))
async def crypto_payment(call: types.CallbackQuery):
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    user_id = call.from_user.id
    price_str = PRICES[cheat][days].replace(" грн", "")
    amount = round(int(price_str) / 43, 2)
    invoice = create_crypto_invoice(user_id, amount, days, cheat)
    if not invoice:
        await call.message.edit_text(f"{em(EMOJI['cancel'], '❌')} Ошибка создания платежа", parse_mode="HTML")
        return
    cursor.execute('INSERT INTO crypto_payments (payment_id, user_id, amount, days, product, created_at) VALUES (?, ?, ?, ?, ?, ?)', 
                   (str(invoice["invoice_id"]), user_id, amount, days, cheat, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    text = (f"{em(EMOJI['crypto'], '💎')} <b>Оплата через CryptoBot</b>\n\n"
            f"{em(EMOJI['money'], '💰')} <b>Сума:</b> {amount}$\n"
            f"{em(EMOJI['calendar'], '📅')} <b>Тариф:</b> {days} дней")
    await call.message.edit_text(text, reply_markup=get_crypto_payment_kb(invoice["pay_url"], invoice["invoice_id"]), parse_mode="HTML")
    await call.answer()
@dp.callback_query(F.data.startswith("check_crypto_"))
async def check_crypto(call: types.CallbackQuery):
    payment_id = int(call.data.replace("check_crypto_", ""))
    user_id = call.from_user.id
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
            await call.message.edit_text(text, parse_mode="HTML")
            await bot.send_message(ADMIN_ID, f"{em(EMOJI['money'], '💰')} Новый крипто-платёж\n👤 {user_id}\n📅 {days} дней\n💎 {CHEAT_NAMES[product]}")
            await call.answer("✅ Оплата подтверждена!")
    else:
        await call.answer("⏳ Платёж ещё не подтверждён", show_alert=True)

@dp.callback_query(F.data == "send_receipt")
async def send_receipt(call: types.CallbackQuery):
    waiting[f"{call.from_user.id}_waiting"] = "receipt"
    await call.message.edit_text(f"{em(EMOJI['photo'], '📸')} Надішліть скріншот чека (одним фото)", parse_mode="HTML")
    await call.answer()

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if waiting.get(f"{user_id}_waiting") == "receipt":
        waiting[f"{user_id}_waiting"] = None
        cheat = waiting.get(f"{user_id}_cheat", "Unknown")
        days = waiting.get(f"{user_id}_days", "0")
        photo = message.photo[-1].file_id
        
        await bot.send_photo(ADMIN_ID, photo, caption=f"{em(EMOJI['photo'], '🔔')} Чек від {user_id}\n{em(EMOJI['product_emoji'], '📦')} Товар: {cheat}\n{em(EMOJI['time'], '⏳')} Тариф: {days} днів", reply_markup=get_admin_decision_kb(user_id), parse_mode="HTML")
        await message.answer(f"{em(EMOJI['success'], '✅')} Чек відправлено адміністратору! Очікуйте підтвердження.", parse_mode="HTML")

# ========== АДМИН-ОБРАБОТЧИКИ ==========
@dp.callback_query(F.data.startswith("adm_ok_"))
async def admin_ok(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[2])
    cheat = waiting.get(f"{target_id}_cheat", "Unknown")
    days = int(waiting.get(f"{target_id}_days", "0"))
    
    expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    expiry_display = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
    key = f"KEY_{target_id}_{int(datetime.now().timestamp())}"
    
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ?, last_key = ? WHERE user_id = ?', 
                   (expiry, CHEAT_NAMES.get(cheat, cheat), key, target_id))
    conn.commit()
    
    user_text = (f"{em(EMOJI['success'], '✅')} <b>Замовлення активовано!</b>\n\n"
                 f"{em(EMOJI['date'], '📅')} <b>Діє до:</b> {expiry_display}\n"
                 f"{em(EMOJI['key'], '🔑')} <b>Ключ:</b> <code>{key}</code>\n\n"
                 f"{em(EMOJI['welcome'], '💜')} Дякуємо за покупку!")
    
    await bot.send_message(target_id, user_text, parse_mode="HTML")
    await call.message.answer(f"{em(EMOJI['success'], '✅')} Ключ видано користувачу {target_id}", parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("adm_no_"))
async def admin_no(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[2])
    await bot.send_message(target_id, f"{em(EMOJI['cancel'], '❌')} Ваша оплата відхилена", parse_mode="HTML")
    await call.message.answer(f"{em(EMOJI['cancel'], '❌')} Відхилено {target_id}", parse_mode="HTML")
    await call.answer()

@dp.message(F.text == "Статистика")
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    text = (f"{em(EMOJI['stats'], '📊')} <b>Статистика</b>\n\n"
            f"{em(EMOJI['catalog'], '👥')} <b>Всього:</b> {total}\n"
            f"{em(EMOJI['success'], '✅')} <b>Активних:</b> {active}\n"
            f"{em(EMOJI['cancel'], '⛔')} <b>Забанено:</b> {banned}")
    await message.answer(text, reply_markup=admin_kb, parse_mode="HTML")

@dp.message(F.text == "Розсилка")
async def broadcast_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    waiting[f"{message.from_user.id}_broadcast"] = "waiting"
    await message.answer(f"{em(EMOJI['broadcast'], '📢')} Надішліть повідомлення для розсилки", reply_markup=back_kb, parse_mode="HTML")

@dp.message(F.text == "Забанити")
async def ban_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    waiting[f"{message.from_user.id}_ban"] = "waiting"
    await message.answer(f"{em(EMOJI['ban'], '⛔')} Введіть ID користувача", parse_mode="HTML")

@dp.message(F.text == "Розбанити")
async def unban_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    waiting[f"{message.from_user.id}_unban"] = "waiting"
    await message.answer(f"{em(EMOJI['unban'], '✅')} Введіть ID користувача", parse_mode="HTML")

@dp.message()
async def admin_commands(message: types.Message):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        return
    
    if waiting.get(f"{user_id}_ban") == "waiting":
        waiting[f"{user_id}_ban"] = None
        try:
            target_id = int(message.text)
            cursor.execute('UPDATE users SET banned = 1 WHERE user_id = ?', (target_id,))
            conn.commit()
            await message.answer(f"{em(EMOJI['success'], '✅')} Забанено {target_id}", parse_mode="HTML")
        except:
            await message.answer("❌ Неверный ID")
        return
    
    if waiting.get(f"{user_id}_unban") == "waiting":
        waiting[f"{user_id}_unban"] = None
        try:
            target_id = int(message.text)
            cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (target_id,))
            conn.commit()
            await message.answer(f"{em(EMOJI['success'], '✅')} Розбанено {target_id}", parse_mode="HTML")
        except:
            await message.answer("❌ Неверный ID")
        return
    
    if waiting.get(f"{user_id}_broadcast") == "waiting":
        waiting[f"{user_id}_broadcast"] = None
        users = cursor.execute('SELECT user_id FROM users WHERE banned = 0').fetchall()
        sent = 0
        for u in users:
            try:
                await bot.send_message(u[0], message.text, parse_mode="HTML")
                sent += 1
            except:
                pass
            await asyncio.sleep(0.05)
        await message.answer(f"{em(EMOJI['success'], '✅')} Розсилка завершена! Відправлено: {sent}", parse_mode="HTML")
        return

# ========== ЗАПУСК ==========
async def main():
    print("🚀 Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
