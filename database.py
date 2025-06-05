import sqlite3
from models import User, Dish

class Database:
    @staticmethod
    def initialize():
        conn = sqlite3.connect('pasta_pizza.db')
        cursor = conn.cursor()
        with open('schema.sql', 'r') as f:
            cursor.executescript(f.read())
        conn.commit()
        conn.close()

    @staticmethod
    def register_user(username, email, password):
        conn = sqlite3.connect('pasta_pizza.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return False
        cursor.execute('INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)',
                       (username, email, password, False))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def authenticate_user(username, password):
        conn = sqlite3.connect('pasta_pizza.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, is_admin FROM users WHERE username = ? AND password = ?', (username, password))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(id=row[0], username=row[1], email=row[2], is_admin=bool(row[3]))
        return None

    @staticmethod
    def get_all_dishes():
        conn = sqlite3.connect('pasta_pizza.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, description, price, category FROM dishes')
        dishes = [Dish(id=row[0], name=row[1], description=row[2], price=row[3], category=row[4]) for row in cursor.fetchall()]
        conn.close()
        return dishes
