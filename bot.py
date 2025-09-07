import os
import time
import json
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telebot
from telebot import types

from telebot.types import BotCommand



# =================== НАСТРОЙКИ ===================
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
MOM_ID = os.getenv("MOM_ID")  # айди мамы берём из .env
DAR_ID = os.getenv("MOM_ID")  # айди мамы берём из .env
AL_ID = os.getenv("MOM_ID")  # айди мамы берём из .env

bot = telebot.TeleBot(TOKEN)

# Дети
user_to_child = {
    DAR_ID: "Дарина",
    AL_ID: "Алиман",
}

# Длительность уроков
lesson_duration = {
    "default": 45,
    "Алиман": 75
}

# Загружаем расписание
with open("schedule.json", "r", encoding="utf-8") as f:
    schedule = json.load(f)


# =================== ВСПОМОГАТЕЛЬНЫЕ ===================
def get_schedule_text(child_name, day):
    """Возвращает текст расписания ребёнка на выбранный день"""
    if day not in schedule[child_name] or not schedule[child_name][day]:
        return f"В этот день у {child_name} занятий нет 😎"

    classes = [f"Расписание {child_name} на день {day}:"]
    for time, subject in schedule[child_name][day].items():
        classes.append(f"{subject} в {time}")
    return "\n".join(classes)


def get_latest_end(day):
    """Возвращает самое позднее окончание занятий всех детей на выбранный день"""
    latest_end_time = None
    children_today = []

    for child_name, days in schedule.items():
        if day in days and days[day]:
            children_today.append(child_name)
            for start_time_str in days[day].keys():
                start_time = datetime.strptime(start_time_str, "%H:%M")
                duration = lesson_duration.get(child_name, lesson_duration["default"])
                end_time = start_time + timedelta(minutes=duration)
                if not latest_end_time or end_time > latest_end_time:
                    latest_end_time = end_time

    return latest_end_time, children_today


