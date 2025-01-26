import sqlite3

DATABASE_NAME = "reminders.db"
TABLE_NAME = "context_table"

class ContextDB:
    def __init__(self, db_name=DATABASE_NAME):
        self.db_name = db_name
        self.initialize_database()

    def initialize_database(self):
        """
        Создаёт базу данных и таблицу, если она отсутствует.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time_of_day TEXT NOT NULL,
                    description TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_context(self, time_of_day: str, description: str):
        """
        Добавляет новую запись в таблицу контекста.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (time_of_day, description)
                VALUES (?, ?)
            """, (time_of_day, description))
            conn.commit()
            return cursor.lastrowid  # Возвращаем ID новой записи

    def get_context_by_time(self, current_hour: int):
        """
        Возвращает записи контекста для заданного времени суток.
        """
        if 5 <= current_hour < 12:
            time_of_day = "morning"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon"
        elif 17 <= current_hour < 23:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, time_of_day, description FROM {TABLE_NAME} WHERE time_of_day = ?", (time_of_day,))
            return cursor.fetchall()

    def get_all_context(self):
        """
        Возвращает все записи из таблицы контекста.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, time_of_day, description FROM {TABLE_NAME}")
            return cursor.fetchall()

    def delete_context(self, context_id: int):
        """
        Удаляет запись из таблицы контекста по ID.
        """
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                DELETE FROM {TABLE_NAME}
                WHERE id = ?
            """, (context_id,))
            conn.commit()
            return cursor.rowcount  # Количество удалённых строк
