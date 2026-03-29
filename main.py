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
conn.commit()

# ========== БОТ ==========
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

waiting = {}

# ========== REPLY КЛАВИАТУРЫ (с Premium эмодзи через icon_custom_emoji_id) ==========
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
        [InlineKeyboardButton(text="Zolo", callback_data="cheat_zolo")],
        [InlineKeyboardButton(text="Impact VIP", callback_data="cheat_impact")],
        [InlineKeyboardButton(text="King Mod", callback_data="cheat_king")],
        [InlineKeyboardButton(text="Inferno", callback_data="cheat_inferno")],
        [InlineKeyboardButton(text="Zolo CIS", callback_data="cheat_zolo_cis")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
    ])

def get_period_kb(cheat):
    buttons = []
    for days in PRICES[cheat]:
        buttons.append([InlineKeyboardButton(text=f"{days} дн. - {PRICES[cheat][days]}", callback_data=f"period_{cheat}_{days}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_kb(cheat, days):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Укр Банк", callback_data=f"bank_{cheat}_{days}")],
        [InlineKeyboardButton(text="Сбербанк", callback_data=f"bank_sber_{cheat}_{days}")],
        [InlineKeyboardButton(text="CryptoBot", callback_data=f"crypto_{cheat}_{days}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"back_to_period_{cheat}")]
    ])

def get_receipt_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатив", callback_data="send_receipt")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="back_to_menu")]
    ])

def get_admin_decision_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Одобрити", callback_data=f"adm_ok_{user_id}")],
        [InlineKeyboardButton(text="❌ Відхилити", callback_data=f"adm_no_{user_id}")]
    ])

# ========== ФУНКЦИИ ==========
def check_subscription(user_id):
    return True  # ОТКЛЮЧАЕМ ПРОВЕРКУ ДЛЯ ТЕСТА

# ========== ОБРАБОТЧИКИ ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)', (user_id, username, first_name))
    conn.commit()
    
    text = f"{em(EMOJI['catalog'], '🔥')} <b>ZROGLIK KEYS</b>\n\n{em(EMOJI['profile'], '👋')} Ласкаво просимо!\n{em(EMOJI['stats'], '🎯')} Купуй чити для PUBG Mobile"
    
    if user_id == ADMIN_ID:
        await message.answer(text, reply_markup=admin_kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=main_kb, parse_mode="HTML")

@dp.message(F.text == "Каталог")
async def catalog(message: types.Message):
    text = f"{em(EMOJI['catalog'], '🎯')} Виберіть чит:"
    await message.answer(text, reply_markup=get_cheats_kb(), parse_mode="HTML")

@dp.message(F.text == "Мій кабінет")
async def profile(message: types.Message):
    user_id = message.from_user.id
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    if user and user[3]:  # expiry_date
        expiry = datetime.strptime(user[3], '%Y-%m-%d %H:%M:%S')
        diff = expiry - datetime.now()
        if diff.total_seconds() > 0:
            time_left = f"{diff.days} дн. {diff.seconds//3600} год."
            product = user[4] or "Немає"
            key = user[6] or "Немає"
        else:
            time_left = "❌ Закінчилась"
            product = user[4] or "Немає"
            key = user[6] or "Немає"
    else:
        time_left = "Немає підписки"
        product = "Немає"
        key = "Немає"
    
    text = (f"{em(EMOJI['profile'], '👤')} <b>МІЙ КАБІНЕТ</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📛 Ім'я: {message.from_user.first_name}\n"
            f"📦 Товар: {product}\n"
            f"⏳ Залишилось: {time_left}\n"
            f"🔑 Ключ: <code>{key}</code>")
    
    await message.answer(text, reply_markup=back_kb, parse_mode="HTML")

@dp.message(F.text == "Відгуки")
async def reviews(message: types.Message):
    await message.answer("⭐ Канал з відгуками: https://t.me/zroglikrotzivv", reply_markup=back_kb)

@dp.message(F.text == "Техпідтримка")
async def support(message: types.Message):
    await message.answer("🎮 Техпідтримка: @ZrogIikCheat", reply_markup=back_kb)

@dp.message(F.text == "Назад")
async def back(message: types.Message):
    user_id = message.from_user.id
    text = f"{em(EMOJI['catalog'], '🔥')} <b>ZROGLIK KEYS</b>\n\n{em(EMOJI['profile'], '👋')} Ласкаво просимо!\n{em(EMOJI['stats'], '🎯')} Купуй чити для PUBG Mobile"
    
    if user_id == ADMIN_ID:
        await message.answer(text, reply_markup=admin_kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=main_kb, parse_mode="HTML")

# ========== INLINE ОБРАБОТЧИКИ ==========
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(call: types.CallbackQuery):
    await call.message.delete()
    await cmd_start(call.message)

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(call: types.CallbackQuery):
    text = f"{em(EMOJI['catalog'], '🎯')} Виберіть чит:"
    await call.message.edit_text(text, reply_markup=get_cheats_kb(), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("cheat_"))
async def show_cheat(call: types.CallbackQuery):
    cheat = call.data.split("_")[1]
    text = f"{CHEAT_NAMES[cheat]}\n\n💰 Ціни:\n"
    for days, price in PRICES[cheat].items():
        days_t = f"{days} дн." if days != "1" else "1 день"
        text += f"├ {days_t}: {price}\n"
    text += f"\n💳 Виберіть період:"
    await call.message.edit_text(text, reply_markup=get_period_kb(cheat), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("period_"))
