import database_for_shop
import os

def clear_console():
    command = 'cls' if os.name == 'nt' else 'clear'
    os.system(command)

def main():
    database = database_for_shop.UserDatabase()

    try:
        while True:
            print("\n1. Зарегистрироваться")
            print("2. Войти")
            print("3. Войти как администратор")
            print("4. Выйти")
            choice = input("Выберите действие: ")

            if choice == "1":
                login = input("\nПридумайте ваш логин для входа в информационную систему: ")
                password = input("Введите пароль: ")

                if len(login) < 5:
                    clear_console()
                    print("В вашем имени недостаточно символов")
                    continue
                elif ' ' in login:
                    clear_console()
                    print("Введите имя без пробелов")
                    continue
                database.add_user(login, password)


            elif choice == "2":

                login = input("\nВведите имя пользователя: ")
                password = input("Введите пароль: ")

                if database.authenticate_user(login, password):
                    while True:
                        print("\n1. Посмотреть товары")
                        print("2. Посмотреть свои заказы")
                        print("3. Оформить заказ")
                        print("4. Выйти")

                        user_choice = input("\nВыберите опцию: ")

                        if user_choice == "1":
                            database._view_products(login)

                        elif user_choice == "2":
                            database._view_orders(login)

                        elif user_choice == "3":
                            address = input("Введите адрес доставки для заказа: ")
                            database._checkout_cart(login, address)

                        elif user_choice == "4":
                            break

                        else:
                            print("\nНеправильный ввод. Пожалуйста, попробуйте снова.")


            elif choice == "3":
                admin_login = input("\nВведите логин администратора: ")
                admin_password = input("Введите пароль администратора: ")

                if admin_login == "ChaseHunter" and admin_password == "LeoAlvarezismyboyfriend00!":
                    while True:
                        print("\n1. Добавить товар")
                        print("2. Удалить товар")
                        print("3. Заблокировать пользователя")
                        print("4. Поиск пользователя")
                        print("5. Выйти")
                        admin_choice = input("\nВыберите действие: ")
                        if admin_choice == "1":
                            product_name = input("\nВведите название товара: ")
                            quantity = int(input("Введите количество: "))
                            price = float(input("Введите цену за единицу товара: "))
                            database._add_product(product_name, quantity, price)

                        elif admin_choice == "2":
                            product_id = int(input("\nВведите ID товара для удаления: "))
                            database._delete_product(product_id)

                        elif admin_choice == "3":
                            user_login = input("\nВведите логин пользователя для блокировки: ")
                            database._block_user(user_login)


                        elif admin_choice == "4":
                            user_id = int(input("ID: "))
                            print("\nУчетные данные пользователя:")
                            database._find_user(user_id)


                        elif admin_choice == "5":
                            break

                        else:
                            print("\nНеправильный ввод. Пожалуйста, попробуйте снова.")
                else:
                    print("\nНеверные учетные данные администратора.")

            elif choice == "4":
                break

            else:
                print("\nНеправильный ввод. Пожалуйста, попробуйте снова.")
    finally:
        database.close()

if __name__ == "__main__":
    main()