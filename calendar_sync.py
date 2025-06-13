import subprocess
from datetime import datetime, timedelta
import os
import pytz
import logging
from typing import Optional, Set, Dict, Any

logger = logging.getLogger(__name__)

class CalendarSync:
    def __init__(self, calendar_name: str = "Tutoring"):
        """
        Инициализация синхронизации с календарем macOS
        calendar_name: имя календаря для синхронизации
        """
        self.calendar_name = calendar_name
        self.timezone = pytz.timezone('Europe/Kiev')
        self._ensure_calendar_exists()

    def _run_applescript(self, script: str) -> Optional[str]:
        """Выполняет AppleScript и возвращает результат"""
        try:
            process = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, 
                                  text=True)
            if process.returncode != 0:
                logger.error(f"AppleScript error: {process.stderr}")
                return None
            return process.stdout.strip()
        except Exception as e:
            logger.error(f"Error running AppleScript: {str(e)}")
            return None

    def _ensure_calendar_exists(self) -> None:
        """Проверяет существование календаря и создает его при необходимости"""
        # Проверяем список календарей
        check_script = '''
        tell application "Calendar"
            return name of calendars
        end tell
        '''
        calendars = self._run_applescript(check_script)
        logger.info(f"Доступные календари: {calendars}")
        
        # Создаем новый календарь
        create_script = '''
        tell application "Calendar"
            if not (exists calendar "Tutoring") then
                make new calendar with properties {name:"Tutoring"}
            end if
            
            tell calendar "Tutoring"
                set its color to {65535, 65535, 0}
            end tell
            
            return "success"
        end tell
        '''
        
        result = self._run_applescript(create_script)
        if result == "success":
            logger.info("Календарь Tutoring успешно создан/обновлен")
        else:
            logger.error("Ошибка при создании календаря Tutoring")
            
        # Проверяем, что календарь появился
        verify_script = '''
        tell application "Calendar"
            if exists calendar "Tutoring" then
                return "exists"
            else
                return "not found"
            end if
        end tell
        '''
        
        verify_result = self._run_applescript(verify_script)
        if verify_result == "exists":
            logger.info("Календарь Tutoring успешно проверен")
        else:
            logger.error("Календарь Tutoring не найден после создания")

    def _format_date(self, dt: datetime) -> str:
        """Форматирует дату для AppleScript"""
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        return dt.strftime("%Y-%m-%d")

    def _format_time(self, dt: datetime) -> str:
        """Форматирует время для AppleScript"""
        if dt.tzinfo is None:
            dt = self.timezone.localize(dt)
        return dt.strftime("%H:%M")

    def add_event(self, start_time: datetime, end_time: datetime, user_id: str, payment_id: str) -> bool:
        """Добавляет событие в календарь"""
        try:
            if self.is_time_slot_busy(start_time):
                logger.warning(f"Время уже занято: {start_time}")
                return False

            # Форматируем даты для AppleScript
            start_date = start_time.strftime("%Y-%m-%d")
            start_hour = start_time.strftime("%H")
            start_minute = start_time.strftime("%M")
            
            end_date = end_time.strftime("%Y-%m-%d")
            end_hour = end_time.strftime("%H")
            end_minute = end_time.strftime("%M")
            
            logger.info(f"Попытка создания события: {start_date} {start_hour}:{start_minute} - {end_date} {end_hour}:{end_minute}")
            
            script = f'''
            tell application "Calendar"
                try
                    tell calendar "Tutoring"
                        -- Создаем даты начала и конца
                        set startDate to current date
                        set year of startDate to {start_time.year} as integer
                        set month of startDate to {start_time.month} as integer
                        set day of startDate to {start_time.day} as integer
                        set hours of startDate to {start_hour} as integer
                        set minutes of startDate to {start_minute} as integer
                        set seconds of startDate to 0
                        
                        set endDate to current date
                        set year of endDate to {end_time.year} as integer
                        set month of endDate to {end_time.month} as integer
                        set day of endDate to {end_time.day} as integer
                        set hours of endDate to {end_hour} as integer
                        set minutes of endDate to {end_minute} as integer
                        set seconds of endDate to 0
                        
                        -- Создаем событие
                        set newEvent to make new event with properties {{summary:"🎓 Урок | Ученик #{user_id}", description:"📝 Детали урока:\\n👤 ID ученика: {user_id}\\n💳 ID платежа: {payment_id}", start date:startDate, end date:endDate}}
                        
                        -- Добавляем напоминание за час
                        tell newEvent
                            make new sound alarm with properties {{trigger interval:-3600}}
                        end tell
                        
                        return "success:" & id of newEvent
                    end tell
                on error errMsg
                    return "error:" & errMsg
                end try
            end tell
            '''
            
            result = self._run_applescript(script)
            if result and result.startswith("success:"):
                event_id = result.split(":", 1)[1]
                logger.info(f"Событие успешно создано (ID: {event_id}) на {start_time}")
                return True
            else:
                error_msg = result.split(":", 1)[1] if result and result.startswith("error:") else "неизвестная ошибка"
                logger.error(f"Не удалось создать событие: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при создании события: {str(e)}")
            return False

    def is_time_slot_busy(self, time: datetime) -> bool:
        """Проверяет, занято ли указанное время"""
        try:
            date_str = time.strftime("%Y-%m-%d")
            time_str = time.strftime("%H:%M")
            
            script = f'''
            tell application "Calendar"
                tell calendar "Tutoring"
                    set checkDate to current date
                    set year of checkDate to {time.year}
                    set month of checkDate to {time.month}
                    set day of checkDate to {time.day}
                    set hours of checkDate to {time.hour}
                    set minutes of checkDate to {time.minute}
                    set seconds of checkDate to 0
                    
                    set dayStart to checkDate
                    set hours of dayStart to 0
                    set minutes of dayStart to 0
                    
                    set dayEnd to checkDate
                    set hours of dayEnd to 23
                    set minutes of dayEnd to 59
                    
                    set existingEvents to (every event whose start date ≥ dayStart and start date ≤ dayEnd)
                    repeat with existingEvent in existingEvents
                        if hours of (start date of existingEvent) is {time.hour} and minutes of (start date of existingEvent) is {time.minute} then
                            return "busy"
                        end if
                    end repeat
                    return "free"
                end tell
            end tell
            '''
            
            result = self._run_applescript(script)
            return result == "busy"

        except Exception as e:
            logger.error(f"Ошибка при проверке слота: {str(e)}")
            return True  # В случае ошибки считаем слот занятым

    def get_busy_slots(self, date: datetime.date) -> Set[str]:
        """Получает список занятых слотов на указанную дату"""
        try:
            script = f'''
            tell application "Calendar"
                tell calendar "Tutoring"
                    set checkDate to current date
                    set year of checkDate to {date.year}
                    set month of checkDate to {date.month}
                    set day of checkDate to {date.day}
                    set hours of checkDate to 0
                    set minutes of checkDate to 0
                    set seconds of checkDate to 0
                    
                    set dayStart to checkDate
                    set dayEnd to checkDate
                    set hours of dayEnd to 23
                    set minutes of dayEnd to 59
                    
                    set busySlots to {{}}
                    set existingEvents to (every event whose start date ≥ dayStart and start date ≤ dayEnd)
                    repeat with existingEvent in existingEvents
                        set eventHour to text -2 thru -1 of ("0" & ((hours of (start date of existingEvent)) as text))
                        set eventMinute to text -2 thru -1 of ("0" & ((minutes of (start date of existingEvent)) as text))
                        set end of busySlots to (eventHour & ":" & eventMinute)
                    end repeat
                    return busySlots
                end tell
            end tell
            '''
            
            result = self._run_applescript(script)
            busy_times = set()
            
            if result and result != "{}":
                times = result.split(", ")
                for time_str in times:
                    time_str = time_str.strip().strip('{}')
                    if ":" in time_str:
                        try:
                            hour, minute = map(int, time_str.split(":"))
                            formatted_time = f"{hour:02d}:{minute:02d}"
                            busy_times.add(formatted_time)
                        except ValueError:
                            continue

            logger.info(f"Занятые слоты на {date}: {sorted(list(busy_times))}")
            return busy_times

        except Exception as e:
            logger.error(f"Ошибка при получении занятых слотов: {str(e)}")
            return set()

    def delete_event(self, event_id):
        """
        Удаляет событие из календаря по его ID
        event_id: ID события для удаления
        """
        try:
            cmd = f'''
            osascript -e '
            tell application "Calendar"
                tell calendar "{self.calendar_name}"
                    delete event id "{event_id}"
                end tell
            end tell'
            '''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Ошибка при удалении события: {str(e)}")
            return False 