async def select_period(call: types.CallbackQuery):
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    waiting[f"{call.from_user.id}_cheat"] = cheat
    waiting[f"{call.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    text = f"{CHEAT_NAMES[cheat]}\n\n📅 {days} дн.\n💰 {price}\n\n💳 Виберіть спосіб оплати:"
    await call.message.edit_text(text, reply_markup=get_payment_kb(cheat, days), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("bank_"))
async def bank_payment(call: types.CallbackQuery):
    parts = call.data.split("_")
    cheat = parts[1]
    days = parts[2]
    waiting[f"{call.from_user.id}_cheat"] = cheat
    waiting[f"{call.from_user.id}_days"] = days
    price = PRICES[cheat][days]
    text = (f"💳 Оплата банківською карткою\n\n💰 Сума: {price}\n"
            f"💳 Карта: <code>{CARD}</code>\n❗ Коментар: За цифрові товари\n\n"
            f"📸 Після оплати натисніть кнопку нижче і надішліть скріншот")
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
    text = (f"🏦 Оплата Сбербанк\n\n💰 Сума: {price}\n"
            f"💳 Карта: <code>{CARD_SBER}</code>\n👤 Отримувач: {CARD_SBER_NAME}\n"
            f"❗ Коментар: За цифрові товари\n\n📸 Після оплати натисніть кнопку нижче і надішліть скріншот")
    await call.message.edit_text(text, reply_markup=get_receipt_kb(), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data == "send_receipt")
async def send_receipt(call: types.CallbackQuery):
    waiting[f"{call.from_user.id}_waiting"] = "receipt"
    await call.message.edit_text("📸 Надішліть скріншот чека (одним фото)")
    await call.answer()

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    if waiting.get(f"{user_id}_waiting") == "receipt":
        waiting[f"{user_id}_waiting"] = None
        cheat = waiting.get(f"{user_id}_cheat", "Unknown")
        days = waiting.get(f"{user_id}_days", "0")
        photo = message.photo[-1].file_id
        
        await bot.send_photo(ADMIN_ID, photo, caption=f"🔔 Чек від {user_id}\n📦 Товар: {cheat}\n⏳ Тариф: {days} днів", reply_markup=get_admin_decision_kb(user_id))
        await message.answer("✅ Чек відправлено адміністратору!")

# ========== АДМИН-ОБРАБОТЧИКИ ==========
@dp.callback_query(F.data.startswith("adm_ok_"))
async def admin_ok(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[2])
    cheat = waiting.get(f"{target_id}_cheat", "Unknown")
    days = int(waiting.get(f"{target_id}_days", "0"))
    
    expiry = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    key = f"KEY_{target_id}_{int(datetime.now().timestamp())}"
    
    cursor.execute('UPDATE users SET expiry_date = ?, product_name = ?, last_key = ? WHERE user_id = ?', 
                   (expiry, CHEAT_NAMES.get(cheat, cheat), key, target_id))
    conn.commit()
    
    await bot.send_message(target_id, f"✅ Замовлення активовано до {expiry}\n🔑 Ключ: <code>{key}</code>", parse_mode="HTML")
    await call.message.answer(f"✅ Ключ видано користувачу {target_id}")
    await call.answer()

@dp.callback_query(F.data.startswith("adm_no_"))
async def admin_no(call: types.CallbackQuery):
    target_id = int(call.data.split("_")[2])
    await bot.send_message(target_id, "❌ Ваша оплата відхилена")
    await call.message.answer(f"❌ Відхилено {target_id}")
    await call.answer()

@dp.message(F.text == "Статистика")
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    await message.answer(f"📊 Статистика\n\n👥 Всього: {total}\n✅ Активних: {active}")

@dp.message(F.text == "Розсилка")
async def broadcast_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    waiting[f"{message.from_user.id}_broadcast"] = "waiting"
    await message.answer("📢 Надішліть повідомлення для розсилки")

@dp.message(F.text == "Забанити")
async def ban_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    waiting[f"{message.from_user.id}_ban"] = "waiting"
    await message.answer("⛔ Введіть ID користувача")

@dp.message(F.text == "Розбанити")
async def unban_prompt(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    waiting[f"{message.from_user.id}_unban"] = "waiting"
    await message.answer("✅ Введіть ID користувача")

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
            await message.answer(f"✅ Забанено {target_id}")
        except:
            await message.answer("❌ Неверный ID")
        return
    
    if waiting.get(f"{user_id}_unban") == "waiting":
        waiting[f"{user_id}_unban"] = None
        try:
            target_id = int(message.text)
            cursor.execute('UPDATE users SET banned = 0 WHERE user_id = ?', (target_id,))
            conn.commit()
            await message.answer(f"✅ Розбанено {target_id}")
        except:
            await message.answer("❌ Неверный ID")
        return
    
    if waiting.get(f"{user_id}_broadcast") == "waiting":
        waiting[f"{user_id}_broadcast"] = None
        users = cursor.execute('SELECT user_id FROM users WHERE banned = 0').fetchall()
        sent = 0
        for u in users:
            try:
                await bot.send_message(u[0], message.text)
                sent += 1
            except:
                pass
            await asyncio.sleep(0.05)
        await message.answer(f"✅ Розсилка завершена! Відправлено: {sent}")
        return

# ========== ЗАПУСК ==========
async def main():
    print("🚀 Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
