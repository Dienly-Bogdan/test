import sqlite3

DB_PATH = "pasta_pizza.db"   # Путь к вашей базе данных

# Добавьте свои категории сюда
categories = [
    "Пицца",
    "Паста",
    "Салаты",
    "Напитки",
    "Десерты"
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Создать таблицу, если её нет
cur.execute("""
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")

# Проверить, есть ли уже такие категории (чтобы не дублировать)
cur.execute("SELECT name FROM categories")
existing = set(row[0] for row in cur.fetchall())

added = 0
for cat in categories:
    if cat not in existing:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        added += 1

conn.commit()
conn.close()

print(f"Добавлено новых категорий: {added}")