from datetime import datetime
import json
import sqlite3
import os
import re


class Database:
    def __init__(self, db_name):
        self._connection = sqlite3.connect(db_name)

    def close(self):
        self._connection.close()

    def _execute(self, query, params=None, commit=False):
        with self._connection:
            cursor = self._connection.cursor()
            query_result = cursor.execute(query, params or [])
            if commit:
                self._connection.commit()
            return cursor if not commit else query_result


class UserDatabase(Database):
    def __init__(self):
        super().__init__("Databse_for_Shop.db")
        self._create_tables()
        self._populate_with_sample_products()

    def _create_tables(self):
        with self._connection:
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    Login TEXT,
                    Password TEXT
                )
            """)
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT,
                    quantity INTEGER,
                    price REAL
                )
            """)

            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS cart (
                    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_login TEXT,
                    product_id INTEGER,
                    quantity INTEGER,
                    FOREIGN KEY (user_login) REFERENCES users (Login),
                    FOREIGN KEY (product_id) REFERENCES products (product_id)
                )
            """)

        with self._connection:
            self._connection.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_login TEXT,
                    address TEXT,
                    order_time TEXT,
                    FOREIGN KEY (user_login) REFERENCES users (Login)
                )
            """)

    def _populate_with_sample_products(self):
        sample_products = [
            ('Молоко', 10, 50.0),
            ('Хлеб', 20, 25.5),
            ('Яблоки', 30, 70.3),
            ('Макароны', 15, 45.9),
            ('Цыпленок', 8, 120.0),
        ]

        # Проверка, пуста ли таблица продуктов
        with self._connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM products")
            if cur.fetchone()[0] == 0:  # если таблица пуста, добавляем продукты
                cur.executemany("INSERT INTO products (product_name, quantity, price) VALUES (?, ?, ?)",
                                sample_products)
                print("Таблица продуктов была заполнена случайными товарами.")


    def _add_product(self, product_name, quantity, price):
        with self._connection:
            self._connection.execute("INSERT INTO products (product_name, quantity, price) VALUES (?, ?, ?)",
                                    (product_name, quantity, price))
        print("\nПродукт успешно добавлен.")

    def add_to_cart(self, login, product_id, quantity):
        with self._connection as conn:
            cur = conn.cursor()

            # Проверка, достаточное ли количество товара на складе
            cur.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
            product_data = cur.fetchone()

            if product_data and product_data[0] >= quantity:
                # Вычитаем заказанное количество из количества на складе и обновляем таблицу продуктов
                new_quantity = product_data[0] - quantity
                cur.execute("UPDATE products SET quantity = ? WHERE product_id = ?", (new_quantity, product_id))

                # Добавляем заказанный товар в корзину пользователя
                cur.execute("INSERT INTO cart (user_login, product_id, quantity) VALUES (?, ?, ?)",
                            (login, product_id, quantity))
                print("\nПродукт добавлен в корзину.")
                conn.commit()  # Подтверждаем изменения в базе данных
            else:
                print("\nНедостаточное количество товара на складе или товар не найден.")

    def add_user(self, login, password):
        with self._connection:
            self._connection.execute("INSERT INTO users (Login, Password) VALUES (?, ?)", (login, password))
        print("\nПользователь успешно зарегистрирован.")

    def authenticate_user(self, login, password):
        with self._connection:
            user_data = self._connection.execute("SELECT * FROM users WHERE Login=? AND Password=?", (login, password)).fetchone()
        if user_data:
            print("\nВход выполнен успешно.")
            return True
        else:
            print("\nНеверные учетные данные.")
            return False

    def _view_products(self, login):
        with self._connection:
            product_list = self._connection.execute("SELECT * FROM products").fetchall()
        print("\nСписок товаров:")
        for product in product_list:
            print(f"ID: {product[0]}, Название: {product[1]}, Количество: {product[2]}, Цена: {product[3]}")

        print("\nВыберите действие:")
        print("1. Добавить товар в корзину")
        print("2. Выйти назад")
        choice = input()
        if choice == "1":
            product_id = int(input("Введите ID продукта для добавления в корзину: "))  # Приводим к int
            quantity = int(input("Введите количество: "))  # Приводим к int

            with self._connection as conn:
                cur = conn.cursor()
                cur.execute("SELECT quantity FROM products WHERE product_id = ?", (product_id,))
                result = cur.fetchone()
                if not result:
                    print("\nПродукт не найден.")
                    return
                if result[0] < quantity:
                    print("\nТакого количества товара нет на складе.")
                    return
                self.add_to_cart(login, product_id, quantity)
        elif choice == "2":
            return
        else:
            print("\nНекорректный ввод. Пожалуйста, попробуйте снова.")

    def _view_orders(self, login):
        # For simplicity, we fetch the cart, but in a real scenario, it should fetch actual orders
        print(f"\nСписок заказов (товаров в корзине) пользователя {login}:")
        with self._connection as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT p.product_name, c.quantity, p.price
                FROM cart c
                JOIN products p ON p.product_id = c.product_id
                WHERE c.user_login = ?""", (login,))
            orders = cur.fetchall()
            if orders:
                for product_name, quantity, price in orders:
                    print(f"Продукт: {product_name}, Количество: {quantity}, Цена за штуку: {price}")
            else:
                print("Ваша корзина пуста.")

    def _checkout_cart(self, login, address):
        with self._connection as conn:
            cur = conn.cursor()

            cur.execute("SELECT count(*) FROM cart WHERE user_login=?", (login,))
            num_items_in_cart = cur.fetchone()[0]

            if num_items_in_cart == 0:
                print("\nНевозможно оформить заказ: ваша корзина пуста.")
                return None  # Возврат None указывает на отсутствие созданного заказа

            cur.execute("INSERT INTO orders (user_login, address, order_time) VALUES (?, ?, datetime('now'))",
                        (login, address))
            order_id = cur.lastrowid

            cur.execute("""
                SELECT product_id, quantity FROM cart WHERE user_login=?""", (login,))
            items = cur.fetchall()

            ordered_items = []
            total_price = 0.0
            for item_id, quantity in items:
                cur.execute("SELECT product_name, price FROM products WHERE product_id = ?", (item_id,))
                product_name, price = cur.fetchone()
                total_price += price * quantity
                ordered_items.append(
                    {'product_id': item_id, 'quantity': quantity, 'product_name': product_name, 'price': price})

            order_info = {
                'order_id': order_id,
                'user_login': login,
                'address': address,
                'order_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'items': ordered_items,
                'total_price': total_price  # Здесь добавляем полную сумму заказа
            }

            with open(f'order_{order_id}.json', 'w') as json_file:
                json.dump(order_info, json_file, ensure_ascii=False, indent=4)

            # Перемещаем содержимое корзины в заказы и удаляем из корзины!!!
            cur.execute("DELETE FROM cart WHERE user_login = ?", (login,))
            conn.commit()
            print(f"\nЗаказ создан. Идентификатор заказа: {order_id}. Итоговая сумма заказа: {total_price:.2f}.")
            return order_id

    def close(self):
        self._connection.close()
        print("Соединение с базой данных закрыто.")

    def _add_product(self, product_name, quantity, price):
        with self._connection:
            self._connection.execute("INSERT INTO products (product_name, quantity, price) VALUES (?, ?, ?)",
                                     (product_name, quantity, price))
        print("\nПродукт успешно добавлен.")

    def _delete_product(self, product_id):
        with self._connection as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
            if cur.rowcount == 0:
                print("\nПродукт не найден.")
            else:
                conn.commit()
                print("\nПродукт успешно удален.")

    def _block_user(self, login):
        with self._connection as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE Login = ?", (login,))
            if cur.rowcount == 0:
                print("\nПользователь не найден.")
            else:
                conn.commit()
                print("\nПользователь успешно заблокирован.")

    def _find_user(self, user_id):
        with self._connection as conn:
            cur = conn.cursor()
            cur.execute("SELECT Login, Password FROM users WHERE rowid = ?", (user_id,))
            user_data = cur.fetchone()
            if user_data:
                print(f"\nЛогин: {user_data[0]}, Пароль: {user_data[1]}")
            else:
                print("\nПользователь не найден.")