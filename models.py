# models.py

class User:
    def __init__(self, id, email, name, is_admin=False, blocked=False):
        self.id = id
        self.email = email
        self.name = name
        self.is_admin = is_admin
        self.blocked = blocked

class Category:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Dish:
    def __init__(self, id, title, description, price, category_id, image, is_veg=False, is_spicy=False):
        self.id = id
        self.title = title
        self.description = description
        self.price = price
        self.category_id = category_id
        self.image = image
        self.is_veg = is_veg
        self.is_spicy = is_spicy

class Order:
    def __init__(self, id, user_id, address, phone, status, delivery_time, payment_method, created_at):
        self.id = id
        self.user_id = user_id
        self.address = address
        self.phone = phone
        self.status = status
        self.delivery_time = delivery_time
        self.payment_method = payment_method
        self.created_at = created_at

class Review:
    def __init__(self, id, user_id, dish_id, rating, text, created_at):
        self.id = id
        self.user_id = user_id
        self.dish_id = dish_id
        self.rating = rating
        self.text = text
        self.created_at = created_at