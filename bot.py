# Импортируем необходимые библиотеки
import telebot
from telebot import types
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
from calendar_sync import CalendarSync
import logging
import sys

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
load_dotenv()

# Инициализация констант
TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Проверяем наличие необходимых переменных окружения
if not TOKEN:
    logger.error("Ошибка: Не установлен TOKEN в файле .env")
    sys.exit(1)

if not ADMIN_ID:
    logger.error("Ошибка: Не установлен ADMIN_ID в файле .env")
    sys.exit(1)

try:
    # Проверяем, что ADMIN_ID является числом
    ADMIN_ID = str(int(ADMIN_ID))
except ValueError:
    logger.error("Ошибка: ADMIN_ID должен быть числом")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

# Инициализируем синхронизацию календаря
try:
    calendar = CalendarSync(calendar_name="Tutoring")
    logger.info("Календарь успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации календаря: {str(e)}")
    calendar = None

logger.info(f"Бот запущен. ADMIN_ID = {ADMIN_ID}")

# Создаем необходимые директории
RECEIPTS_DIR = Path("receipts")
RECEIPTS_DIR.mkdir(exist_ok=True)
DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "payments.db"

# Доступные часы для занятий
AVAILABLE_HOURS = [
    "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", 
    "15:00", "16:00", "17:00", "18:00", "19:00"
]

# Словари для хранения временных данных
user_data = {}
confirmed_payments = set()

def init_database():
    """Инициализация базы данных"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            file_id TEXT NOT NULL,
            local_path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            admin_response_timestamp TEXT,
            admin_comment TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS booked_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            user_id TEXT NOT NULL,
            payment_id INTEGER,
            FOREIGN KEY (payment_id) REFERENCES payments (id),
            UNIQUE(date, time)
        )
        ''')
        conn.commit()

# Инициализируем базу данных
init_database()

def save_payment_to_db(user_id, file_id, local_path, timestamp):
    """Сохранение информации о платеже в БД"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO payments (user_id, file_id, local_path, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (user_id, file_id, local_path, timestamp))
        payment_id = cursor.lastrowid
        conn.commit()
        return payment_id

def update_payment_status(payment_id, status, admin_comment=None):
    """Обновление статуса платежа"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE payments 
        SET status = ?, 
            admin_response_timestamp = ?, 
            admin_comment = ?
        WHERE id = ?
        ''', (status, datetime.now().strftime("%d.%m.%Y %H:%M"), admin_comment, payment_id))
        conn.commit()

def save_booked_slot(date, time, user_id, payment_id):
    """Сохранение забронированного слота"""
    date_obj = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M")
    end_time = date_obj + timedelta(minutes=50)
    
    if not calendar.add_event(date_obj, end_time, user_id, payment_id):
        return False
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO booked_slots (date, time, user_id, payment_id)
            VALUES (?, ?, ?, ?)
            ''', (date, time, user_id, payment_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_available_time_slots(date):
    """Получение доступных временных слотов"""
    date_obj = datetime.strptime(date, "%d.%m.%Y").date()
    busy_times = calendar.get_busy_slots(date_obj)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT time FROM booked_slots WHERE date = ?', (date,))
        local_busy_times = {row[0] for row in cursor.fetchall()}
    
    all_busy_times = busy_times.union(local_busy_times)
    return [time for time in AVAILABLE_HOURS if time not in all_busy_times]

def get_week_dates():
    """Получение дат на неделю вперед (только рабочие дни)"""
    today = datetime.now()
    dates = []
    for i in range(7):
        date = today + timedelta(days=i)
        if date.weekday() < 5:  # Только рабочие дни (0-4)
            dates.append(date.strftime("%d.%m.%Y"))
    return dates

def create_schedule_keyboard():
    """Создание клавиатуры с датами"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    dates = get_week_dates()
    buttons = [types.InlineKeyboardButton(date, callback_data=f"date_{date}") for date in dates]
    markup.add(*buttons)
    return markup

