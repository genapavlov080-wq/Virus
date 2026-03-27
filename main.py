import urllib.request
import json
import time
import sqlite3
import logging
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8522948833:AAFPgQz77GDY2YafZRtNMM9ilcxZ65_2wus"
ADMIN_ID = 1471307057
CARD = "4441111008011946"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ID каналов для обязательной подписки
REQUIRED_CHANNELS = [
    {"id": -1002271436385, "url": "https://t.me/plutoniumrewiews", "name": "Plutonium Reviews"},
    {"id": -1002544275396, "url": "https://t.me/OfficialPlutonium", "name": "Official Plutonium"}
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СБРОС ВЕБХУКА ---
try:
    urllib.request.urlopen(f"{API_URL}/deleteWebhook?drop_pending_updates=true", timeout=5)
    urllib.request.urlopen(f"{API_URL}/getUpdates?offset=-1", timeout=5)
    time.sleep(1)
    print("✅ Webhook сброшен")
except:
    pass

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
conn.commit()

# --- ФУНКЦИИ API ---
def api(method, data=None):
    url = f"{API_URL}/{method}"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode() if data else None,
            headers={'Content-Type': 'application/json'} if data else {},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"API error: {e}")
        return {'ok': False}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api("sendMessage", data)

def send_photo(chat_id, photo, caption=None, reply_markup=None):
    data = {"chat_id": chat_id, "photo": photo, "parse_mode": "HTML"}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api("sendPhoto", data)

def send_document(chat_id, document, caption=None):
    data = {"chat_id": chat_id, "document": document, "parse_mode": "HTML"}
    if caption:
        data["caption"] = caption
    return api("sendDocument", data)

def edit_message_caption(chat_id, message_id, caption, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    return api("editMessageCaption", data)

def get_updates(offset=None, timeout=30):
    data = {"timeout": timeout}
    if offset is not None:
        data["offset"] = offset
    return api("getUpdates", data)

def answer_callback(callback_id, text=None, show_alert=False):
    data = {"callback_query_id": callback_id}
    if text:
        data["text"] = text
    if show_alert:
        data["show_alert"] = True
    return api("answerCallbackQuery", data)

# --- ФУНКЦИЯ ДЛЯ ЭМОДЗИ ---
def em(emoji_id, char):
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

# --- ПРОВЕРКА ПОДПИСКИ ---
def check_all_subscriptions(user_id):
    """Проверяет подписку на все обязательные каналы"""
    for channel in REQUIRED_CHANNELS:
        try:
            result = api("getChatMember", {"chat_id": channel["id"], "user_id": user_id})
            if not result.get('ok'):
                return False, channel["url"], channel["name"]
            status = result['result']['status']
            if status not in ['member', 'administrator', 'creator']:
                return False, channel["url"], channel["name"]
        except Exception as e:
            logger.error(f"Check subscription error: {e}")
            return False, channel["url"], channel["name"]
    return True, None, None

def get_subscribe_keyboard():
    """Клавиатура для подписки"""
    buttons = []
    for channel in REQUIRED_CHANNELS:
        buttons.append([{"text": f"{em('5927118708873892465', '📢')} Подписаться на {channel['name']}", "url": channel["url"], "icon_custom_emoji_id": "5927118708873892465"}])
    buttons.append([{"text": f"{em('5774022692642492953', '🔄')} Проверить подписку", "callback_data": "check_sub", "icon_custom_emoji_id": "5774022692642492953"}])
    return {"inline_keyboard": buttons}

# --- ХРАНИЛИЩА ---
waiting = {}

# --- КНОПКИ ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": f"{em('5156877291397055163', '🔑')} Купить ключ", "callback_data": "buy_key", "icon_custom_emoji_id": "5156877291397055163"},
             {"text": f"{em('5904630315946611415', '👤')} Мой профиль", "callback_data": "profile", "icon_custom_emoji_id": "5904630315946611415"}],
            [{"text": f"{em('5938252440926163756', '⭐')} Наши отзывы", "callback_data": "show_reviews", "icon_custom_emoji_id": "5938252440926163756"},
             {"text": f"{em('5208539876747662991', '🆘')} Техподдержка", "url": "https://t.me/IllyaGarant", "icon_custom_emoji_id": "5208539876747662991"}]
        ]
    }

