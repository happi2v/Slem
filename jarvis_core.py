import webbrowser
import os

def execute_command(command):
    """Анализирует строку и вызывает нужную функцию."""
    command = command.lower() # Приводим к нижнему регистру для простоты

    if "браузер" in command or "интернет" in command:
        print("Запускаю браузер.")
        webbrowser.open("https://google.com")
    elif "калькулятор" in command:
        print("Запускаю калькулятор.")
        os.system("calc") # Для Windows
        # os.system("gnome-calculator") # Для Linux
    elif "выход" in command or "пока" in command:
        print("Завершаю работу.")
        return False # Сигнал для остановки цикла
    else:
        print(f"Команда '{command}' не распознана.")
    return True # Сигнал продолжать

# Основной цикл
print("Джарвис к вашим услугам. Жду текстовых команд.")
while True:
    user_input = input("Ваш приказ: ")
    if not execute_command(user_input):
        break