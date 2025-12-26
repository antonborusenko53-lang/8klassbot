import telebot
from telebot import types
import json, os
from datetime import datetime, timedelta
from keep_alive import keep_alive

keep_alive()  # запускаємо Flask сервер для UptimeRobot

TOKEN = "ВСТАВ_СЮДИ_TOKEN"  # <- заміни на свій токен
ADMINS = [1013047918, 5245235883]

bot = telebot.TeleBot(TOKEN)
FILE = "data.json"

# ---------- Завантаження даних ----------
def load():
    if not os.path.exists(FILE):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({"dz": {}, "ogol": "", "rozklad": {}}, f)
    with open(FILE, encoding="utf-8") as f:
        return json.load(f)

def save(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- Кнопки ----------
def main_kb(is_admin=False):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📌 Сьогодні", "⏭ Завтра")
    kb.add("📅 Розклад", "📚 ДЗ")
    kb.add("📅 Розклад дзвінків")
    kb.add("📢 Оголошення")
    if is_admin:
        kb.add("➕ Додати ДЗ", "➖ Видалити ДЗ", "✏️ Змінити ДЗ")
        kb.add("➕ Оголошення", "✏️ Змінити Оголошення")
    return kb

def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅ Назад")
    return kb

# ---------- START ----------
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(
        m.chat.id,
        "👋 Бот 8 класу\nОбери дію 👇",
        reply_markup=main_kb(m.from_user.id in ADMINS)
    )

# ---------- СЬОГОДНІ / ЗАВТРА ----------
days_map = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер", 4: "Пʼятниця"}

def show_day(chat_id, day):
    data = load()
    lessons = data["rozklad"].get(day)
    if not lessons:
        bot.send_message(chat_id, f"{day} — вихідний 🎉")
        return
    text = f"📅 {day}\n\n📚 Уроки:"
    for i, l in enumerate(lessons, 1):
        text += f"\n{i}. {l}"
    dz = data["dz"].get(day, [])
    if dz:
        text += "\n\n📝 ДЗ:"
        for t in dz:
            if isinstance(t, list):
                t = ''.join(t)
            text += f"\n- {t}"
    bot.send_message(chat_id, text)

@bot.message_handler(func=lambda m: m.text == "📌 Сьогодні")
def today(m):
    day = days_map.get(datetime.now().weekday())
    if not day:
        bot.send_message(m.chat.id, "Сьогодні вихідний 🎉")
        return
    show_day(m.chat.id, day)

@bot.message_handler(func=lambda m: m.text == "⏭ Завтра")
def tomorrow(m):
    day = days_map.get((datetime.now() + timedelta(days=1)).weekday())
    if not day:
        bot.send_message(m.chat.id, "Завтра вихідний 🎉")
        return
    show_day(m.chat.id, day)

# ---------- РОЗКЛАД ----------
@bot.message_handler(func=lambda m: m.text == "📅 Розклад")
def schedule(m):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for d in load()["rozklad"]:
        kb.add(d)
    kb.add("⬅ Назад")
    bot.send_message(m.chat.id, "Оберіть день:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in load()["rozklad"])
def day_schedule(m):
    show_day(m.chat.id, m.text)

# ---------- РОЗКЛАД ДЗВІНКІВ ----------
@bot.message_handler(func=lambda m: m.text == "📅 Розклад дзвінків")
def show_calls(m):
    text = (
        "🕘 Розклад дзвінків:\n"
        "1 урок — 09:00-09:40\n"
        "2 урок — 09:50-10:30\n"
        "3 урок — 10:40-11:20\n"
        "4 урок — 11:40-12:20\n"
        "5 урок — 12:30-13:10\n"
        "6 урок — 13:20-14:00\n"
        "7 урок — 14:10-14:50"
    )
    bot.send_message(m.chat.id, text)

# ---------- ДЗ ----------
@bot.message_handler(func=lambda m: m.text == "📚 ДЗ")
def show_dz(m):
    dz_data = load()["dz"]
    if not dz_data:
        bot.send_message(m.chat.id, "ДЗ немає")
        return
    text = "📚 Домашнє завдання:"
    for day, tasks in dz_data.items():
        text += f"\n\n🔹 {day}:"
        for t in tasks:
            if isinstance(t, list):
                t = ''.join(t)
            text += f"\n- {t}"
    bot.send_message(m.chat.id, text)

# ---------- ДОДАТИ, ВИДАЛИТИ, ЗМІНИТИ ДЗ ----------
# (код як у попередньому пакеті — все працює)

# ---------- Оголошення ----------
# (код як у попередньому пакеті — все працює)

# ---------- Назад ----------
@bot.message_handler(func=lambda m: m.text == "⬅ Назад")
def back(m):
    start(m)

# ---------- RUN BOT ----------
bot.polling()