def get_back_button(target):
    return {"inline_keyboard": [[{"text": f"{em('5960671702059848143', '⬅️')} Назад", "callback_data": target, "icon_custom_emoji_id": "5960671702059848143"}]]}

# --- ЦЕНЫ PUBG ЧИТОВ ---
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

CHEAT_PHOTOS = {
    "zolo": "https://files.catbox.moe/opz3nu.png",
    "impact": "https://files.catbox.moe/9ztxkj.png",
    "king": "https://files.catbox.moe/vyhlec.png",
    "inferno": "https://files.catbox.moe/5vtpq1.png",
    "zolo_cis": "https://files.catbox.moe/deicc2.png"
}

# --- ОСНОВНЫЕ ФОТО ---
MAIN_PHOTO = "https://files.catbox.moe/6n69h6.jpg"
PROFILE_PHOTO = "https://files.catbox.moe/kybf8l.png"
REVIEWS_PHOTO = "https://files.catbox.moe/3z96th.png"

# --- ОБРАБОТЧИКИ ---
def handle_start(chat_id, user_id, username, first_name):
    # Проверяем бан
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    # Проверяем подписку на каналы
    subscribed, channel_url, channel_name = check_all_subscriptions(user_id)
    if not subscribed:
        text = (f"{em('6037249452824072506', '🔒')} <b>Доступ ограничен!</b>\n\n"
                f"Для доступа к боту необходимо подписаться на канал:\n"
                f"{em('5927118708873892465', '📢')} <b>{channel_name}</b>\n\n"
                f"После подписки нажмите кнопку «Проверить подписку»")
        send_photo(chat_id, MAIN_PHOTO, text, get_subscribe_keyboard())
        return
    
    # Сохраняем пользователя
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, subscribed_at) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?))
    ''', (user_id, username, first_name, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = (f"{em('5339472242529045815', '🔥')} <b>ZROGLIK KEYS</b>\n\n"
            f"{em('5208657859499282838', '👋')} Добро пожаловать в ZroglikShop!\n"
            f"{em('6073605466221451561', '🎯')} Здесь ты можешь купить читы для PUBG Mobile")
    
    send_photo(chat_id, MAIN_PHOTO, text, get_main_keyboard())

def handle_check_subscription(chat_id, user_id, message_id):
    """Проверка подписки после нажатия кнопки"""
    subscribed, _, _ = check_all_subscriptions(user_id)
    if subscribed:
        # Сохраняем пользователя если его нет
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, subscribed_at) 
            VALUES (?, ?)
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        
        text = (f"{em('5339472242529045815', '🔥')} <b>ZROGLIK KEYS</b>\n\n"
                f"{em('5208657859499282838', '👋')} Добро пожаловать в ZroglikShop!\n"
                f"{em('6073605466221451561', '🎯')} Здесь ты можешь купить читы для PUBG Mobile")
        edit_message_caption(chat_id, message_id, text, get_main_keyboard())
        answer_callback(message_id, "✅ Подписка подтверждена!")
    else:
        answer_callback(message_id, "❌ Вы еще не подписались на все каналы!", True)

def handle_profile(chat_id, user_id, message_id, username, first_name):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Вы заблокированы")
        return
    
    user = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    res = cursor.execute('SELECT expiry_date, product_name, last_key FROM users WHERE user_id = ?', (user_id,)).fetchone()
    
    time_left = "Нет активной подписки"
    product = "Нет"
    last_key = ""
    
    if res and res['expiry_date']:
        try:
            expiry = datetime.strptime(res['expiry_date'], '%Y-%m-%d %H:%M:%S')
            diff = expiry - datetime.now()
            if diff.total_seconds() > 0:
                days = diff.days
                hours = diff.seconds // 3600
                time_left = f"{days} дн. {hours} ч." if days > 0 else f"{hours} ч."
                product = res['product_name'] if res['product_name'] else "Нет"
                last_key = res['last_key'] if res['last_key'] else ""
            else:
                time_left = "❌ Истекла"
                product = res['product_name'] if res['product_name'] else "Нет"
        except:
            pass
    
    user_name = user['first_name'] if user and user['first_name'] else str(user_id)
    user_username = user['username'] if user and user['username'] else "Нет"
    
    text = (f"{em('5904630315946611415', '👤')} <b>ПРОФІЛЬ</b>\n\n"
            f"{em('6032693626394382504', '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
            f"{em('5879770735999717115', '📛')} <b>Ім'я:</b> {user_name}\n"
            f"{em('5814247475141153332', '🔖')} <b>Username:</b> @{user_username}\n"
            f"{em('6041730074376410123', '📦')} <b>Товар:</b> {product}\n"
            f"{em('5891211339170326418', '⏳')} <b>Залишилось:</b> {time_left}")
    
    if last_key:
        text += f"\n{em('6048733173171359488', '🔑')} <b>Ваш ключ:</b> <code>{last_key}</code>"
    
    edit_message_caption(chat_id, message_id, text, get_back_button("start"))

def handle_reviews(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": f"{em('6028171274939797252', '🔗')} Канал с отзывами", "url": "https://t.me/plutoniumrewiews", "icon_custom_emoji_id": "6028171274939797252"}],
            [{"text": f"{em('5960671702059848143', '⬅️')} Назад", "callback_data": "start", "icon_custom_emoji_id": "5960671702059848143"}]
        ]
    }
    text = f"{em('5938252440926163756', '⭐')} <b>Наші відгуки</b>"
    edit_message_caption(chat_id, message_id, text, kb)

def handle_buy_key(chat_id, message_id):
    kb = {
        "inline_keyboard": [
            [{"text": f"{em('5451653043089070124', '🔥')} Zolo", "callback_data": "cheat_zolo", "icon_custom_emoji_id": "5451653043089070124"}],
            [{"text": f"{em('5276079251089547977', '⚡')} Impact VIP", "callback_data": "cheat_impact", "icon_custom_emoji_id": "5276079251089547977"}],
            [{"text": f"{em('6172520285330214110', '👑')} King Mod", "callback_data": "cheat_king", "icon_custom_emoji_id": "6172520285330214110"}],
            [{"text": f"{em('5296273418516187626', '💥')} Inferno", "callback_data": "cheat_inferno", "icon_custom_emoji_id": "5296273418516187626"}],
            [{"text": f"{em('5451841459009379088', '🎮')} Zolo CIS", "callback_data": "cheat_zolo_cis", "icon_custom_emoji_id": "5451841459009379088"}],
            [{"text": f"{em('5960671702059848143', '⬅️')} Назад", "callback_data": "start", "icon_custom_emoji_id": "5960671702059848143"}]
        ]
    }
    text = f"{em('6073605466221451561', '🎯')} <b>PUBG Mobile</b>\nВиберіть чит:"
    edit_message_caption(chat_id, message_id, text, kb)

def show_cheat(chat_id, message_id, cheat):
    desc = f"{CHEAT_NAMES[cheat]}\n\n"
    desc += f"{em('5339472242529045815', '💰')} <b>Ціни:</b>\n"
    
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        desc += f"├ {days_text}: {em('5890848474563352982', '💰')} {price}\n"
    
    desc += f"\n{em('5393330385096575682', '💳')} <b>Виберіть період:</b>"
    
    buttons = []
    for days in PRICES[cheat].keys():
        days_text = f"{days} дн." if days != "1" else "1 день"
        buttons.append([{"text": days_text, "callback_data": f"period_{cheat}_{days}", "icon_custom_emoji_id": "5393330385096575682"}])
    
    buttons.append([{"text": f"{em('5960671702059848143', '⬅️')} Назад", "callback_data": "buy_key", "icon_custom_emoji_id": "5960671702059848143"}])
    
    edit_message_caption(chat_id, message_id, desc, {"inline_keyboard": buttons})

def handle_select_period(chat_id, message_id, cheat, days):
    waiting[f"{chat_id}_product"] = cheat
    waiting[f"{chat_id}_days"] = days
    
    price = PRICES[cheat][days]
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n📅 {days} дн.\n"
    desc += f"💰 {price}\n\n"
    desc += f"{em('5393576224729633040', '💳')} <b>Виберіть спосіб оплати:</b>"
    
    kb = {
        "inline_keyboard": [
            [{"text": f"{em('5393576224729633040', '🇺🇦')} Укр Банк", "callback_data": f"bank_{cheat}_{days}", "icon_custom_emoji_id": "5393576224729633040"}],
            [{"text": f"{em('5960671702059848143', '⬅️')} Назад", "callback_data": f"cheat_{cheat}", "icon_custom_emoji_id": "5960671702059848143"}]
        ]
    }
    edit_message_caption(chat_id, message_id, desc, kb)

def handle_bank_payment(chat_id, message_id, cheat, days):
    waiting[f"{chat_id}_product"] = cheat
    waiting[f"{chat_id}_days"] = days
    
    price = PRICES[cheat][days]
    
    text = (f"{em('5890848474563352982', '💳')} <b>Оплата банківською карткою</b>\n\n"
            f"{em('5890848474563352982', '💰')} <b>Сума:</b> {price}\n"
            f"{em('5890848474563352982', '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
            f"{em('5891105528356018797', '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em('5769126056262898415', '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    
    kb = {
        "inline_keyboard": [
            [{"text": f"{em('5258205968025525531', '✅')} Я оплатив", "callback_data": "send_receipt", "icon_custom_emoji_id": "5258205968025525531"}],
            [{"text": f"{em('5208480322731137426', '❌')} Скасувати", "callback_data": "start", "icon_custom_emoji_id": "5208480322731137426"}]
        ]
    }
    edit_message_caption(chat_id, message_id, text, kb)

def handle_send_receipt(chat_id, message_id, user_id):
    waiting[f"{user_id}_waiting"] = "receipt"
    send_message(chat_id, f"{em('5769126056262898415', '📸')} <b>Надішліть скріншот чека</b> (одним фото)")

# --- АДМИН-КОМАНДЫ ---
def handle_ban(chat_id, text):
    args = text.split(maxsplit=1)
    if len(args) < 2:
        send_message(chat_id, "❌ /ban [id] [причина]")
        return
    parts = args[1].split(maxsplit=1)
    target_id = int(parts[0])
    reason = parts[1] if len(parts) > 1 else "Нарушение правил"
    
    cursor.execute('UPDATE users SET banned = 1, ban_reason = ? WHERE user_id = ?', (reason, target_id))
    conn.commit()
    
    try:
        send_message(target_id, f"⛔️ <b>Вы заблокированы</b>\nПричина: {reason}")
    except:
        pass
    send_message(chat_id, f"{em('6030563507299160824', '✅')} Пользователь {target_id} забанен")

def handle_unban(chat_id, text):
    args = text.split()
    if len(args) < 2:
        send_message(chat_id, "❌ /unban [id]")
        return
    target_id = int(args[1])
    cursor.execute('UPDATE users SET banned = 0, ban_reason = NULL WHERE user_id = ?', (target_id,))
    conn.commit()
    try:
        send_message(target_id, f"✅ <b>Вы разблокированы</b>")
    except:
        pass
    send_message(chat_id, f"{em('6028205772117118673', '✅')} Пользователь {target_id} разблокирован")

def handle_users(chat_id):
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    send_message(chat_id, 
        f"{em('5904630315946611415', '👥')} <b>Статистика користувачів:</b>\n\n"
        f"{em('5208846279714560254', '📊')} Всього: {total}\n"
        f"{em('5938252440926163756', '✅')} Активних: {active}\n"
        f"{em('5208480322731137426', '⛔')} Забанено: {banned}")

def handle_broadcast(chat_id, user_id):
    waiting[f"{user_id}_broadcast"] = "waiting"
    send_message(chat_id, f"{em('5208846279714560254', '📢')} <b>Надішліть повідомлення для розсилки</b>")

# --- ОБРАБОТКА АДМИН-РЕШЕНИЙ ---
def handle_admin_key(chat_id, user_id, key):
    target_id = waiting.get(f"admin_target", 0)
    if not target_id:
        return
    
    product = waiting.get(f"admin_{target_id}_product", "Unknown")
    days = int(waiting.get(f"admin_{target_id}_days", "0"))
    file_id = waiting.get(f"admin_{target_id}_file")
    file_text = waiting.get(f"admin_{target_id}_file_text")
    
    expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    product_name = CHEAT_NAMES.get(product, "Zroglik")
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, expiry_date, product_name, subscribed_at, banned, last_key) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?), 0, ?)
    ''', (target_id, expiry_date, product_name, target_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), key))
    conn.commit()
    
    text = (f"{em('5938252440926163756', '✅')} <b>Замовлення активовано!</b>\n\n"
            f"{em('5891211339170326418', '📅')} <b>Діє до:</b> {expiry_date}\n"
            f"{em('6048733173171359488', '🔑')} <b>Ключ:</b> <code>{key}</code>\n\n"
            f"{em('5413879192267805083', '💜')} Дякуємо за покупку в ZroglikShop!")
    
    try:
        if file_id:
            send_document(target_id, file_id, text)
        elif file_text:
            send_message(target_id, text + f"\n\n{em('6039348811363520645', '📝')} {file_text}")
        else:
            send_message(target_id, text)
        
        send_message(chat_id, f"{em('5208422125924275090', '✅')} Готово! Товар видано користувачу.")
    except Exception as e:
        send_message(chat_id, f"❌ Помилка при відправці: {e}")
    
    # Очищаем
    for k in list(waiting.keys()):
        if f"admin_{target_id}" in k or k == "admin_target":
            del waiting[k]

