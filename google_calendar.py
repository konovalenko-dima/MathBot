from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os.path
import pickle

# Если изменить эти области, удалите файл token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    creds = None
    # Файл token.pickle хранит токены доступа и обновления пользователя
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # Если нет действительных учетных данных, позволяем пользователю войти
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Сохраняем учетные данные для следующего запуска
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)

def create_event(start_time, end_time, user_id, payment_id):
    """Создает событие в Google Calendar."""
    service = get_calendar_service()
    
    event = {
        'summary': f'Занятие с учеником (ID: {user_id})',
        'description': f'Платеж ID: {payment_id}',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Kiev',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Kiev',
        },
        'reminders': {
            'useDefault': True
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event['id']
    except Exception as e:
        print(f'Ошибка при создании события: {e}')
        return None

def delete_event(event_id):
    """Удаляет событие из Google Calendar."""
    service = get_calendar_service()
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        return True
    except Exception as e:
        print(f'Ошибка при удалении события: {e}')
        return False

def get_busy_slots(start_date, end_date):
    """Получает занятые слоты из Google Calendar."""
    service = get_calendar_service()
    
    # Получаем временные границы для проверки
    start_datetime = datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z'
    end_datetime = datetime.combine(end_date, datetime.max.time()).isoformat() + 'Z'
    
    body = {
        "timeMin": start_datetime,
        "timeMax": end_datetime,
        "items": [{"id": "primary"}]
    }
    
    events_result = service.freebusy().query(body=body).execute()
    busy_slots = events_result['calendars']['primary']['busy']
    
    return busy_slots 