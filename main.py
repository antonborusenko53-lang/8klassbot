import telebot
from telebot import types
from flask import Flask
from threading import Thread
import json
import os
import requests
import sys
from json import JSONDecodeError

# ================== НАЛАШТУВАННЯ ==================

# Читати токен із змінної оточення. НЕ зберігайте токен у коді.
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("8435790914:AAHOV7cyt-HIG3kEJk-7gE1zT31XvqKYgfk")
if not TOKEN:
    raise ValueError("TOKEN not found. Set TELEGRAM_TOKEN environment variable.")

ADMINS = [1013047918, 5245235883]

DAYS = ["Понеділок", "Вівторок", "Середа", "Четвер", "Пʼятниця"]

LESSON_TIMES = (
    "1️⃣ 09:00 – 09:40\n"
    "2️⃣ 09:50 – 10:30\n"
    "3️⃣ 10:40 – 11:20\n"
    "4️⃣ 11:40 – 12:20\n"
    "5️⃣ 12:30 – 13:10\n"
    "6️⃣ 13:20 – 14:00\n"
    "7️⃣ 14:10 – 14:50"
)

SCHEDULE = {
    "Понеділок": ["Укр. мова", "Алгебра", "Англ. мова"],
    "Вівторок": ["Історія", "Географія"],
    "Середа": ["Біологія", "Фізика"],
    "Четвер": ["Хімія", "Англ. мова"],
    "Пʼятниця": ["Алгебра", "Інформатика"]
}

# Краще використовувати абсолютний шлях відносно файлу
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# ================== ДАНІ ==================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"homework": {d: [] for d in DAYS}, "announcements": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (IOError, JSONDecodeError) as e:
        print("Error loading data.json:", e, file=sys.stderr)
        # Якщо файл пошкоджений, повертаємо чисту структуру
        return {"homework": {d: [] for d in DAYS}, "announcements": []}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print("Error saving data.json:", e, file=sys.stderr)

data = load_data()
state = {}

# ================== BOT ==================

bot = telebot.TeleBot(TOKEN)

# Спробуємо видалити webhook без падіння програми при помилці
try:
    # Використовуємо HTTP-запит до Telegram API як раніше, або можна використати метод бібліотеки
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
except Exception as e:
    print("Failed to delete webhook (ignored):", e, file=sys.stderr)

# ================== FLASK ==================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Порт можна брати із змінної оточення, за замовчуванням 10000
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run, daemon=True).start()

# ================== КНОПКИ ==================

def main_kb(is_admin=False):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Домашнє завдання", "📅 Розклад уроків")
    kb.add("⏰ Дзвінки", "📢 Оголошення")
    if is_admin:
        kb.add("➕ Додати ДЗ", "➕ Оголошення")
        kb.add("❌ Очистити ДЗ")
    return kb

def days_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for d in DAYS:
        kb.add(d)
    kb.add("⬅️ Назад")
    return kb

# ================== START ==================

@bot.message_handler(commands=["start"])
def start(message):
    is_admin = message.from_user and message.from_user.id in ADMINS
    bot.send_message(
        message.chat.id,
        "👋 Вітаю! Це PRO-бот класу 📘",
        reply_markup=main_kb(is_admin)
    )

# ================== ДЗ ==================

@bot.message_handler(func=lambda m: m.text == "📚 Домашнє завдання")
def show_hw(message):
    text = "📚 Домашнє завдання:\n\n"
    for d in DAYS:
        if data["homework"].get(d):
            text += f"🔹 {d}:\n"
            for hw in data["homework"][d]:
                text += f"• {hw}\n"
            text += "\n"
    if text.strip() == "📚 Домашнє завдання:":
        text += "Поки що немає 🙂"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "➕ Додати ДЗ" and m.from_user and m.from_user.id in ADMINS)
def add_hw(message):
    state[message.from_user.id] = {"step": "day"}
    bot.send_message(message.chat.id, "Обери день:", reply_markup=days_kb())

@bot.message_handler(func=lambda m: m.from_user and m.from_user.id in state)
def hw_steps(message):
    user_id = message.from_user.id
    st = state.get(user_id)
    if not st:
        return

    if message.text == "⬅️ Назад":
        state.pop(user_id, None)
        bot.send_message(message.chat.id, "Меню", reply_markup=main_kb(user_id in ADMINS))
        return

    if st["step"] == "day":
        if message.text not in DAYS:
            # Ігноруємо невірні відповіді або можна повідомити про помилку
            bot.send_message(message.chat.id, "Оберіть, будь ласка, день із клавіатури.", reply_markup=days_kb())
            return
        st["day"] = message.text
        st["step"] = "text"
        bot.send_message(message.chat.id, "Введи ДЗ:")

    elif st["step"] == "text":
        text = message.text or ""
        data["homework"].setdefault(st["day"], []).append(text)
        save_data()
        state.pop(user_id, None)
        bot.send_message(message.chat.id, "✅ ДЗ додано!", reply_markup=main_kb(user_id in ADMINS))

@bot.message_handler(func=lambda m: m.text == "❌ Очистити ДЗ" and m.from_user and m.from_user.id in ADMINS)
def clear_hw(message):
    data["homework"] = {d: [] for d in DAYS}
    save_data()
    bot.send_message(message.chat.id, "🧹 Усі ДЗ очищено", reply_markup=main_kb(message.from_user.id in ADMINS))

# ================== РОЗКЛАД ==================

@bot.message_handler(func=lambda m: m.text == "📅 Розклад уроків")
def lessons(message):
    text = "📅 Розклад уроків:\n\n"
    for d, lessons in SCHEDULE.items():
        text += f"🔹 {d}:\n"
        for i, l in enumerate(lessons, 1):
            text += f"{i}️⃣ {l}\n"
        text += "\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "⏰ Дзвінки")
def bells(message):
    bot.send_message(message.chat.id, f"⏰ Дзвінки:\n\n{LESSON_TIMES}")

# ================== ОГОЛОШЕННЯ ==================

@bot.message_handler(func=lambda m: m.text == "📢 Оголошення")
def show_ann(message):
    if not data.get("announcements"):
        bot.send_message(message.chat.id, "📢 Поки немає оголошень")
        return
    text = "📢 Оголошення:\n\n"
    for a in data["announcements"]:
        text += f"• {a}\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "➕ Оголошення" and m.from_user and m.from_user.id in ADMINS)
def add_ann(message):
    state[message.from_user.id] = {"step": "ann"}
    bot.send_message(message.chat.id, "Введи оголошення:")

@bot.message_handler(func=lambda m: m.from_user and m.from_user.id in state and state[m.from_user.id].get("step") == "ann")
def save_ann(message):
    text = message.text or ""
    data.setdefault("announcements", []).append(text)
    save_data()
    state.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "📢 Оголошення додано", reply_markup=main_kb(message.from_user.id in ADMINS))

# ================== RUN ==================

# infinity_polling зазвичай достатній для простого бота
bot.infinity_polling()