def create_time_keyboard(date):
    """Создание клавиатуры со временем"""
    markup = types.InlineKeyboardMarkup(row_width=3)
    available_slots = get_available_time_slots(date)
    
    if available_slots:
        buttons = [types.InlineKeyboardButton(hour, callback_data=f"time_{hour}") for hour in available_slots]
        markup.add(*buttons)
        back_btn = types.InlineKeyboardButton("◀️ Назад к датам", callback_data="schedule")
        markup.add(back_btn)
    else:
        no_slots_btn = types.InlineKeyboardButton("❌ Нет свободного времени", callback_data="no_action")
        back_btn = types.InlineKeyboardButton("◀️ Выбрать другую дату", callback_data="schedule")
        markup.add(no_slots_btn, back_btn)
    
    return markup

def save_receipt_file(bot, file_id, user_id, timestamp, file_type="photo"):
    """
    Сохранение файла чека (фото или PDF)
    file_type: тип файла ('photo' или 'document')
    """
    try:
        file_info = bot.get_file(file_id)
        if file_type == "photo":
            file_ext = file_info.file_path.split('.')[-1]
        else:  # для PDF
            file_ext = "pdf"
            
        filename = f"receipt_{user_id}_{timestamp.replace(' ', '_').replace(':', '-')}.{file_ext}"
        file_path = RECEIPTS_DIR / filename
        
        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        print(f"Файл сохранен: {file_path}")
        return str(file_path)
    except Exception as e:
        print(f"Ошибка при сохранении файла: {str(e)}")
        raise

def send_admin_notification(user_id, file_id, payment_info, file_type="photo"):
    """Отправка уведомления администратору"""
    try:
        # Получаем информацию о пользователе
        try:
            user = bot.get_chat_member(user_id, user_id).user
            user_info = f"{user.first_name}"
            if user.last_name:
                user_info += f" {user.last_name}"
            if user.username:
                user_info += f" (@{user.username})"
        except Exception as e:
            print(f"Ошибка при получении информации о пользователе: {str(e)}")
            user_info = f"ID: {user_id}"
        
        print(f"Отправка уведомления администратору {ADMIN_ID}")
        
        # Отправляем файл чека
        try:
            if file_type == "photo":
                sent_file = bot.send_photo(int(ADMIN_ID), file_id, caption="💳 Чек об оплате")
            else:  # для PDF
                sent_file = bot.send_document(int(ADMIN_ID), file_id, caption="💳 Чек об оплате (PDF)")
            
            if not sent_file:
                raise Exception("sent_file is None")
                
        except Exception as e:
            print(f"Ошибка отправки файла администратору: {str(e)}")
            return
            
        # Создаем клавиатуру для подтверждения/отклонения
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"admin_confirm_{payment_info['payment_id']}")
        btn2 = types.InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{payment_info['payment_id']}")
        markup.add(btn1, btn2)
        
        # Формируем текст уведомления
        admin_text = f"""💳 <b>Новый платеж!</b>

👤 <b>От:</b> {user_info}
🆔 <b>ID пользователя:</b> <code>{user_id}</code>
📝 <b>ID платежа:</b> {payment_info['payment_id']}
⏰ <b>Время отправки:</b> {payment_info['timestamp']}
📂 <b>Сохранено в:</b> {payment_info['local_path']}
📎 <b>Тип файла:</b> {'Фото' if file_type == 'photo' else 'PDF'}

Проверьте чек и подтвердите оплату."""
        
        try:
            # Отправляем информацию о платеже
            sent_message = bot.send_message(int(ADMIN_ID), admin_text, parse_mode="HTML", reply_markup=markup)
            
            if sent_message:
                print(f"Уведомление успешно отправлено администратору (ID: {ADMIN_ID})")
            else:
                print("Ошибка отправки сообщения администратору: sent_message is None")
                
        except Exception as e:
            print(f"Ошибка отправки текстового сообщения администратору: {str(e)}")
            
    except Exception as e:
        print(f"Общая ошибка при отправке уведомления администратору: {str(e)}")

def check_payment_status(user_id):
    """Проверка статуса оплаты пользователя"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT status FROM payments 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

@bot.message_handler(commands=["start", "main"])
def main(message):
    """Обработчик команды /start - главное меню"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📚 Пакеты занятий", callback_data="packages")
    btn2 = types.InlineKeyboardButton("💰 Оплата", callback_data="help")
    btn3 = types.InlineKeyboardButton("📅 Расписание", callback_data="schedule")
    btn4 = types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
    markup.add(btn1, btn2, btn3, btn4)
    
    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

