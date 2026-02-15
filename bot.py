from telebot import TeleBot, types
from config import TOKEN
import sqlite3

bot = TeleBot(TOKEN)

user_data = {}

level1 = [
    {
        "q": "Сколько континентов на Земле",
        "options": ["3", "5", "7"],
        "answer": 2
    },
    {
        "q": "16 * 2",
        "options": ["33", "64", "32"],
        "answer": 2
    },
    {
        "q": "как пишется слово (не) знаю",
        "options": ["слитно", "раздельно", "не знаю"],
        "answer": 1
    },
]
level2 = [
    {
        "q": "Сколько будет 80 * на 10",
        "options": ["100", "50", "400", "160", "800", "1600"],
        "answer": 4
    },
]


quiz = level1 + level2

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY,
    text TEXT
)
""")

cursor.execute("INSERT OR IGNORE INTO schedule (id, text) VALUES (1, 'Расписание пока не установлено')")
conn.commit()

ADMIN_ID = 'вписать свой id в телеграме'

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет я бот для показа информации о школе, расписания и т.д, можете написать команду /reg и продолжить' )

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '''
в боте есть такие команды как 
    /login [логин] [пароль] 
    /reg [логин] [пароль]  
    /schedule
    /quiz
    /schedule_rename
                         
                     ''')

@bot.message_handler(commands=['login'])
def login_user(message):
    try:
        _, login, password = message.text.split()

        cursor.execute("SELECT role FROM users WHERE login=? AND password=?",
                       (login, password))
        user = cursor.fetchone()

        if not user:
            bot.reply_to(message, "Неверный логин или пароль")
            return

        if user[0] == "ожидание":
            bot.reply_to(message, "Аккаунт не подтверждён")
            return

        
        cursor.execute("UPDATE users SET telegram_id=? WHERE login=?",
                       (message.from_user.id, login))
        conn.commit()

        bot.reply_to(message, f"Вы вошли как {user[0]}")

    except:
        bot.reply_to(message, "Используй: /login логин пароль")



@bot.message_handler(commands=['reg'])
def register(message):
    try:
        _, login, password = message.text.split()

        cursor.execute("INSERT INTO users (login, password, role) VALUES (?, ?, ?)",
                       (login, password, "ожидание"))
        conn.commit()

        bot.reply_to(message, "Заявка отправлена. Ожидайте подтверждения админа")

    except sqlite3.IntegrityError:
        bot.reply_to(message, "Такой логин уже существует")

    except:
        bot.reply_to(message, "Используй: /reg логин пароль")

@bot.message_handler(commands=['setrole'])
def set_role(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У тебя нет доступа")
        return

    try:
        _, login, role = message.text.split()

        if role not in ["учитель", "ученик"]:
            bot.reply_to(message, "Роль: учитель или ученик")
            return

        cursor.execute("UPDATE users SET role=? WHERE login=?", (role, login))
        conn.commit()

        bot.reply_to(message, f"Роль {role} назначена пользователю {login}")

    except:
        bot.reply_to(message, "Используй: /setrole логин учитель/ученик")

@bot.message_handler(commands=['schedule_rename'])
def rename_schedule(message):
    telegram_id = message.from_user.id

    cursor.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,))
    user = cursor.fetchone()

    if not user:
        bot.reply_to(message, "Сначала войдите через /login ")
        return

    if user[0] != "учитель":
        bot.reply_to(message, "Только учитель может менять расписание ")
        return

    msg = bot.reply_to(message, "Введите новое расписание:")
    bot.register_next_step_handler(msg, save_new_schedule)


def save_new_schedule(message):
    new_text = message.text

    cursor.execute("UPDATE schedule SET text=? WHERE id=1", (new_text,))
    conn.commit()

    bot.reply_to(message, "Расписание успешно обновлено ")

    
@bot.message_handler(commands=['schedule'])
def show_schedule(message):
    telegram_id = message.from_user.id

    cursor.execute("SELECT role FROM users WHERE telegram_id=?", (telegram_id,))
    user = cursor.fetchone()

    if not user:
        bot.reply_to(message, "Сначала войдите через /login ")
        return

    cursor.execute("SELECT text FROM schedule WHERE id=1")
    schedule = cursor.fetchone()

    bot.reply_to(message, f" Текущее расписание:\n\n{schedule[0]}")

@bot.message_handler(commands=['quiz'])
@bot.message_handler(commands=['wik'])
def wik(message):
    user_data[message.chat.id] = {"q": 0, "score": 0}
    send_question(message.chat.id)

def send_question(chat_id):
    q_index = user_data[chat_id]["q"]
    question = quiz[q_index]

    kb = types.InlineKeyboardMarkup()
    for i, option in enumerate(question["options"]):
        kb.add(types.InlineKeyboardButton(
            text=option,
            callback_data=str(i)
        ))

    bot.send_message(chat_id, question["q"], reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def answer(call):
    chat_id = call.message.chat.id
    user_answer = int(call.data)

    q_index = user_data[chat_id]["q"]
    if user_answer == quiz[q_index]["answer"]:
        user_data[chat_id]["score"] += 1

    user_data[chat_id]["q"] += 1

    if user_data[chat_id]["q"] >= len(quiz):
        score = user_data[chat_id]["score"]
        bot.edit_message_text(
            f"Квиз окончен! Результат: {score}/{len(quiz)}",
            chat_id,
            call.message.message_id
        )
    else:
        send_question(chat_id)

if __name__=="__main__":
    bot.polling()
    bot.polling()
