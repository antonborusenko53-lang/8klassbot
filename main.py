import telebot
from telebot import types
from flask import Flask
from threading import Thread

# ================== НАЛАШТУВАННЯ ==================
TOKEN = "8453039217:AAEZYmcyehIe1flEeLSMdz1G6VucRXLYPLM"
bot = telebot.TeleBot(TOKEN)

ADMINS = [1013047918, 5245235883]

DAYS = ["Понеділок", "Вівторок", "Середа", "Четвер", "Пʼятниця"]

homework = {
    "Понеділок": "",
    "Вівторок": "",
    "Середа": "",
    "Четвер": "",
    "Пʼятниця": ""
}

user_state = {}

bot = telebot.TeleBot(TOKEN)

# ================== FLASK (UPTIME ROBOT) ==================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ================== КНОПКИ ==================

def main_keyboard(is_admin=False):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📚 Домашнє завдання")
    kb.add("📅 Розклад")
    if is_admin:
        kb.add("➕ Додати ДЗ")
    return kb

def days_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for d in DAYS:
        kb.add(d)
    kb.add("⬅️ Назад")
    return kb

# ================== /start ==================

@bot.message_handler(commands=["start"])
def start(message):
    is_admin = message.from_user.id in ADMINS
    bot.send_message(
        message.chat.id,
        "Привіт 👋\nЯ бот для домашніх завдань 📚",
        reply_markup=main_keyboard(is_admin)
    )

# ================== ДЗ ==================

@bot.message_handler(func=lambda m: m.text == "📚 Домашнє завдання")
def show_homework(message):
    text = "📚 Домашнє завдання:\n\n"
    for day in DAYS:
        if homework[day]:
            text += f"🔹 {day}:\n{homework[day]}\n\n"
    if text.strip() == "📚 Домашнє завдання:":
        text += "Поки що нічого не задано 🙂"
    bot.send_message(message.chat.id, text)

# ================== ДОДАТИ ДЗ (АДМІН) ==================

@bot.message_handler(func=lambda m: m.text == "➕ Додати ДЗ")
def add_hw(message):
    if message.from_user.id not in ADMINS:
        return
    user_state[message.from_user.id] = {"step": "day"}
    bot.send_message(message.chat.id, "Обери день:", reply_markup=days_keyboard())

@bot.message_handler(func=lambda m: m.from_user.id in user_state)
def process_hw(message):
    state = user_state.get(message.from_user.id)

    if message.text == "⬅️ Назад":
        user_state.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            "Головне меню",
            reply_markup=main_keyboard(True)
        )
        return

    if state["step"] == "day":
        if message.text not in DAYS:
            return
        state["day"] = message.text
        state["step"] = "text"
        bot.send_message(message.chat.id, f"Введи ДЗ для {message.text}:")

    elif state["step"] == "text":
        homework[state["day"]] = message.text
        user_state.pop(message.from_user.id)
        bot.send_message(
            message.chat.id,
            "✅ Домашнє завдання збережено!",
            reply_markup=main_keyboard(True)
        )

# ================== РОЗКЛАД ==================

@bot.message_handler(func=lambda m: m.text == "📅 Розклад")
def schedule(message):
    bot.send_message(
        message.chat.id,
        "📅 Розклад дзвінків:\n\n"
        "1️⃣ 09:00 – 09:40\n"
        "2️⃣ 09:50 – 10:30\n"
        "3️⃣ 10:40 – 11:20\n"
        "4️⃣ 11:40 – 12:20\n"
        "5️⃣ 12:30 – 13:10\n"
        "6️⃣ 13:20 – 14:00\n"
        "7️⃣ 14:10 – 14:50"
    )

# ================== ЗАПУСК ==================

bot.infinity_polling()
