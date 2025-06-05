# Пиццерия — заказ пиццы и пасты на Flask

Это учебное приложение для онлайн-заказа еды. Вы можете:
- Смотреть меню по категориям
- Добавлять блюда в корзину и оформлять заказ
- Оставлять отзывы к блюдам
- Регистрироваться и авторизовываться
- Управлять меню, категориями и заказами в админ-панели

---

## Установка и запуск (подробная инструкция)

### 1. Клонирование репозитория

```sh
git clone https://github.com/Dienly-Bogdan/test.git
cd test
```

### 2. Создание и активация виртуального окружения (рекомендуется)

#### Windows

```sh
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux

```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```sh
pip install -r requirements.txt
```

### 4. Инициализация базы данных

**Внимание:**  
База данных создаётся по структуре из файла `schema.sql`.  
Если вы уже создавали базу ранее — этот шаг можно пропустить.

#### Через flask CLI

**Windows (PowerShell):**
```sh
$env:FLASK_APP = "app.py"
python -m flask init-db
```

**Windows (cmd):**
```cmd
set FLASK_APP=app.py
python -m flask init-db
```

**macOS/Linux:**
```sh
export FLASK_APP=app.py
flask init-db
```

#### Если flask CLI не работает

- Откройте SQLite Browser (или любой SQLite-клиент)
- Создайте файл базы данных `pasta_pizza.db` (или с нужным именем)
- Вставьте содержимое `schema.sql` и выполните

### 5. Запуск приложения

```sh
python app.py
```
По умолчанию сайт откроется на: [http://localhost:8088](http://localhost:8088)

---

## Доступ к приложению

- Главная страница: [http://localhost:8088/](http://localhost:8088/)
- Меню: [http://localhost:8088/menu](http://localhost:8088/menu)
- Корзина: [http://localhost:8088/cart](http://localhost:8088/cart)
- Регистрация: [http://localhost:8088/register](http://localhost:8088/register)
- Вход: [http://localhost:8088/login](http://localhost:8088/login)

---

## Админ-панель

> **Админ-панель доступна только для пользователей с флагом is_admin=1 в базе данных.**

- Панель администратора: [http://localhost:8088/admin/dashboard](http://localhost:8088/admin/dashboard)
- Управление блюдами: [http://localhost:8088/admin/manage_menu](http://localhost:8088/admin/manage_menu)
- Добавить блюдо: [http://localhost:8088/admin/add_dish](http://localhost:8088/admin/add_dish)
- Управление категориями: [http://localhost:8088/admin/manage_categories](http://localhost:8088/admin/manage_categories)
- Управление заказами: [http://localhost:8088/admin/manage_orders](http://localhost:8088/admin/manage_orders)

### Как сделать себя админом

После регистрации пользователя вручную измените поле `is_admin` на 1 в таблице `users` вашей базы данных (например, через SQLite Browser).

---

## Структура проекта

- `app.py` — Flask-приложение, все маршруты и логика
- `database.py` — подключение к базе данных и вспомогательные функции
- `schema.sql` — структура базы данных SQLite
- `requirements.txt` — зависимости Python
- `templates/` — все HTML-шаблоны (обязательны: `base.html`, `index.html`, `menu.html`, `cart.html`, `order.html`, `dish_detail.html`, шаблоны для админки)
- `static/` — стили, картинки, JS (здесь же папка `uploads` для фоток блюд)

---

## Примечания

- Если шаблон не найден (ошибка `TemplateNotFound`), убедитесь что файл с нужным именем лежит в папке `templates`.
- Если возникает ошибка “no such table”, убедитесь, что вы выполнили инициализацию БД.
- Для загрузки картинок блюда создайте папку `static/uploads`.

---

## Лицензия

MIT или любая другая по вашему выбору.