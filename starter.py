import os
import sqlite3
import time
from datetime import datetime, timezone
from RealtimeTTS import TextToAudioStream, SystemEngine
from RealtimeSTT import AudioToTextRecorder
from HuggingFaceTTSEngine import RussianTTSEngine, AutoSystemEngine
from calendar_tools import Calendar
import asyncio
from langchain.tools import tool

# Настройка соединения с базой данных
def connect_db(db_name="reminders.db"):
    return sqlite3.connect(db_name)

# Создание базы данных и таблицы, если она не существует
def create_db_and_table():
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_calendar_id TEXT,
                summary TEXT NOT NULL,
                description TEXT,
                notification_time TEXT NOT NULL,
                status INTEGER DEFAULT 0
            )
        """)
        conn.commit()

# Проверка на наличие незавершенных записей
def check_pending_tasks():
    current_timestamp = datetime.now(timezone.utc).astimezone().isoformat()
    with connect_db() as conn:
        cursor = conn.cursor()

        # Выбираем записи с notification_time <= текущего времени и статусом 0
        cursor.execute("""
            SELECT id, google_calendar_id, summary, notification_time FROM reminders
            WHERE notification_time <= ? AND status = 0
            ORDER BY notification_time ASC
        """, (current_timestamp,))

        return cursor.fetchall()

# Добавление новой записи в таблицу
def add_task(google_calendar_id, summary, description, notification_time):
    with connect_db() as conn:
        cursor = conn.cursor()
        # Проверяем наличие записи с такими же параметрами
        cursor.execute("""
            SELECT 1 FROM reminders
            WHERE google_calendar_id = ? AND summary = ? AND description = ? AND notification_time = ?
        """, (google_calendar_id, summary, description, notification_time))

        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO reminders (google_calendar_id, summary, description, notification_time, status)
                VALUES (?, ?, ?, ?, 0)
            """, (google_calendar_id, summary, description, notification_time))
            conn.commit()
            print(f"Task added: {summary} with notification time {notification_time}")

# Удаление записей по google_calendar_id
def delete_tasks_by_google_id(google_calendar_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM reminders
            WHERE google_calendar_id = ?
        """, (google_calendar_id,))
        conn.commit()
        print(f"Tasks with Google Calendar ID {google_calendar_id} deleted.")

# Обновление статуса задачи на завершенную
def mark_task_as_done(task_id):
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE reminders
            SET status = 1
            WHERE id = ?
        """, (task_id,))
        conn.commit()

# Синхронизация с Google Календарем
def sync_with_calendar(calendar_instance):
    calendar_events = calendar_instance.calendar_get_task()  # Получаем события из календаря
    with connect_db() as conn:
        cursor = conn.cursor()

        # Получаем все google_calendar_id из локальной базы
        cursor.execute("""
            SELECT DISTINCT google_calendar_id, summary, description, notification_time FROM reminders
        """)
        local_records = cursor.fetchall()

        local_data = {}
        for record in local_records:
            google_calendar_id, summary, description, notification_time = record
            if google_calendar_id not in local_data:
                local_data[google_calendar_id] = []
            local_data[google_calendar_id].append({
                'summary': summary,
                'description': description,
                'notification_time': notification_time,
            })

        for event in calendar_events:
            google_calendar_id = event['google_calendar_id']

            # Уведомления или начало события
            notification_times = event['notification_times'] if event['notification_times'] != ['No reminders set for this event'] else [event['start']]
            updated_data = [{'summary': event['summary'], 'description': event['description'], 'notification_time': nt} for nt in notification_times]

            # Преобразование времени в ISO 8601 для сравнения
            updated_data = [
                {
                    'summary': d['summary'],
                    'description': d['description'],
                    'notification_time': datetime.fromisoformat(d['notification_time']).isoformat()
                }
                for d in updated_data
            ]

            # Проверяем изменения
            if local_data.get(google_calendar_id) == updated_data:
                continue  # Пропускаем, если данные совпадают

            # Удаляем старые записи об этом мероприятии
            delete_tasks_by_google_id(google_calendar_id)

            # Добавляем новые записи
            for notification_time in notification_times:
                add_task(
                    google_calendar_id,
                    event['summary'],
                    event['description'],
                    notification_time)

# Инициализация Text-to-Speech
stream = TextToAudioStream(
    AutoSystemEngine(),
    log_characters=False,
)

# Основной скрипт
if __name__ == "__main__":
    db_name = "reminders.db"  # Имя вашей базы данных
    calendar_instance = Calendar()  # Создаем экземпляр класса Calendar

    print("Starting the background task checker...")

    create_db_and_table()  # Создаем таблицу, если ее нет

    last_calendar_sync_time = 0  # Время последней синхронизации с календарем

    while True:
        start_time = time.time()

        # Проверяем невыполненные задачи каждую минуту
        tasks = check_pending_tasks()

        if tasks:
            stream.feed(['Напоминание']).play()
        
        for task in tasks:
            task_id, google_calendar_id, summary, notification_time = task
            print(f"[NOTIFICATION] {summary} (Notification Time: {notification_time})")

            # Озвучиваем summary
            stream.feed([summary]).play()

            # Отмечаем задачу как завершенную
            mark_task_as_done(task_id)

        # Синхронизируем с Google Календарем каждые 30 минут
        if time.time() - last_calendar_sync_time >= 180:  # 30 минут = 1800 секунд
            sync_with_calendar(calendar_instance)
            last_calendar_sync_time = time.time()

        # Рассчитываем оставшееся время до 1 секунды
        elapsed_time = time.time() - start_time
        if elapsed_time < 1:
            time.sleep(1 - elapsed_time)