def days_keyboard(prefix, child_name=None):
    """Клавиатура с выбором дня недели"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    for i in range(7):
        callback = f"{prefix}_{i}" if not child_name else f"{prefix}_{child_name}_{i}"
        markup.add(types.InlineKeyboardButton(text=str(i), callback_data=callback))
    return markup


# =================== НАПОМИНАНИЯ ===================
def send_reminder(child_name, subject, lesson_time):
    """Шлём ребёнку напоминание за 5 минут"""
    for user_id, name in user_to_child.items():
        if name == child_name:
            bot.send_message(user_id, f"Через 5 минут у тебя {subject} в {lesson_time}! 🚀")


def schedule_reminders():
    """Ставит напоминания Дарине и Алиман на сегодня"""
    now = datetime.now()
    weekday = str(now.weekday())

    for child_name in ["Дарина", "Алиман"]:
        if child_name in schedule and weekday in schedule[child_name]:
            for lesson_time, subject in schedule[child_name][weekday].items():
                reminder_time = datetime.strptime(lesson_time, "%H:%M") - timedelta(minutes=5)
                reminder_time = reminder_time.replace(year=now.year, month=now.month, day=now.day)

                delay = (reminder_time - now).total_seconds()
                if delay > 0:
                    threading.Timer(delay, send_reminder, args=[child_name, subject, lesson_time]).start()


def send_mom_reminder(latest_time, children_str):
    """Шлём маме напоминание за 20 минут"""
    if MOM_ID:
        bot.send_message(MOM_ID, f"Через 20 минут ({latest_time.strftime('%H:%M')}) "
                                 f"у детей ({children_str}) закончатся уроки. Можно ехать их забирать 🚗")


def schedule_mom_reminder():
    """Ставит напоминание маме на сегодня"""
    now = datetime.now()
    weekday = str(now.weekday())
    latest_end_time, children_today = get_latest_end(weekday)

    if not latest_end_time or not children_today:
        return

    reminder_time = latest_end_time - timedelta(minutes=20)
    reminder_time = reminder_time.replace(year=now.year, month=now.month, day=now.day)

    delay = (reminder_time - now).total_seconds()
    if delay > 0:
        children_str = ", ".join(children_today)
        threading.Timer(delay, send_mom_reminder, args=[latest_end_time, children_str]).start()


def daily_scheduler():
    """Каждый день в полночь пересчитывает все напоминания"""
    while True:
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
        sleep_time = (tomorrow - now).total_seconds()
        time.sleep(sleep_time)

        # Новый день — пересчитываем напоминания
        schedule_reminders()
        schedule_mom_reminder()


# =================== КОМАНДЫ ===================
@bot.message_handler(commands=['start'])
# def start(message):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     start_btn = types.KeyboardButton("Старт")
#     markup.add(start_btn)
#     bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! "
#                                       f"Нажми 'Старт', чтобы открыть меню.", reply_markup=markup)
#

# @bot.message_handler(func=lambda message: message.text == "Старт")
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}! ", reply_markup=markup)

    # кнопки с описанием
    buttons = [
        types.KeyboardButton("/today - Расписание на сегодня"),
        types.KeyboardButton("/children - Выбрать ребёнка"),
        types.KeyboardButton("/weekdays - Расписание по дню недели"),
        types.KeyboardButton("/zabrat - Самое позднее занятие сегодня"),
        types.KeyboardButton("/zabratpotom - Самое позднее занятие в выбранный день"),
    ]

    # кнопка старт всегда внизу
    start_btn = types.KeyboardButton("/start - Старт")

    markup.add(*buttons)
    markup.add(start_btn)

    bot.send_message(
        message.chat.id,
        "Меню команд:\n"
        "📅 /today – расписание на сегодня\n"
        "👶 /children – выбрать ребёнка\n"
        "🗓 /weekdays – расписание по дню недели\n"
        "🚗 /zabrat – время забирания сегодня\n"
        "⏳ /zabratpotom – забирание в выбранный день",
        reply_markup=markup
    )


@bot.message_handler(commands=['today'])
def today(message):
    user_id = str(message.from_user.id)
    child_name = user_to_child.get(user_id)
    if not child_name:
        bot.send_message(message.chat.id, "Я не знаю твоего имени, напиши администратору 🙃")
        return
    weekday = str(datetime.now().weekday())
    text = get_schedule_text(child_name, weekday)
    bot.send_message(message.chat.id, f"Сегодня у тебя:\n{text}" if "Расписание" in text else text)


@bot.message_handler(commands=['children'])
def children(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [types.KeyboardButton(name) for name in schedule.keys()]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выберите ребёнка:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in schedule.keys())
def show_schedule(message):
    child_name = message.text
    weekday = str(datetime.now().weekday())
    text = get_schedule_text(child_name, weekday)
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['weekdays'])
def weekdays(message):
    markup = types.InlineKeyboardMarkup()
    for name in schedule.keys():
        markup.add(types.InlineKeyboardButton(text=name, callback_data=f"child_{name}"))
    bot.send_message(message.chat.id, "Выберите ребёнка:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("child_"))
def choose_day(call):
    child_name = call.data.split("_")[1]
    markup = days_keyboard("day", child_name)
    bot.send_message(call.message.chat.id,
                     f"Выберите день для {child_name} (0 - понедельник, 6 - воскресенье):",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def show_schedule_day(call):
    _, child_name, day = call.data.split("_")
    text = get_schedule_text(child_name, day)
    bot.send_message(call.message.chat.id, text)


@bot.message_handler(commands=['zabrat'])
def zabrat_today(message):
    day = str(datetime.now().weekday())
    latest_end_time, children_today = get_latest_end(day)
    if not children_today:
        bot.send_message(message.chat.id, "Сегодня ни у кого нет занятий, можно отдыхать 😎")
        return
    latest_time_str = latest_end_time.strftime("%H:%M")
    children_str = ", ".join(children_today)
    bot.send_message(message.chat.id,
                     f"Сегодня у детей ({children_str}) самое позднее окончание занятия в {latest_time_str}. "
                     f"Мама может забрать всех в это время.")


@bot.message_handler(commands=['zabratpotom'])
def choose_day_for_zabrat(message):
    markup = days_keyboard("zabratday")
    bot.send_message(message.chat.id,
                     "Выберите день (0 - понедельник, 6 - воскресенье):",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("zabratday_"))
def zabratpotom(call):
    day = call.data.split("_")[1]
    latest_end_time, children_today = get_latest_end(day)
    if not children_today:
        bot.send_message(call.message.chat.id, f"В этот день у детей нет занятий 😎")
        return
    latest_time_str = latest_end_time.strftime("%H:%M")
    children_str = ", ".join(children_today)
    bot.send_message(call.message.chat.id,
                     f"В этот день ({day}) у детей ({children_str}) самое позднее окончание занятия в {latest_time_str}. "
                     f"Мама может забрать всех в это время.")


# =================== ЗАПУСК ===================
schedule_reminders()
schedule_mom_reminder()
threading.Thread(target=daily_scheduler, daemon=True).start()

# при старте задаём команды для меню возле скрепки
bot.set_my_commands([
    BotCommand("start", "Запуск бота и меню"),
    BotCommand("today", "Расписание на сегодня"),
    BotCommand("children", "Выбрать ребёнка"),
    BotCommand("weekdays", "Расписание по дню недели"),
    BotCommand("zabrat", "Самое позднее занятие сегодня"),
    BotCommand("zabratpotom", "Самое позднее занятие в выбранный день"),
])

bot.polling(none_stop=True)