Добро пожаловать в бот для записи на занятия! 🎓

📱 Выберите нужный раздел в меню ниже ⬇️"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """Обработчик всех callback-запросов от кнопок"""
    try:
        if call.data == "help":
            payment_text = """💳 <b>Способы оплаты</b>

🏦 <b>Банковская карта (monobank):</b>
<code>4441 1110 7175 4448</code>

💫 <i>Пожалуйста, отправьте скриншот чека об оплате.</i>
После подтверждения оплаты администратором, вам станет доступна запись на занятие."""
            
            bot.send_message(call.message.chat.id, payment_text, parse_mode="HTML")

        elif call.data == "packages":
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
            btn = types.InlineKeyboardButton("💰 Оплатить", callback_data="help")
            markup.add(btn)
            bot.send_message(call.message.chat.id, packages_text, parse_mode="HTML", reply_markup=markup)

        elif call.data == "contacts":
            user_id = str(call.from_user.id)
            payment_status = check_payment_status(user_id)
            
            base_contact_text = """📞 <b>Наши контакты</b>

📱 <b>Telegram:</b>
• Бот: @zno_nmt2025_bot
• Группа: @zno_ukraine2018

⏰ <b>Часы работы:</b>
Пн-Пт: 9:00 - 20:00

🎓 <b>Формат занятий:</b>
• Онлайн через Zoom
• Индивидуальный подход
• Интерактивные материалы"""

            if payment_status == "confirmed":
                contact_text = base_contact_text + """

🔗 <b>Ваша ссылка на Zoom:</b>
https://us05web.zoom.us/j/6281722803?pwd=TFNSSHpwSEhJMVVZY2NSRzUrcFkwdz09

✅ <i>Оплата подтверждена. Вы можете присоединиться к занятию по ссылке выше.</i>"""
            else:
                contact_text = base_contact_text + """

❗️ <i>Ссылка на Zoom будет доступна после подтверждения оплаты администратором.</i>"""
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            if payment_status != "confirmed":
                btn_payment = types.InlineKeyboardButton("💰 Оплатить", callback_data="help")
                markup.add(btn_payment)
            btn_schedule = types.InlineKeyboardButton("📅 Записаться на занятие", callback_data="schedule")
            markup.add(btn_schedule)
            
            bot.send_message(call.message.chat.id, contact_text, parse_mode="HTML", reply_markup=markup)

        elif call.data == "schedule":
            user_id = str(call.from_user.id)
            if user_id not in confirmed_payments:
                not_paid_text = """❌ <b>Запись недоступна</b>

Для записи на занятие необходимо:
1. Нажать кнопку "💰 Оплата"
2. Оплатить занятие
3. Отправить чек об оплате
4. Дождаться подтверждения от администратора"""
                
                markup = types.InlineKeyboardMarkup(row_width=1)
                btn = types.InlineKeyboardButton("💰 Оплата", callback_data="help")
                markup.add(btn)
                
                bot.send_message(call.message.chat.id, not_paid_text, parse_mode="HTML", reply_markup=markup)
                return

            markup = create_schedule_keyboard()
            schedule_text = """📅 <b>Выберите дату для занятия</b>

Доступны только рабочие дни (Пн-Пт)
Выберите удобную дату ⬇️"""
            bot.send_message(call.message.chat.id, schedule_text, parse_mode="HTML", reply_markup=markup)

        elif call.data.startswith("date_"):
            date = call.data.split("_")[1]
            user_id = call.from_user.id
            user_data[user_id] = {"date": date}
            markup = create_time_keyboard(date)
            time_text = f"""🕒 <b>Выберите время для занятия</b>

