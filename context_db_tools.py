import sqlite3

DATABASE_NAME = "reminders.db"
TABLE_NAME = "context_table"

# Инициализация базы данных
def initialize_database():
    """
    Создаёт базу данных и таблицу, если она отсутствует.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_of_day TEXT NOT NULL,
                description TEXT NOT NULL
            )
        """)
        conn.commit()

# Чтение данных из таблицы
def read_context_table() -> list:
    """
    Читает все данные из таблицы контекста.

    Returns:
        list: Список записей из таблицы.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, time_of_day, description FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        return rows

# Добавление новой записи в таблицу
def write_to_context_table(time_of_day: str, description: str) -> str:
    """
    Добавляет новую запись в таблицу контекста.

    Args:
        time_of_day (str): Время суток (утро, день, вечер, ночь).
        description (str): Описание задачи или условия.

    Returns:
        str: Сообщение об успехе.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} (time_of_day, description)
            VALUES (?, ?)
        """, (time_of_day, description))
        conn.commit()
        return "Запись успешно добавлена."

# Удаление записи из таблицы
def delete_from_context_table(condition: str) -> str:
    """
    Удаляет записи из таблицы контекста, соответствующие условию.

    Args:
        condition (str): Условие удаления (например, часть описания).

    Returns:
        str: Сообщение об успехе.
    """
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            DELETE FROM {TABLE_NAME}
            WHERE description LIKE ?
        """, (f"%{condition}%",))
        conn.commit()
        return "Записи успешно удалены."

# Автоматическая инициализация при импорте
initialize_database()
