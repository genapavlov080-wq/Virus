import urllib.request
import json
import time
import sqlite3
import logging
import requests
import traceback
from datetime import datetime, timedelta

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8655981898:AAE6-Ija80rwYN0FQoXIfcuAsNsUosAl_z0"
ADMIN_ID = 1471307057
CARD = "5167803275649049"
CARD_SBER = "2202206340487136"
CARD_SBER_NAME = "Вазген Б."
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- ДИАГНОСТИКА ТОКЕНА ---
print("🔍 Проверка токена...")
try:
    test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = urllib.request.urlopen(test_url, timeout=10)
    data = json.loads(response.read().decode())
    if data.get('ok'):
        bot_username = data['result']['username']
        print(f"✅ Токен работает! Бот: @{bot_username}")
    else:
        print(f"❌ Ошибка API: {data}")
        exit(1)
except Exception as e:
    print(f"❌ Токен недействителен: {e}")
    print("Проверьте токен в @BotFather. Команда: /mybots")
    exit(1)

# CryptoBot API
CRYPTO_TOKEN = "466345:AADMm3mzlC6KGJmwt3r771bUPIx40CMEKhQ"
CRYPTO_API = "https://pay.crypt.bot/api"

# ОДИН КАНАЛ для обязательной подписки
REQUIRED_CHANNELS = [
    {"id": -1002544275396, "url": "https://t.me/+P2DK2IpHKBdiZGUy", "name": "ZroglikCheat_rezelvv"}
]

REVIEWS_CHANNEL_URL = "https://t.me/zroglikrotzivv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- СБРОС ВЕБХУКА ---
try:
    urllib.request.urlopen(f"{API_URL}/deleteWebhook?drop_pending_updates=true", timeout=10)
    print("✅ Webhook удален")
except Exception as e:
    print(f"Ошибка удаления webhook: {e}")

try:
    urllib.request.urlopen(f"{API_URL}/getUpdates?offset=-1", timeout=10)
    print("✅ Очередь очищена")
except Exception as e:
    print(f"Ошибка очистки: {e}")

time.sleep(1)

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

# --- ФУНКЦИИ API ---
def api(method, data=None, timeout=30):
    url = f"{API_URL}/{method}"
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
        else:
            req = urllib.request.Request(url, method='GET')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        logger.error(f"API error: {e}")
        return {'ok': False}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return api("sendMessage", data)

def send_photo(chat_id, photo, caption=None, reply_markup=None):
    data = {"chat_id": chat_id, "photo": photo, "parse_mode": "HTML"}
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = reply_markup
    return api("sendPhoto", data)

def send_document(chat_id, document, caption=None):
    data = {"chat_id": chat_id, "document": document, "parse_mode": "HTML"}
    if caption:
        data["caption"] = caption
    return api("sendDocument", data)