📅 Дата: {date}
Выберите удобное время из доступных слотов ⬇️"""
            bot.send_message(call.message.chat.id, time_text, parse_mode="HTML", reply_markup=markup)

        elif call.data.startswith("time_"):
            time = call.data.split("_")[1]
            user_id = call.from_user.id
            if user_id in user_data and "date" in user_data[user_id]:
                date = user_data[user_id]["date"]
                user_data[user_id].update({"time": time})
                
                # Проверяем статус оплаты
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                    SELECT id FROM payments 
                    WHERE user_id = ? AND status = 'confirmed' 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                    ''', (str(user_id),))
                    payment_result = cursor.fetchone()
                
                if payment_result:
                    payment_id = payment_result[0]
                    # Преобразуем дату и время в datetime объекты
                    try:
                        date_time_str = f"{date} {time}"
                        start_time = datetime.strptime(date_time_str, "%d.%m.%Y %H:%M")
                        end_time = start_time + timedelta(minutes=50)
                        
                        logger.info(f"Попытка добавления события в календарь: {date_time_str}")
                        
                        if calendar is None:
                            logger.error("Календарь не инициализирован")
                            bot.answer_callback_query(call.id, "Ошибка календаря. Обратитесь к администратору.")
                            return
                        
                        # Сохраняем в календарь
                        if calendar.add_event(start_time, end_time, user_id, payment_id):
                            # Сохраняем в базу данных
                            if save_booked_slot(date, time, str(user_id), payment_id):
                                confirmation_text = f"""✅ <b>Запись подтверждена!</b>

📅 <b>Дата:</b> {date}
🕒 <b>Время:</b> {time}
⏱ <b>Длительность:</b> 50 минут

💫 <i>Занятие добавлено в календарь. До встречи!</i>"""
                                
                                if ADMIN_ID:
                                    admin_text = f"""📝 <b>Новая запись на занятие!</b>

👤 Пользователь: {user_id}
📅 Дата: {date}
🕒 Время: {time}
💳 Платеж: #{payment_id}"""
                                    bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
                                
                                bot.edit_message_text(
                                    confirmation_text,
                                    call.message.chat.id,
                                    call.message.message_id,
                                    parse_mode="HTML"
                                )
                                logger.info(f"Успешно добавлено занятие: {date} {time}")
                            else:
                                error_text = """❌ <b>Ошибка бронирования</b>

Это время уже занято. Пожалуйста, выберите другое время."""
                                bot.edit_message_text(
                                    error_text,
                                    call.message.chat.id,
                                    call.message.message_id,
                                    parse_mode="HTML"
                                )
                                logger.warning(f"Время уже занято: {date} {time}")
                        else:
                            error_text = """❌ <b>Ошибка календаря</b>

Не удалось добавить занятие в календарь. Пожалуйста, попробуйте выбрать другое время или обратитесь к администратору."""
                            bot.edit_message_text(
                                error_text,
                                call.message.chat.id,
                                call.message.message_id,
                                parse_mode="HTML"
                            )
                            logger.error(f"Ошибка добавления в календарь: {date} {time}")
                    except Exception as e:
                        logger.error(f"Ошибка при обработке даты/времени: {str(e)}")
                        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")
                else:
                    bot.edit_message_text(
                        """❌ <b>Ошибка бронирования</b>

Не найден подтвержденный платеж. Пожалуйста, сначала оплатите занятие.""",
                        call.message.chat.id,
                        call.message.message_id,
                        parse_mode="HTML"
                    )
                    logger.warning(f"Попытка записи без оплаты: user_id={user_id}")

        elif call.data.startswith("admin_confirm_"):
            if str(call.from_user.id) == ADMIN_ID:
                payment_id = int(call.data.split("_")[2])
                update_payment_status(payment_id, "confirmed")
                
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM payments WHERE id = ?', (payment_id,))
                    result = cursor.fetchone()
                    if result:
                        user_id = result[0]
                        confirm_text = """✅ <b>Оплата подтверждена!</b>

💫 Теперь вам доступны:
• Запись на занятия
• Ссылка на Zoom
• Доступ к материалам

Чтобы начать, выберите удобное время в расписании ⬇️"""
                        
                        markup = types.InlineKeyboardMarkup(row_width=1)
                        btn = types.InlineKeyboardButton("📅 Расписание", callback_data="schedule")
                        markup.add(btn)
                        
                        # Отправляем сообщение пользователю
                        bot.send_message(user_id, confirm_text, parse_mode="HTML", reply_markup=markup)
                        
                        # Отправляем подтверждение администратору
                        admin_confirm_text = f"""✅ <b>Платеж #{payment_id} подтвержден</b>

Уведомление отправлено пользователю."""
                        bot.answer_callback_query(call.id, "Оплата подтверждена")
                        bot.edit_message_text(admin_confirm_text, 
                                            call.message.chat.id, 
                                            call.message.message_id, 
                                            parse_mode="HTML")
                        
                        confirmed_payments.add(user_id)

        elif call.data.startswith("admin_reject_"):
            if str(call.from_user.id) == ADMIN_ID:
                payment_id = int(call.data.split("_")[2])
                update_payment_status(payment_id, "rejected")
                
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT user_id FROM payments WHERE id = ?', (payment_id,))
                    result = cursor.fetchone()
                    if result:
                        user_id = result[0]
                        reject_text = """❌ <b>Оплата отклонена</b>

Возможные причины:
• Некорректная сумма
• Нечитаемый чек
• Ошибка в реквизитах

Пожалуйста, проверьте правильность оплаты и отправьте чек повторно."""
                        
                        markup = types.InlineKeyboardMarkup(row_width=1)
                        btn = types.InlineKeyboardButton("💰 Оплатить", callback_data="help")
                        markup.add(btn)
                        
                        # Отправляем сообщение пользователю
                        bot.send_message(user_id, reject_text, parse_mode="HTML", reply_markup=markup)
                        
                        # Отправляем подтверждение администратору
                        admin_reject_text = f"""❌ <b>Платеж #{payment_id} отклонен</b>

Уведомление отправлено пользователю."""
                        bot.answer_callback_query(call.id, "Оплата отклонена")
                        bot.edit_message_text(admin_reject_text, 
                                            call.message.chat.id, 
                                            call.message.message_id, 
                                            parse_mode="HTML")

    except Exception as e:
        logger.error(f"Ошибка в обработчике callback: {str(e)}")
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")

