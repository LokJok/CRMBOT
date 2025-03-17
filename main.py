import telebot
import requests

# Ваши настройки бота и API
API_TOKEN = "cb589626abe2488ac0bd2c750419a496"
bot = telebot.TeleBot("7840803477:AAFql7Ppyk9bQ8RQI7uoSLnEFvahRpjQkV0")

# Функция для обработки запросов на создание ТТН
def create_tracking_number(message):
    try:
        # Пример данных для создания ТТН, замените на актуальные данные
        data = {
            "apiKey": "cb589626abe2488ac0bd2c750419a496",  # Ваш API ключ
            "modelName": "InternetDocument",
            "calledMethod": "save",
            "methodProperties": {
                "senderName": "Давид Куточка",
                "senderPhone": "+380931168786",
                "senderCity": "Фастів",
                "senderDepartment": 5,
                "recipientName": "Максим Виговський",
                "recipientPhone": "+380669642205",
                "recipientCity": "Одесса",
                "recipientDepartment": 11,
                "weight": 2.5,
                "payer": "ПолуПолучатель",
                "amount": 500,
                "description": "Одежда"
            }
        }

        # Пример запроса на создание ТТН (замените на реальный API)
        response = requests.post('https://api.novaposhta.ua/v2.0/json/', json=data)

        # Проверка успешности запроса
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                # Формирование успешного сообщения
                success_message = f"✅ ТТН успешно создано!\n\n"
                success_message += f"ТТН: {response_data.get('tracking_number')}\n"
                success_message += f"Отправитель: {data['methodProperties']['senderName']}\n"
                success_message += f"Получатель: {data['methodProperties']['recipientName']}\n"
                success_message += f"Описание: {data['methodProperties']['description']}\n"
                success_message += f"Стоимость: {data['methodProperties']['amount']} UAH\n"
                bot.send_message(message.chat.id, success_message)
            else:
                # Если ошибка в ответе от сервера
                error_message = f"❌ Ошибка при создании ТТН: {response_data.get('error', 'Неизвестная ошибка')}"
                bot.send_message(message.chat.id, error_message)
        else:
            # Если сервер вернул ошибку (например, неправильный запрос)
            bot.send_message(message.chat.id, f"❌ Ошибка сервера: {response.status_code}")
            print(f"Error: Server returned status code {response.status_code}")
    except Exception as e:
        # Логирование ошибки
        error_message = f"❌ Произошла ошибка: {str(e)}"
        bot.send_message(message.chat.id, error_message)
        print(f"Error details: {str(e)}")  # Логирование ошибки в консоль или файл

# Обработка команды от пользователя
@bot.message_handler(commands=['create_ttn'])
def handle_create_ttn(message):
    create_tracking_number(message)

# Запуск бота
bot.polling(none_stop=True)