def edit_message_caption(chat_id, message_id, caption, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    return api("editMessageCaption", data)

def get_updates(offset=None, timeout=30):
    data = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
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

# --- ФУНКЦИЯ ДЛЯ ЭМОДЗИ В ТЕКСТЕ ---
def em(emoji_id, char):
    return f'<tg-emoji emoji-id="{emoji_id}">{char}</tg-emoji>'

# --- REPLY КЛАВИАТУРА С TELEGRAM PREMIUM ЭМОДЗИ ---
def get_main_reply_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "📦",
                            "custom_emoji_id": "5156877291397055163"
                        },
                        {
                            "type": "text",
                            "text": " Каталог"
                        }
                    ]
                }
            ],
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "👤",
                            "custom_emoji_id": "5904630315946611415"
                        },
                        {
                            "type": "text",
                            "text": " Мій кабінет"
                        }
                    ]
                }
            ],
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "⭐",
                            "custom_emoji_id": "5938252440926163756"
                        },
                        {
                            "type": "text",
                            "text": " Відгуки"
                        }
                    ]
                },
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "🎮",
                            "custom_emoji_id": "5208539876747662991"
                        },
                        {
                            "type": "text",
                            "text": " Техпідтримка"
                        }
                    ]
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_back_reply_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "◀️",
                            "custom_emoji_id": "5960671702059848143"
                        },
                        {
                            "type": "text",
                            "text": " Назад"
                        }
                    ]
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_cheats_reply_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "🔥",
                            "custom_emoji_id": "5451653043089070124"
                        },
                        {
                            "type": "text",
                            "text": " Zolo"
                        }
                    ]
                },
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "⚡",
                            "custom_emoji_id": "5276079251089547977"
                        },
                        {
                            "type": "text",
                            "text": " Impact VIP"
                        }
                    ]
                }
            ],
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "👑",
                            "custom_emoji_id": "6172520285330214110"
                        },
                        {
                            "type": "text",
                            "text": " King Mod"
                        }
                    ]
                },
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "💥",
                            "custom_emoji_id": "5296273418516187626"
                        },
                        {
                            "type": "text",
                            "text": " Inferno"
                        }
                    ]
                }
            ],
            [
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "🎮",
                            "custom_emoji_id": "5451841459009379088"
                        },
                        {
                            "type": "text",
                            "text": " Zolo CIS"
                        }
                    ]
                },
                {
                    "text": "",
                    "text_entities": [
                        {
                            "type": "custom_emoji",
                            "text": "◀️",
                            "custom_emoji_id": "5960671702059848143"
                        },
                        {
                            "type": "text",
                            "text": " Назад"
                        }
                    ]
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_period_reply_keyboard(cheat):
    PRICES = {
        "zolo": {"1": "85 грн", "3": "180 грн", "7": "325 грн", "14": "400 грн", "30": "690 грн", "60": "1000 грн"},
        "impact": {"1": "115 грн", "7": "480 грн", "30": "1170 грн"},
        "king": {"1": "100 грн", "7": "425 грн", "30": "1060 грн"},
        "inferno": {"1": "80 грн", "3": "200 грн", "7": "350 грн", "15": "530 грн", "30": "690 грн", "60": "950 грн"},
        "zolo_cis": {"1": "70 грн", "3": "150 грн", "7": "250 грн", "14": "350 грн", "30": "700 грн", "60": "900 грн"}
    }
    buttons = []
    row = []
    for i, days in enumerate(PRICES[cheat].keys()):
        days_text = f"{days} дн." if days != "1" else "1 день"
        button_text = f"{days_text} - {PRICES[cheat][days]}"
        row.append({"text": button_text})
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([{"text": "◀️ Назад"}])
    return {
        "keyboard": buttons,
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_payment_reply_keyboard(cheat, days):
    return {
        "keyboard": [
            [{"text": "🏦 Укр Банк"}],
            [{"text": "🏦 Сбербанк"}],
            [{"text": "💎 CryptoBot"}],
            [{"text": "◀️ Назад"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_receipt_reply_keyboard():
    return {
        "keyboard": [
            [{"text": "✅ Я оплатив"}],
            [{"text": "❌ Скасувати"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

def get_subscribe_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "ПОДПИСАТЬСЯ", "url": REQUIRED_CHANNELS[0]["url"], "icon_custom_emoji_id": "5927118708873892465"}],
            [{"text": "ПРОВЕРИТИ", "callback_data": "check_sub", "icon_custom_emoji_id": "5774022692642492953"}]
        ]
    }

def get_admin_decision_keyboard(user_id):
    return {
        "inline_keyboard": [
            [{"text": "Одобрити", "callback_data": f"adm_ok_{user_id}", "icon_custom_emoji_id": "5208657859499282838"}],
            [{"text": "Відхилити", "callback_data": f"adm_no_{user_id}", "icon_custom_emoji_id": "5208480322731137426"}]
        ]
    }

# --- ОСНОВНЫЕ ФОТО ---
MAIN_PHOTO = "https://files.catbox.moe/6n69h6.jpg"
PROFILE_PHOTO = "https://files.catbox.moe/kybf8l.png"

# --- ЦЕНЫ ---
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

# --- ХРАНИЛИЩА ---
waiting = {}
user_selection = {}

# --- ФУНКЦИИ CRYPTOBOT ---
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

# --- ПРОВЕРКА ПОДПИСКИ ---
def check_all_subscriptions(user_id):
    if user_id == ADMIN_ID:
        return True, None, None
    
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

# --- ОБРАБОТЧИКИ ---
def handle_start(chat_id, user_id, username, first_name):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Ви заблоковані")
        return
    
    subscribed, _, _ = check_all_subscriptions(user_id)
    if not subscribed:
        text = (f"{em('5208806229144524155', '🔒')} <b>Доступ обмежено!</b>\n\n"
                f"Для доступу до бота необхідно підписатися на канал:\n"
                f"📢 <b>{REQUIRED_CHANNELS[0]['name']}</b>\n\n"
                f"Після підписки натисніть кнопку «ПРОВЕРИТИ»")
        send_message(chat_id, text, get_subscribe_keyboard())
        return
    
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, subscribed_at) 
        VALUES (?, ?, ?, COALESCE((SELECT subscribed_at FROM users WHERE user_id = ?), ?))
    ''', (user_id, username, first_name, user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = (f"{em('5208806229144524155', '🔥')} <b>ZROGLIK KEYS</b>\n\n"
            f"{em('5208657859499282838', '👋')} Ласкаво просимо до ZroglikShop!\n"
            f"{em('6073605466221451561', '🎯')} Тут ти можеш купити чити для PUBG Mobile")
    
    send_photo(chat_id, MAIN_PHOTO, text, get_main_reply_keyboard())

def handle_check_subscription(chat_id, user_id, callback_id, message_id):
    subscribed, _, _ = check_all_subscriptions(user_id)
    if subscribed:
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, subscribed_at) 
            VALUES (?, ?)
        ''', (user_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        
        text = (f"{em('5208806229144524155', '🔥')} <b>ZROGLIK KEYS</b>\n\n"
                f"{em('5208657859499282838', '👋')} Ласкаво просимо до ZroglikShop!\n"
                f"{em('6073605466221451561', '🎯')} Тут ти можеш купити чити для PUBG Mobile")
        
        # Удаляем старое сообщение с клавиатурой подписки и отправляем новое
        try:
            api("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
        except:
            pass
        send_photo(chat_id, MAIN_PHOTO, text, get_main_reply_keyboard())
        answer_callback(callback_id, "✅ Підписка підтверджена!")
    else:
        answer_callback(callback_id, "❌ Ви ще не підписалися на канал!", True)

def handle_profile(chat_id, user_id, username, first_name):
    banned = cursor.execute('SELECT banned FROM users WHERE user_id = ?', (user_id,)).fetchone()
    if banned and banned['banned']:
        send_message(chat_id, "⛔ Ви заблоковані")
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
                product = user['product_name'] if user['product_name'] else "Немає"
                last_key = user['last_key'] if user['last_key'] else "Немає"
        except Exception as e:
            logger.error(f"Error parsing date: {e}")
            time_left = "Помилка формату"
            product = user['product_name'] if user['product_name'] else "Немає"
            last_key = user['last_key'] if user['last_key'] else "Немає"
    
    user_name = user['first_name'] if user and user['first_name'] else str(user_id)
    user_username = user['username'] if user and user['username'] else "Немає"
    
    text = (f"{em('5904630315946611415', '👤')} <b>МІЙ КАБІНЕТ</b>\n\n"
            f"{em('6032693626394382504', '🆔')} <b>ID:</b> <code>{user_id}</code>\n"
            f"{em('5879770735999717115', '📛')} <b>Ім'я:</b> {user_name}\n"
            f"{em('5814247475141153332', '🔖')} <b>Username:</b> @{user_username}\n"
            f"{em('6041730074376410123', '📦')} <b>Товар:</b> {product}\n"
            f"{em('5891211339170326418', '⏳')} <b>Залишилось:</b> {time_left}\n"
            f"{em('6048733173171359488', '🔑')} <b>Ваш ключ:</b> <code>{last_key}</code>\n"
            f"{em('5208474816583063829', '📅')} <b>Діє до:</b> {expiry_display}")
    
    send_message(chat_id, text, get_back_reply_keyboard())

def handle_catalog(chat_id):
    text = f"{em('6073605466221451561', '🎯')} <b>Виберіть чит:</b>"
    send_message(chat_id, text, get_cheats_reply_keyboard())

def handle_cheat_selection(chat_id, cheat_name):
    cheat_map = {
        "Zolo": "zolo",
        "Impact VIP": "impact",
        "King Mod": "king",
        "Inferno": "inferno",
        "Zolo CIS": "zolo_cis"
    }
    
    cheat = cheat_map.get(cheat_name)
    if not cheat:
        return
    
    user_selection[chat_id] = {"cheat": cheat}
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n"
    desc += f"{em('5208806229144524155', '💰')} <b>Ціни:</b>\n"
    
    for days, price in PRICES[cheat].items():
        days_text = f"{days} дн." if days != "1" else "1 день"
        desc += f"├ {days_text}: {em('5890848474563352982', '💰')} {price}\n"
    
    desc += f"\n{em('5393330385096575682', '💳')} <b>Виберіть період:</b>"
    
    send_message(chat_id, desc, get_period_reply_keyboard(cheat))

def handle_period_selection(chat_id, period_text):
    if chat_id not in user_selection:
        return
    
    cheat = user_selection[chat_id]["cheat"]
    
    # Парсим период из текста (например "1 дн. - 85 грн")
    days = period_text.split(" ")[0]
    
    if days not in PRICES[cheat]:
        return
    
    user_selection[chat_id]["days"] = days
    price = PRICES[cheat][days]
    
    desc = f"{CHEAT_NAMES[cheat]}\n\n"
    desc += f"{em('5413879192267805083', '📅')} {days} дн.\n"
    desc += f"{em('5208954744818651087', '💰')} {price}\n\n"
    desc += f"{em('5393576224729633040', '💳')} <b>Виберіть спосіб оплати:</b>"
    
    send_message(chat_id, desc, get_payment_reply_keyboard(cheat, days))

def handle_bank_payment(chat_id, cheat, days):
    price = PRICES[cheat][days]
    
    text = (f"{em('5890848474563352982', '💳')} <b>Оплата банківською карткою</b>\n\n"
            f"{em('5890848474563352982', '💰')} <b>Сума:</b> {price}\n"
            f"{em('5890848474563352982', '💳')} <b>Карта:</b> <code>{CARD}</code>\n"
            f"{em('5891105528356018797', '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em('5769126056262898415', '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    
    send_message(chat_id, text, get_receipt_reply_keyboard())

def handle_bank_payment_sber(chat_id, cheat, days):
    price = PRICES[cheat][days]
    
    text = (f"{em('5247180323120225302', '🏦')} <b>Оплата Сбербанк</b>\n\n"
            f"{em('5890848474563352982', '💰')} <b>Сума:</b> {price}\n"
            f"{em('5890848474563352982', '💳')} <b>Карта:</b> <code>{CARD_SBER}</code>\n"
            f"{em('5879770735999717115', '👤')} <b>Отримувач:</b> {CARD_SBER_NAME}\n"
            f"{em('5891105528356018797', '❗')} <b>Коментар:</b> За цифрові товари\n\n"
            f"{em('5769126056262898415', '📸')} Після оплати натисніть кнопку нижче і надішліть скріншот")
    
    send_message(chat_id, text, get_receipt_reply_keyboard())

def handle_crypto_payment(chat_id, cheat, days, user_id):
    price_str = PRICES[cheat][days].replace(" грн", "")
    amount = round(int(price_str) / 43, 2)
    
    invoice = create_crypto_invoice(user_id, amount, days, cheat)
    if not invoice:
        send_message(chat_id, "❌ Ошибка создания платежа", get_back_reply_keyboard())
        return
    
    cursor.execute('''
        INSERT INTO crypto_payments (payment_id, user_id, amount, days, product, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (str(invoice["invoice_id"]), user_id, amount, days, cheat, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    
    text = (f"{em('5208954744818651087', '💎')} <b>Оплата через CryptoBot</b>\n\n"
            f"{em('5890848474563352982', '💰')} <b>Сума:</b> {amount}$\n"
            f"{em('5413879192267805083', '📅')} <b>Тариф:</b> {days} дней\n\n"
            f"{em('5208480322731137426', '🔗')} <b>Посилання для оплати:</b>\n{invoice['pay_url']}\n\n"
            f"Після оплати натисніть кнопку «Проверить оплату» нижче")
    
    kb = {
        "inline_keyboard": [
            [{"text": "💎 Проверить оплату", "callback_data": f"check_crypto_{invoice['invoice_id']}", "icon_custom_emoji_id": "6039486778597970865"}],
            [{"text": "◀️ Назад", "callback_data": "back_to_menu", "icon_custom_emoji_id": "5960671702059848143"}]
        ]
    }
    send_message(chat_id, text, kb)

def handle_check_crypto(chat_id, message_id, payment_id, user_id):
    payment = check_crypto_payment(payment_id)
    
    if payment and payment.get("status") == "paid":
        res = cursor.execute('SELECT product, days FROM crypto_payments WHERE payment_id = ?', (str(payment_id),)).fetchone()
        if res:
            product, days = res
            expiry = (datetime.now() + timedelta(days=int(days))).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('UPDATE users SET expiry_date = ?, product_name = ? WHERE user_id = ?', (expiry, CHEAT_NAMES[product], user_id))
            cursor.execute('UPDATE crypto_payments SET status = "paid" WHERE payment_id = ?', (str(payment_id),))
            conn.commit()
            send_message(chat_id, 
                f"{em('5938252440926163756', '✅')} <b>Оплата подтверждена!</b>\n\n{em('5413879192267805083', '📅')} Подписка до {expiry}",
                get_main_reply_keyboard())
            send_message(ADMIN_ID, f"{em('6039486778597970865', '💰')} <b>Новый крипто-платёж</b>\n👤 {user_id}\n📅 {days} дней\n💎 {CHEAT_NAMES[product]}")
    else:
        answer_callback(message_id, "⏳ Платёж ещё не подтверждён", True)

def handle_send_receipt(chat_id, user_id):
    waiting[f"{user_id}_waiting"] = "receipt"
    send_message(chat_id, f"{em('5769126056262898415', '📸')} <b>Надішліть скріншот чека</b> (одним фото)")

def handle_reviews(chat_id):
    text = f"{em('5938252440926163756', '⭐')} <b>Наші відгуки</b>\n\nКанал з відгуками: {REVIEWS_CHANNEL_URL}"
    send_message(chat_id, text, get_back_reply_keyboard())

def handle_support(chat_id):
    text = f"{em('5208539876747662991', '🎮')} <b>Технічна підтримка</b>\n\nЗв'яжіться з нами: @ZrogIikCheat"
    send_message(chat_id, text, get_back_reply_keyboard())

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
    send_message(chat_id, f"✅ Пользователь {target_id} забанен")

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
    send_message(chat_id, f"✅ Пользователь {target_id} разблокирован")

def handle_users(chat_id):
    total = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    banned = cursor.execute('SELECT COUNT(*) FROM users WHERE banned = 1').fetchone()[0]
    active = cursor.execute('SELECT COUNT(*) FROM users WHERE expiry_date > ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).fetchone()[0]
    send_message(chat_id, 
        f"👥 <b>Статистика користувачів:</b>\n\n"
        f"📊 Всього: {total}\n"
        f"✅ Активних: {active}\n"
        f"⛔ Забанено: {banned}")

def handle_broadcast(chat_id, user_id):
    waiting[f"{user_id}_broadcast"] = "waiting"
    send_message(chat_id, f"📢 <b>Надішліть повідомлення для розсилки</b>")

# --- ОБРАБОТКА АДМИН-РЕШЕНИЙ ---
def handle_admin_decision(chat_id, data, user_id):
    parts = data.split("_")
    if parts[1] == "ok":
        target_id = int(parts[2])
        product = waiting.get(f"{target_id}_product", "Unknown")
        days = waiting.get(f"{target_id}_days", "0")
        
        waiting[f"admin_{user_id}_target"] = target_id
        waiting[f"admin_{user_id}_product"] = product
        waiting[f"admin_{user_id}_days"] = days
        waiting[f"admin_{user_id}_state"] = "waiting_file"
        
        send_message(chat_id, f"📎 <b>Надішліть файл з читом</b> (або текст з інструкцією)")
    else:
        target_id = int(parts[2])
        try:
            send_message(target_id, f"❌ Ваша оплата була відхилена адміністратором.")
        except:
            pass
        send_message(chat_id, f"❌ Відхилено")
        if waiting.get(f"{target_id}_product"):
            del waiting[f"{target_id}_product"]
        if waiting.get(f"{target_id}_days"):
            del waiting[f"{target_id}_days"]

def handle_admin_file(chat_id, user_id, msg):
    state = waiting.get(f"admin_{user_id}_state")
    if state != "waiting_file":
        return
    
    target_id = waiting.get(f"admin_{user_id}_target")
    if not target_id:
        send_message(chat_id, "❌ Ошибка: не найден пользователь")
        waiting[f"admin_{user_id}_state"] = None
        return
    
    file_id = None
    file_text = None
    
    if 'document' in msg:
        file_id = msg['document']['file_id']
    elif 'photo' in msg:
        file_id = msg['photo'][-1]['file_id']
    else:
        file_text = msg.get('text', '')
    
    waiting[f"admin_{user_id}_file"] = file_id
    waiting[f"admin_{user_id}_file_text"] = file_text
    waiting[f"admin_{user_id}_state"] = "waiting_key"
    
    send_message(chat_id, f"🔑 <b>Введіть ключ активації</b>")

def handle_admin_key(chat_id, user_id, key):
    state = waiting.get(f"admin_{user_id}_state")
    if state != "waiting_key":
        return
    
    target_id = waiting.get(f"admin_{user_id}_target")
    if not target_id:
        send_message(chat_id, "❌ Ошибка: не найден пользователь")
        waiting[f"admin_{user_id}_state"] = None
        return
    
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
    
    user_text = (f"{em('5938252440926163756', '✅')} <b>Замовлення активовано!</b>\n\n"
                 f"{em('5208474816583063829', '📅')} <b>Діє до:</b> {expiry_display}\n"
                 f"{em('6048733173171359488', '🔑')} <b>Ключ:</b> <code>{key}</code>\n\n"
                 f"{em('5413879192267805083', '💜')} Дякуємо за покупку в ZroglikShop!\n\n"
                 f"{em('6039348811363520645', '📝')} <b>Інструкція:</b>\n"
                 f"1. Скачайте чит за посиланням вище\n"
                 f"2. Вставте ключ {key}\n"
                 f"3. Насолоджуйтесь грою! 🎮")
    
    admin_text = (f"✅ <b>Ключ видано!</b>\n"
                  f"👤 Користувач: {target_id}\n"
                  f"📦 Товар: {product_name}\n"
                  f"📅 {days} дн. до {expiry_display}\n"
                  f"🔑 Ключ: <code>{key}</code>")
    
    try:
        if file_id:
            send_document(target_id, file_id, user_text)
        elif file_text:
            send_message(target_id, user_text + f"\n\n📝 {file_text}")
        else:
            send_message(target_id, user_text)
        
        send_message(chat_id, admin_text)
        
    except Exception as e:
        send_message(chat_id, f"❌ Помилка: {e}")
    
    for k in list(waiting.keys()):
        if k.startswith(f"admin_{user_id}_"):
            del waiting[k]
    
    if waiting.get(f"{target_id}_product"):
        del waiting[f"{target_id}_product"]
    if waiting.get(f"{target_id}_days"):
        del waiting[f"{target_id}_days"]
    if waiting.get(f"{target_id}_waiting"):
        del waiting[f"{target_id}_waiting"]

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
                        chat_id = cb['message']['chat']['id']
                        message_id = cb['message']['message_id']
                        data = cb['data']
                        
                        try:
                            if data == "check_sub":
                                handle_check_subscription(chat_id, user_id, cb_id, message_id)
                            elif data.startswith("check_crypto_"):
                                payment_id = int(data.replace("check_crypto_", ""))
                                handle_check_crypto(chat_id, message_id, payment_id, user_id)
                            elif data == "back_to_menu":
                                handle_start(chat_id, user_id, None, None)
                            elif data.startswith("adm_ok_") or data.startswith("adm_no_"):
                                handle_admin_decision(chat_id, data, user_id)
                            
                            answer_callback(cb_id)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                            logger.error(traceback.format_exc())
                            answer_callback(cb_id, f"❌ Ошибка: {str(e)[:50]}")
                    
                    elif 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        user_id = msg['from']['id']
                        username = msg['from'].get('username')
                        first_name = msg['from'].get('first_name')
                        text = msg.get('text', '')
                        
                        try:
                            if text == "/start":
                                handle_start(chat_id, user_id, username, first_name)
                            elif text == "Каталог":
                                handle_catalog(chat_id)
                            elif text == "Мій кабінет":
                                handle_profile(chat_id, user_id, username, first_name)
                            elif text == "Відгуки":
                                handle_reviews(chat_id)
                            elif text == "Техпідтримка":
                                handle_support(chat_id)
                            elif text == "◀️ Назад":
                                handle_start(chat_id, user_id, username, first_name)
                            elif text in ["Zolo", "Impact VIP", "King Mod", "Inferno", "Zolo CIS"]:
                                handle_cheat_selection(chat_id, text)
                            elif text.endswith("грн") and ("дн." in text or "день" in text):
                                handle_period_selection(chat_id, text)
                            elif text == "🏦 Укр Банк":
                                if chat_id in user_selection:
                                    handle_bank_payment(chat_id, user_selection[chat_id]["cheat"], user_selection[chat_id]["days"])
                            elif text == "🏦 Сбербанк":
                                if chat_id in user_selection:
                                    handle_bank_payment_sber(chat_id, user_selection[chat_id]["cheat"], user_selection[chat_id]["days"])
                            elif text == "💎 CryptoBot":
                                if chat_id in user_selection:
                                    handle_crypto_payment(chat_id, user_selection[chat_id]["cheat"], user_selection[chat_id]["days"], user_id)
                            elif text == "✅ Я оплатив":
                                handle_send_receipt(chat_id, user_id)
                            elif text == "❌ Скасувати":
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
                                    send_message(chat_id, f"✅ Розсилка завершена!\nВідправлено: {sent}")
                            elif waiting.get(f"{user_id}_waiting") == "receipt" and 'photo' in msg:
                                waiting[f"{user_id}_waiting"] = None
                                product = user_selection.get(chat_id, {}).get("cheat", "Unknown")
                                days = user_selection.get(chat_id, {}).get("days", "0")
                                
                                waiting[f"{user_id}_product"] = product
                                waiting[f"{user_id}_days"] = days
                                
                                send_photo(
                                    ADMIN_ID,
                                    msg['photo'][-1]['file_id'],
                                    f"🔔 <b>Чек від {user_id}</b>\n"
                                    f"📦 Товар: {product}\n"
                                    f"⏳ Тариф: {days} днів",
                                    get_admin_decision_keyboard(user_id)
                                )
                                send_message(chat_id, f"✅ Чек відправлено адміністратору! Очікуйте підтвердження.")
                            elif waiting.get(f"admin_{user_id}_state") == "waiting_file" and user_id == ADMIN_ID:
                                handle_admin_file(chat_id, user_id, msg)
                            elif waiting.get(f"admin_{user_id}_state") == "waiting_key" and user_id == ADMIN_ID:
                                handle_admin_key(chat_id, user_id, text)
                            elif text == "/cancel":
                                if waiting.get(f"{user_id}_waiting"):
                                    waiting[f"{user_id}_waiting"] = None
                                    send_message(chat_id, "✅ Операцію скасовано")
                                if waiting.get(f"admin_{user_id}_state"):
                                    for k in list(waiting.keys()):
                                        if k.startswith(f"admin_{user_id}_"):
                                            del waiting[k]
                                    send_message(chat_id, "✅ Операцію скасовано")
                        except Exception as e:
                            logger.error(f"Message error: {e}")
                            logger.error(traceback.format_exc())
                            send_message(chat_id, f"❌ Ошибка: {str(e)[:50]}")
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            logger.error(traceback.format_exc())
            time.sleep(5)

if __name__ == "__main__":
    main()
