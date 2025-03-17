import telebot
from telebot import types
import sqlite3

# Инициализация бота
bot = telebot.TeleBot('7576662427:AAGso4U9daybsZqD92Y77dtJJypFeYVkEko')


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, role TEXT, rating REAL DEFAULT 0.0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, employer_id INTEGER, 
                 title TEXT, description TEXT, price REAL, category TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS applications 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER, student_id INTEGER)''')
    conn.commit()
    conn.close()


# Стартовая команда
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👨‍🎓 Я студент")
    btn2 = types.KeyboardButton("👩‍💼 Я работодатель")
    markup.add(btn1, btn2)
    bot.reply_to(message, "Добро пожаловать в WorkMatch!\nВыберите свою роль:", reply_markup=markup)


# Обработка выбора роли и команд
@bot.message_handler(content_types=['text'])
def handle_text(message):
    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()

    if message.text == "👨‍🎓 Я студент":
        c.execute("INSERT OR REPLACE INTO users (user_id, role) VALUES (?, ?)",
                  (message.from_user.id, "student"))
        conn.commit()
        show_student_menu(message)
    elif message.text == "👩‍💼 Я работодатель":
        c.execute("INSERT OR REPLACE INTO users (user_id, role) VALUES (?, ?)",
                  (message.from_user.id, "employer"))
        conn.commit()
        show_employer_menu(message)
    elif message.text == "➕ Создать задание":
        create_task(message)
    elif message.text == "👤 Мой профиль":
        show_profile(message)
    elif message.text == "📋 Найти задание":
        find_task(message)
    elif message.text in ["Доставка", "Онлайн-задача", "Помощник", "Все категории"]:
        show_tasks(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки меню")

    conn.close()


# Меню студента
def show_student_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("📋 Найти задание")
    btn2 = types.KeyboardButton("👤 Мой профиль")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Меню студента:", reply_markup=markup)


# Меню работодателя
def show_employer_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("➕ Создать задание")
    btn2 = types.KeyboardButton("👤 Мой профиль")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Меню работодателя:", reply_markup=markup)


# Создание задания
def create_task(message):
    msg = bot.send_message(message.chat.id, "Введите название задания:")
    bot.register_next_step_handler(msg, process_task_title)


def process_task_title(message):
    task = {'title': message.text}
    msg = bot.send_message(message.chat.id, "Введите описание задания:")
    bot.register_next_step_handler(msg, process_task_description, task)


def process_task_description(message, task):
    task['description'] = message.text
    msg = bot.send_message(message.chat.id, "Введите цену:")
    bot.register_next_step_handler(msg, process_task_price, task)


def process_task_price(message, task):
    try:
        task['price'] = float(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Доставка")
        btn2 = types.KeyboardButton("Онлайн-задача")
        btn3 = types.KeyboardButton("Помощник")
        markup.add(btn1, btn2, btn3)
        msg = bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_task_category, task)
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите корректную цену")


def process_task_category(message, task):
    task['category'] = message.text
    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (employer_id, title, description, price, category, status) VALUES (?, ?, ?, ?, ?, ?)",
              (message.from_user.id, task['title'], task['description'], task['price'], task['category'], 'active'))
    conn.commit()
    conn.close()
    show_employer_menu(message)
    bot.send_message(message.chat.id, "Задание успешно создано!")


# Поиск заданий
def find_task(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Доставка")
    btn2 = types.KeyboardButton("Онлайн-задача")
    btn3 = types.KeyboardButton("Помощник")
    btn4 = types.KeyboardButton("Все категории")
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)


def show_tasks(message):
    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()

    category = message.text if message.text != "Все категории" else None
    if category:
        c.execute("SELECT * FROM tasks WHERE status='active' AND category=?", (category,))
    else:
        c.execute("SELECT * FROM tasks WHERE status='active'")

    tasks = c.fetchall()
    conn.close()

    if tasks:
        for task in tasks:
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("Откликнуться", callback_data=f"apply_{task[0]}")
            markup.add(btn)
            bot.send_message(message.chat.id,
                             f"📌 {task[2]}\n📝 {task[3]}\n💰 {task[4]} руб.\n🏷 {task[5]}",
                             reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Активных заданий в этой категории пока нет")
    show_student_menu(message)


# Обработка отклика
@bot.callback_query_handler(func=lambda call: call.data.startswith('apply_'))
def apply_task(call):
    task_id = int(call.data.split('_')[1])
    student_id = call.from_user.id

    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()

    # Сохраняем отклик в таблице applications
    c.execute("INSERT INTO applications (task_id, student_id) VALUES (?, ?)", (task_id, student_id))

    # Получаем информацию о задании и работодателе
    c.execute("SELECT employer_id, title FROM tasks WHERE id=?", (task_id,))
    task = c.fetchone()
    employer_id = task[0]
    task_title = task[1]

    # Получаем информацию о студенте
    c.execute("SELECT rating FROM users WHERE user_id=?", (student_id,))
    student = c.fetchone()
    student_rating = student[0] if student else 0.0

    conn.commit()
    conn.close()

    # Уведомление студенту
    bot.send_message(call.message.chat.id, "Вы успешно откликнулись на задание!")
    bot.answer_callback_query(call.id)

    # Уведомление работодателю с ссылкой на профиль студента
    try:
        student_link = f"tg://user?id={student_id}"
        employer_message = (
            f"Кто-то откликнулся на ваше задание: '{task_title}'\n"
            f"Студент: @{call.from_user.username if call.from_user.username else 'Без имени'}\n"
            f"ID студента: {student_id}\n"
            f"Рейтинг студента: {student_rating}\n"
            f"[Связаться со студентом]({student_link})"
        )
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Написать студенту", callback_data=f"contact_{student_id}_{task_id}")
        markup.add(btn)
        bot.send_message(employer_id, employer_message, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        print(f"Не удалось отправить уведомление работодателю: {e}")


# Обработка кнопки "Написать студенту"
@bot.callback_query_handler(func=lambda call: call.data.startswith('contact_'))
def contact_student(call):
    data = call.data.split('_')
    student_id = int(data[1])
    task_id = int(data[2])

    bot.send_message(call.message.chat.id, "Напишите сообщение для студента:")
    bot.register_next_step_handler(call.message, send_message_to_student, student_id, task_id)


def send_message_to_student(message, student_id, task_id):
    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()
    c.execute("SELECT title FROM tasks WHERE id=?", (task_id,))
    task = c.fetchone()
    task_title = task[0] if task else "Неизвестное задание"
    conn.close()

    employer_message = f"Работодатель отправил вам сообщение по заданию '{task_title}':\n{message.text}"
    try:
        bot.send_message(student_id, employer_message)
        bot.send_message(message.chat.id, "Сообщение успешно отправлено студенту!")
    except Exception as e:
        bot.send_message(message.chat.id, "Не удалось отправить сообщение студенту.")
        print(f"Ошибка при отправке сообщения: {e}")
    show_employer_menu(message)


# Просмотр профиля
def show_profile(message):
    conn = sqlite3.connect('workmatch.db')
    c = conn.cursor()
    c.execute("SELECT role, rating FROM users WHERE user_id=?", (message.from_user.id,))
    user = c.fetchone()
    conn.close()

    if user:
        role = "Студент" if user[0] == "student" else "Работодатель"
        bot.send_message(message.chat.id, f"Ваша роль: {role}\nВаш рейтинг: {user[1]}")
    else:
        bot.send_message(message.chat.id, "Профиль не найден")

    if user and user[0] == "employer":
        show_employer_menu(message)
    elif user and user[0] == "student":
        show_student_menu(message)


# Запуск бота
if __name__ == '__main__':
    init_db()
    bot.polling(none_stop=True)
