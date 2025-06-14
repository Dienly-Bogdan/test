import sqlite3

email = input("Введите ваш email, для получения Админ-прав: ") 

conn = sqlite3.connect("pasta_pizza.db")
c = conn.cursor()
c.execute("UPDATE users SET is_admin=1 WHERE email=?", (email,))
conn.commit()
conn.close()
print("Готово! Теперь вы админ.")