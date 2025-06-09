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

# Обработчик команды /site - открывает сайт в браузере
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open(SITE_URL)

# Получаем IP адрес компьютера для доступа к сайту
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
SITE_URL = f"http://{local_ip}:8081"  # Используем IP вместо localhost
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
    btn7 = types.InlineKeyboardButton("🌐 Наш сайт", url=SITE_URL)
    btn8 = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    bot.send_message(message.chat.id, f'👋 Привет, {message.from_user.first_name}! \n\n🔍 Выберите опцию из меню ниже:', reply_markup=markup)

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
    btn7 = types.InlineKeyboardButton("🌐 Наш сайт", url=SITE_URL)
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    bot.send_message(message.chat.id, "🔍 Выберите опцию из меню ниже:", reply_markup=markup)

# Обработчик команды /help - информация об оплате
@bot.message_handler(commands=["help"])
def main(message):
    bot.send_message(message.chat.id, "✨ <b>Успешных</b> <em><u>занятий!</u></em> ✨", parse_mode="html")

# Обработчик всех callback-запросов от кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    # Обработка различных callback-данных
    if call.data == "commands":
        # Показываем информацию о пакетах занятий
        packages_text = """📚 Доступные пакеты занятий:

⏱ Разовое занятие (50 минут) - 300 грн

📦 Пакет А:   📦 Пакет Б:     📦 Пакет В:
• 5 занятий   • 10 занятий    • 20 занятий
• 45 минут    • 50 минут      • 60 минут
• 1400 грн    • 2400 грн      • 4400 грн"""


        bot.send_message(call.message.chat.id, packages_text)
    elif call.data == "about":
        # Показываем информацию о ценах и акциях
        about_text = f"""💰 Цены и акции:

🎁 Специальное предложение:
При оплате пакетов А, Б или В - первое занятие бесплатно!

📝 Это бот для получения информации и оплаты уроков математики.

🌐 Наши социальные сети:
<a href="{FACEBOOK_URL}">Facebook</a>
<a href="{INSTAGRAM_URL}">Instagram</a>"""
        bot.send_message(call.message.chat.id, about_text, parse_mode="HTML", disable_web_page_preview=True)
    elif call.data == "contacts":
        # Показываем информацию о занятиях
        zoom_text = """🎓 Информация о занятиях:

📅 Занятия проходят по назначенному расписанию
💻 Платформа: Zoom
🔗 Ссылка на конференцию:
https://us05web.zoom.us/j/6281722803?pwd=TFNSSHpwSEhJMVVZY2NSRzUrcFkwdz09"""
        bot.send_message(call.message.chat.id, zoom_text)
    elif call.data == "help":
        # Показываем информацию об оплате
        payment_text = """💳 Информация об оплате:

🏦 Банковская карта (monobank):
<b><u>4441 1110 7175 4448</u></b>

💎 TON coin:
<b><u>UQCQelJLMF451RE4fJIg1UWleDBZksfDyHMkxZj68e7GTe1M</u></b>"""
        bot.send_message(call.message.chat.id, payment_text, parse_mode="HTML")
    elif call.data == "contacts_info":
        # Показываем контактную информацию
        contact_text = f"""📞 Наши контакты:

📱 Telegram бот: @zno_nmt2025_bot
📧 Email: konovalenkodim@gmail.com
💬 Telegram группа: @zno_ukraine2018
🌐 Facebook: <a href="{FACEBOOK_URL}">Наша страница</a>
📸 Instagram: <a href="{INSTAGRAM_URL}">Наш Instagram</a>

⏰ Часы работы:
Пн-Пт: 9:00 - 20:00"""
        bot.send_message(call.message.chat.id, contact_text, parse_mode="HTML", disable_web_page_preview=True)
    elif call.data == "reviews":
        # Показываем меню отзывов
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("⭐️ Посмотреть отзывы на сайте", url=SITE_URL)
        btn2 = types.InlineKeyboardButton("📘 Отзывы на Facebook", url=FACEBOOK_URL)
        btn3 = types.InlineKeyboardButton("📸 Отзывы в Instagram", url=INSTAGRAM_URL)
        markup.add(btn1, btn2, btn3)
        bot.send_message(call.message.chat.id, "📝 Выберите, где вы хотите посмотреть отзывы:", reply_markup=markup)
    elif call.data == "website":
        # Показываем меню сайта
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("🌐 Открыть сайт", url="http://localhost:8081")
        btn2 = types.InlineKeyboardButton("📘 Наш Facebook", url=FACEBOOK_URL)
        btn3 = types.InlineKeyboardButton("📸 Наш Instagram", url=INSTAGRAM_URL)
        markup.add(btn1, btn2, btn3)
        bot.send_message(call.message.chat.id, "🔗 Выберите, куда вы хотите перейти:", reply_markup=markup)
    elif call.data == "schedule":
        # Показываем расписание
        markup = create_schedule_keyboard()
        bot.send_message(call.message.chat.id, "📅 Выберите дату для занятия:", reply_markup=markup)
    elif call.data.startswith("date_"):
        # Обработка выбора даты
        date = call.data.split("_")[1]
        user_data[call.from_user.id] = {"date": date}
        markup = create_time_keyboard()
        bot.send_message(call.message.chat.id, f"🕒 Выберите время для занятия на {date}:", reply_markup=markup)
    elif call.data.startswith("time_"):
        # Обработка выбора времени
        time = call.data.split("_")[1]
        user_id = call.from_user.id
        if user_id in user_data and "date" in user_data[user_id]:
            date = user_data[user_id]["date"]
            confirmation_text = f"""✅ Подтверждение записи:

📅 Дата: {date}
🕒 Время: {time}

Для подтверждения записи, пожалуйста, оплатите занятие.
💳 Реквизиты для оплаты можно получить, нажав кнопку 'Оплата' в главном меню."""
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            btn1 = types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_booking")
            btn2 = types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking")
            markup.add(btn1, btn2)
            
            bot.send_message(call.message.chat.id, confirmation_text, reply_markup=markup)
    elif call.data == "confirm_booking":
        # Подтверждение записи
        bot.send_message(call.message.chat.id, "✅ Спасибо за запись! Мы свяжемся с вами для подтверждения оплаты.")
    elif call.data == "cancel_booking":
        # Отмена записи
        bot.send_message(call.message.chat.id, "❌ Запись отменена. Вы можете попробовать записаться снова.")
        if call.from_user.id in user_data:
            del user_data[call.from_user.id]

# Обработчик текстовых сообщений
@bot.message_handler()
def info(message):
    if message.text.lower() == "привет":
        bot.send_message(message.chat.id, f'👋 Привет, {message.from_user.first_name} {message.from_user.last_name}!')
    elif message.text.lower() == "id":
        bot.reply_to(message, f'🆔 Ваш ID: {message.from_user.id}')

# Запуск бота
bot.polling(none_stop=True)