@bot.message_handler(content_types=['photo', 'document'])
def handle_payment_receipt(message):
    """Обработчик фотографий и PDF-файлов (чеков об оплате)"""
    try:
        user_id = str(message.from_user.id)
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Определяем тип файла и получаем file_id
        if message.photo:  # Если прислали фото
            file_id = message.photo[-1].file_id
            file_type = "photo"
        elif message.document and message.document.mime_type == 'application/pdf':  # Если прислали PDF
            file_id = message.document.file_id
            file_type = "document"
        else:  # Если прислали другой тип файла
            bot.reply_to(message, """❌ <b>Неподдерживаемый формат файла</b>

Пожалуйста, отправьте чек в виде фотографии или PDF-файла.""", parse_mode="HTML")
            return
        
        print(f"Получен чек от пользователя {user_id} (тип: {file_type})")
        
        # Сохраняем файл
        local_path = save_receipt_file(bot, file_id, user_id, timestamp, file_type)
        payment_id = save_payment_to_db(user_id, file_id, local_path, timestamp)
        
        # Отправляем уведомление администратору
        payment_info = {
            "payment_id": payment_id,
            "timestamp": timestamp,
            "local_path": local_path
        }
        
        send_admin_notification(user_id, file_id, payment_info, file_type)
        
        # Отправляем подтверждение пользователю
        confirmation_markup = types.InlineKeyboardMarkup(row_width=2)
        cancel_btn = types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_payment_{payment_id}")
        confirmation_markup.add(cancel_btn)
        
        bot.reply_to(message, """✅ <b>Чек получен!</b>

⏳ Ожидайте подтверждения от администратора.
Мы уведомим вас о результате проверки.""", 
                    parse_mode="HTML",
                    reply_markup=confirmation_markup)
                    
    except Exception as e:
        error_message = f"Ошибка при обработке чека: {str(e)}"
        print(error_message)
        bot.reply_to(message, """❌ <b>Произошла ошибка при сохранении чека</b>

Пожалуйста, попробуйте отправить чек еще раз.""", parse_mode="HTML")
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"❌ Ошибка при сохранении чека от {user_id}: {str(e)}")

@bot.message_handler(commands=['myid'])
def send_user_id(message):
    """Отправляет ID пользователя"""
    user_id = message.from_user.id
    bot.reply_to(message, f"🆔 Ваш ID: `{user_id}`", parse_mode="Markdown")

# Запуск бота
bot.polling(none_stop=True)