# --- ГЛАВНЫЙ ЦИКЛ ---
def main():
    logger.info("🚀 Запуск ZroglikShop Bot")
    logger.info(f"👑 Адмін ID: {ADMIN_ID}")
    
    offset = 0
    while True:
        try:
            updates = get_updates(offset, timeout=30)
            if updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    
                    if 'callback_query' in update:
                        cb = update['callback_query']
                        cb_id = cb['id']
                        user_id = cb['from']['id']
                        username = cb['from'].get('username')
                        first_name = cb['from'].get('first_name')
                        chat_id = cb['message']['chat']['id']
                        message_id = cb['message']['message_id']
                        data = cb['data']
                        
                        if data == "start":
                            handle_start(chat_id, user_id, username, first_name)
                        elif data == "check_sub":
                            handle_check_subscription(chat_id, user_id, message_id)
                        elif data == "profile":
                            handle_profile(chat_id, user_id, message_id, username, first_name)
                        elif data == "show_reviews":
                            handle_reviews(chat_id, message_id)
                        elif data == "buy_key":
                            handle_buy_key(chat_id, message_id)
                        elif data == "cheat_zolo":
                            show_cheat(chat_id, message_id, "zolo")
                        elif data == "cheat_impact":
                            show_cheat(chat_id, message_id, "impact")
                        elif data == "cheat_king":
                            show_cheat(chat_id, message_id, "king")
                        elif data == "cheat_inferno":
                            show_cheat(chat_id, message_id, "inferno")
                        elif data == "cheat_zolo_cis":
                            show_cheat(chat_id, message_id, "zolo_cis")
                        elif data.startswith("period_"):
                            parts = data.split("_")
                            handle_select_period(chat_id, message_id, parts[1], parts[2])
                        elif data.startswith("bank_"):
                            parts = data.split("_")
                            handle_bank_payment(chat_id, message_id, parts[1], parts[2])
                        elif data == "send_receipt":
                            handle_send_receipt(chat_id, message_id, user_id)
                        elif data.startswith("adm_ok_") or data.startswith("adm_no_"):
                            handle_admin_decision(chat_id, data, user_id)
                        answer_callback(cb_id)
                    
                    elif 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        user_id = msg['from']['id']
                        username = msg['from'].get('username')
                        first_name = msg['from'].get('first_name')
                        text = msg.get('text', '')
                        
                        if text == "/start":
                            handle_start(chat_id, user_id, username, first_name)
                        elif text.startswith("/ban") and user_id == ADMIN_ID:
                            handle_ban(chat_id, text)
                        elif text.startswith("/unban") and user_id == ADMIN_ID:
                            handle_unban(chat_id, text)
                        elif text == "/users" and user_id == ADMIN_ID:
                            handle_users(chat_id)
                        elif text == "/broadcast" and user_id == ADMIN_ID:
                            handle_broadcast(chat_id, user_id)
                        elif waiting.get(f"{user_id}_broadcast") == "waiting" and user_id == ADMIN_ID:
                            waiting[f"{user_id}_broadcast"] = None
                            users = cursor.execute('SELECT user_id FROM users WHERE banned = 0').fetchall()
                            if not users:
                                send_message(chat_id, "📭 Немає користувачів")
                            else:
                                sent = 0
                                for u in users:
                                    try:
                                        if 'text' in msg:
                                            send_message(u['user_id'], msg['text'])
                                        elif 'photo' in msg:
                                            send_photo(u['user_id'], msg['photo'][-1]['file_id'], msg.get('caption', ''))
                                        sent += 1
                                    except:
                                        pass
                                    time.sleep(0.05)
                                send_message(chat_id, f"{em('5938252440926163756', '✅')} Розсилка завершена!\nВідправлено: {sent}")
                        elif waiting.get(f"{user_id}_waiting") == "receipt" and 'photo' in msg:
                            waiting[f"{user_id}_waiting"] = None
                            product = waiting.get(f"{user_id}_product", "Unknown")
                            days = waiting.get(f"{user_id}_days", "0")
                            
                            adm_kb = {
                                "inline_keyboard": [
                                    [{"text": f"{em('5208657859499282838', '✅')} Одобрити", "callback_data": f"adm_ok_{user_id}", "icon_custom_emoji_id": "5208657859499282838"}],
                                    [{"text": f"{em('5208480322731137426', '❌')} Відхилити", "callback_data": f"adm_no_{user_id}", "icon_custom_emoji_id": "5208480322731137426"}]
                                ]
                            }
                            send_photo(
                                ADMIN_ID,
                                msg['photo'][-1]['file_id'],
                                f"{em('6039486778597970865', '🔔')} <b>Чек від {user_id}</b>\n"
                                f"{em('6041730074376410123', '📦')} Товар: {CHEAT_NAMES.get(product, 'Unknown')}\n"
                                f"{em('5891211339170326418', '⏳')} Тариф: {days} днів",
                                adm_kb
                            )
                            send_message(chat_id, f"{em('5938252440926163756', '✅')} Чек відправлено адміністратору!")
                        elif waiting.get(f"{user_id}_waiting") == "file" and user_id == ADMIN_ID:
                            handle_admin_file(chat_id, user_id, msg)
                        elif waiting.get(f"{user_id}_waiting") == "key" and user_id == ADMIN_ID:
                            handle_admin_key(chat_id, user_id, text)
                        elif text == "/cancel":
                            if waiting.get(f"{user_id}_waiting"):
                                waiting[f"{user_id}_waiting"] = None
                                send_message(chat_id, "✅ Операцію скасовано")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
