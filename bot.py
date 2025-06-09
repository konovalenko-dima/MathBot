# Импортируем необходимые библиотеки
import telebot
from telebot import types
from dotenv import load_dotenv
import os
import webbrowser
from datetime import datetime, timedelta
import socket

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен бота из переменных окружения
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Получаем IP адрес компьютера для доступа к сайту
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
SITE_URL = f"http://{local_ip}:8081"  # Локальный URL для разработки
FACEBOOK_URL = "https://www.facebook.com/dmitry.konovalenko.1/friends"
INSTAGRAM_URL = "https://instagram.com/dmitry.konovalenko"

# Словарь для хранения временных данных пользователей
user_data = {}

# Доступные часы для занятий
AVAILABLE_HOURS = [
    "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"
]

# Функция получения дат на неделю вперед (только рабочие дни)
def get_week_dates():
    today = datetime.now()
    dates = []
    for i in range(7):
        date = today + timedelta(days=i)
        if date.weekday() < 5:  # Только рабочие дни (0-4)
            dates.append(date.strftime("%d.%m.%Y"))
    return dates

# Создание клавиатуры с датами для записи
def create_schedule_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    dates = get_week_dates()
    buttons = []
    for date in dates:
        btn = types.InlineKeyboardButton(date, callback_data=f"date_{date}")
        buttons.append(btn)
    markup.add(*buttons)
    return markup

# Создание клавиатуры с доступным временем
def create_time_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for hour in AVAILABLE_HOURS:
        btn = types.InlineKeyboardButton(hour, callback_data=f"time_{hour}")
        buttons.append(btn)
    markup.add(*buttons)
    return markup

# Обработчик команды /site - открывает сайт в браузере
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open(SITE_URL)
    bot.send_message(message.chat.id, f"🌐 Локальный адрес сайта: {SITE_URL}")

