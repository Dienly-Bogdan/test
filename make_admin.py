import sqlite3

email = "admin@list.ru"  # <-- ВПИШИ свой email

conn = sqlite3.connect("pasta_pizza.db")
c = conn.cursor()
c.execute("UPDATE users SET is_admin=1 WHERE email=?", (email,))
conn.commit()
conn.close()
print("Готово! Теперь вы админ.")