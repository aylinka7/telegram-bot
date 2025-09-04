import os
from dotenv import load_dotenv
import telebot
import webbrowser
from telebot import types
import sqlite3

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
name  = None

@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open('https://61.edubish.kg/')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Перейти на сайт')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Удалить фото')
    btn3 = types.KeyboardButton('Изменить текст')
    markup.row(btn2, btn3)
    file = open('./img.png', 'rb')
    bot.send_photo(message.chat.id, file, reply_markup=markup)
    # bot.send_audio(message.chat.id, file, reply_markup=markup)
    # bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!', reply_markup=markup)
    bot.register_next_step_handler(message, on_click)

    conn = sqlite3.connect('raspisanie.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment PRIMARY KEY, name varchar(50), pass varchar(50))')
    conn.commit()
    cur.close()
    conn.close()

    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}, введи свое имя для регистрации')
    bot.register_next_step_handler(message, user_name)

def on_click(message):
    if message.text == 'Перейти на сайт':
        bot.send_message(message.chat.id, 'Сайт открыт')
    elif message.text == 'Удалить фото':
        bot.send_message(message.chat.id, 'Удалено')



def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Введите пароль!')
    bot.register_next_step_handler(message, user_pass)

def user_pass(message):
    password = message.text.strip()
    conn = sqlite3.connect('raspisanie.sql')
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, pass) VALUES ('%s', '%s')" % (name, password))
    conn.commit()
    cur.close()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Список пользователей', callback_data='users'))
    bot.send_message(message.chat.id, 'Пользователь зарегистрирован!', reply_markup=markup)

@bot.message_handler(commands=['help'])
def main(message):
    bot.send_message(message.chat.id, '<b>Вот</b>, надеюсь поможет)', parse_mode='html')

@bot.message_handler(content_types=['photo'])
def get_photo(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Перейти на сайт', url='https://google.com')
    markup.row(btn1)
    btn2 = types.InlineKeyboardButton('Удалить фото', callback_data='delete')
    btn3 = types.InlineKeyboardButton('Изменить текст', callback_data='edit')
    markup.row(btn2, btn3)
    bot.reply_to(message, 'Какое красивое фото!', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'delete':
        bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)
    elif callback.data == 'edit':
        bot.edit_message_text('Edit text', callback.message.chat.id, callback.message.message_id)
    elif callback.data == 'users':
        conn = sqlite3.connect('raspisanie.sql')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        info = ''
        for el in users:
            info += f'Имя: {el[1]}, пароль: {el[2]}\n'

        cur.close()
        conn.close()
        bot.send_message(callback.message.chat.id, info)

# @bot.callback_query_handler(func=lambda callback: True)
# def callback(call):
#     conn = sqlite3.connect('raspisanie.sql')
#     cur = conn.cursor()
#     cur.execute("SELECT * FROM users")
#     users = cur.fetchall()
#
#     info = ''
#     for el in users:
#         info += f'Имя: {el[1]}, пароль: {el[2]}\n'
#
#     cur.close()
#     conn.close()
#     bot.send_message(call.message.chat.id, info)

@bot.message_handler()
def info(message):
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, 'Привет еще раз!')




bot.polling(none_stop=True)