# Обработчик команды /start - главное меню
@bot.message_handler(commands=["start", "main", "hello"])
def main(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📚 Пакеты занятий", callback_data="commands")
    btn2 = types.InlineKeyboardButton("💰 Цены и акции", callback_data="about")
    btn3 = types.InlineKeyboardButton("🎓 Занятия", callback_data="contacts")
    btn4 = types.InlineKeyboardButton("💳 Оплата", callback_data="help")
    btn5 = types.InlineKeyboardButton("📞 Контакты", callback_data="contacts_info")
    btn6 = types.InlineKeyboardButton("⭐️ Отзывы", callback_data="reviews")
    btn7 = types.InlineKeyboardButton("🌐 Наш сайт", callback_data="site_url")
    btn8 = types.InlineKeyboardButton("📅 Расписание", callback_data="schedule")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    
    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

Добро пожаловать в бот репетитора по математике! 🎓

📱 Выберите нужный раздел в меню ниже ⬇️"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Обработчик команды /info - информационное меню
@bot.message_handler(commands=["info"])
def info(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📚 Пакеты занятий", callback_data="commands")
    btn2 = types.InlineKeyboardButton("💰 Цены и акции", callback_data="about")
    btn3 = types.InlineKeyboardButton("🎓 Занятия", callback_data="contacts")
    btn4 = types.InlineKeyboardButton("💳 Оплата", callback_data="help")
    btn5 = types.InlineKeyboardButton("📞 Контакты", callback_data="contacts_info")
    btn6 = types.InlineKeyboardButton("⭐️ Отзывы", callback_data="reviews")
    btn7 = types.InlineKeyboardButton("🌐 Наш сайт", callback_data="site_url")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    bot.send_message(message.chat.id, "🔍 Выберите опцию из меню ниже:", reply_markup=markup)

# Обработчик команды /help - информация об оплате
@bot.message_handler(commands=["help"])
def main(message):
    bot.send_message(message.chat.id, "✨ <b>Успешных</b> <em><u>занятий!</u></em> ✨", parse_mode="html")

# Обработчик всех callback-запросов от кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "site_url":
        bot.send_message(call.message.chat.id, f"🌐 Локальный адрес сайта: {SITE_URL}")
    elif call.data == "commands":
        packages_text = """📚 <b>Пакеты занятий</b>

🎯 <b>Разовое занятие:</b>
• 50 минут
• 300 грн

📦 <b>Пакет А:</b>
• 5 занятий
• 45 минут
• 1400 грн

📦 <b>Пакет Б:</b>
• 10 занятий
• 50 минут
• 2400 грн

📦 <b>Пакет В:</b>
• 20 занятий
• 60 минут
• 4400 грн

💫 <i>Выберите удобный для вас вариант!</i>"""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
        markup.add(btn)
        bot.send_message(call.message.chat.id, packages_text, parse_mode="HTML", reply_markup=markup)

    elif call.data == "about":
        about_text = f"""💰 <b>Цены и акции</b>

🎁 <b>Специальное предложение:</b>
При оплате любого пакета (А, Б или В) - первое занятие бесплатно!

💎 <b>Наши преимущества:</b>
• Индивидуальный подход
• Гибкий график
• Онлайн и офлайн занятия
• Современные методики

🌐 <b>Мы в соцсетях:</b>
<a href="{FACEBOOK_URL}">📘 Facebook</a>
<a href="{INSTAGRAM_URL}">📸 Instagram</a>"""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
        markup.add(btn)
        bot.send_message(call.message.chat.id, about_text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=markup)

    elif call.data == "contacts":
        zoom_text = """🎓 <b>Информация о занятиях</b>

📱 <b>Формат занятий:</b>
• Онлайн через Zoom
• Индивидуальный подход
• Интерактивные материалы

🔗 <b>Ссылка на Zoom:</b>
https://us05web.zoom.us/j/6281722803?pwd=TFNSSHpwSEhJMVVZY2NSRzUrcFkwdz09

💡 <i>Все материалы предоставляются бесплатно!</i>"""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
        markup.add(btn)
        bot.send_message(call.message.chat.id, zoom_text, parse_mode="HTML", reply_markup=markup)

    elif call.data == "help":
        payment_text = """💳 <b>Способы оплаты</b>

🏦 <b>Банковская карта (monobank):</b>
<code>4441 1110 7175 4448</code>

💎 <b>TON coin:</b>
<code>UQCQelJLMF451RE4fJIg1UWleDBZksfDyHMkxZj68e7GTe1M</code>

💫 <i>После оплаты отправьте скриншот чека для подтверждения</i>"""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
        markup.add(btn)
        bot.send_message(call.message.chat.id, payment_text, parse_mode="HTML", reply_markup=markup)

    elif call.data == "contacts_info":
        contact_text = f"""📞 <b>Наши контакты</b>

📱 <b>Telegram:</b>
• Бот: @zno_nmt2025_bot
• Группа: @zno_ukraine2018

📧 <b>Email:</b>
konovalenkodim@gmail.com

🌐 <b>Социальные сети:</b>
<a href="{FACEBOOK_URL}">📘 Facebook</a>
<a href="{INSTAGRAM_URL}">📸 Instagram</a>

⏰ <b>Часы работы:</b>
Пн-Пт: 9:00 - 20:00"""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
        markup.add(btn)
        bot.send_message(call.message.chat.id, contact_text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=markup)

    elif call.data == "reviews":
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("⭐️ Отзывы на сайте", url=SITE_URL)
        btn2 = types.InlineKeyboardButton("📘 Отзывы на Facebook", url=FACEBOOK_URL)
        btn3 = types.InlineKeyboardButton("📸 Отзывы в Instagram", url=INSTAGRAM_URL)
        btn4 = types.InlineKeyboardButton("📅 Расписание", callback_data="schedule")
        markup.add(btn1, btn2, btn3, btn4)
        
        reviews_text = """⭐️ <b>Отзывы наших учеников</b>

Выберите платформу, где хотите посмотреть отзывы ⬇️

💫 <i>Мы гордимся успехами наших учеников!</i>"""
        
        bot.send_message(call.message.chat.id, reviews_text, parse_mode="HTML", reply_markup=markup)

    elif call.data == "schedule":
        markup = create_schedule_keyboard()
        schedule_text = """📅 <b>Выберите дату для занятия</b>

Доступны только рабочие дни (Пн-Пт)
Выберите удобную дату ⬇️"""
        bot.send_message(call.message.chat.id, schedule_text, parse_mode="HTML", reply_markup=markup)

    elif call.data.startswith("date_"):
        date = call.data.split("_")[1]
        user_data[call.from_user.id] = {"date": date}
        markup = create_time_keyboard()
        time_text = f"""🕒 <b>Выберите время для занятия</b>

Дата: {date}
Выберите удобное время ⬇️"""
        bot.send_message(call.message.chat.id, time_text, parse_mode="HTML", reply_markup=markup)

    elif call.data.startswith("time_"):
        time = call.data.split("_")[1]
        user_id = call.from_user.id
        if user_id in user_data and "date" in user_data[user_id]:
            date = user_data[user_id]["date"]
            confirmation_text = f"""✅ <b>Подтверждение записи</b>

📅 <b>Дата:</b> {date}
🕒 <b>Время:</b> {time}

💳 <b>Для подтверждения записи:</b>
1. Оплатите занятие
2. Нажмите кнопку "Подтвердить"
3. Отправьте скриншот оплаты"""
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn1 = types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_booking")
            btn2 = types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking")
            btn3 = types.InlineKeyboardButton("💳 Оплата", callback_data="help")
            markup.add(btn1, btn2, btn3)
            
            bot.send_message(call.message.chat.id, confirmation_text, parse_mode="HTML", reply_markup=markup)

    elif call.data == "confirm_booking":
        confirm_text = """✅ <b>Спасибо за запись!</b>

Мы свяжемся с вами для подтверждения оплаты.

💫 <i>До встречи на занятии!</i>"""
        bot.send_message(call.message.chat.id, confirm_text, parse_mode="HTML")

    elif call.data == "cancel_booking":
        cancel_text = """❌ <b>Запись отменена</b>

Вы можете попробовать записаться снова, нажав кнопку "Расписание" в главном меню."""
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton("📅 Записаться снова", callback_data="schedule")
        markup.add(btn)
        
        bot.send_message(call.message.chat.id, cancel_text, parse_mode="HTML", reply_markup=markup)
        if call.from_user.id in user_data:
            del user_data[call.from_user.id]

# Обработчик текстовых сообщений
@bot.message_handler()
def info(message):
    if message.text.lower() == "привет":
        bot.send_message(message.chat.id, f'👋 Привет, {message.from_user.first_name} {message.from_user.last_name}!')
    elif message.text.lower() == "id":
        bot.reply_to(message, f'🆔 Ваш ID: {message.from_user.id}')

# Обработчик выхода пользователя из чата
@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message):
    farewell_text = """👋 <b>До новых встреч!</b>

Спасибо, что были с нами! 

💫 <i>Желаем вам успехов в изучении математики!</i>

Если захотите вернуться, мы всегда будем рады видеть вас снова! 🌟"""
    
    bot.send_message(message.chat.id, farewell_text, parse_mode="HTML")

# Запуск бота
bot.polling(none_stop=True)