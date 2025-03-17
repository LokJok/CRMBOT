import telebot
import requests

# Ваши настройки бота и API
API_TOKEN = "7840803477:AAFql7Ppyk9bQ8RQI7uoSLnEFvahRpjQkV0"
bot = telebot.TeleBot(cb589626abe2488ac0bd2c750419a496)

# Функция для обработки запросов на создание ТТН
def create_tracking_number(message):
    try:
        # Пример данных для создания ТТН, замените на актуальные данные
        data = {
            "sender_name": "Давид Куточка",
            "sender_phone": "+380931168786",
            "sender_city": "Фастів",
            "sender_department": 5,
            "recipient_name": "Максим Виговський",
            "recipient_phone": "+380669642205",
            "recipient_city": "Одесса",
            "recipient_department": 11,
            "weight": 2.5,
            "payer": "ПолуПолучатель",
            "amount": 500,
            "description": "Одежда"
        }

        # Пример запроса на создание ТТН (замените на реальный API)
response = requests.post('https://api.novaposhta.ua/v2.0/json/', data=data)



        # Проверка успешности запроса
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('ok'):
                # Формирование успешного сообщения
                success_message = f"✅ ТТН успешно создано!\n\n"
                success_message += f"ТТН: {response_data.get('tracking_number')}\n"
                success_message += f"Отправитель: {data['sender_name']}\n"
                success_message += f"Получатель: {data['recipient_name']}\n"
                success_message += f"Описание: {data['description']}\n"
                success_message += f"Стоимость: {data['amount']} UAH\n"
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
