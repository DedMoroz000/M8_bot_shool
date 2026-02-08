from telebot import TeleBot, types
from config import TOKEN
import sqlite3

bot = TeleBot(TOKEN)

tg_id = {'rustolowka': 1}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет я бот для показа информации о школе, расписания и т.д, можете написать команду /login и продолжить' )

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '''
в боте есть такие команды как 
    /login [логин] [пароль] 
    /schedule
    /reg [логин] [пароль]
    /schedule_rename      
                     ''')

@bot.message_handler(commands=['login'])
def login(message):
    pass




if __name__=="__main__":
    bot.polling()