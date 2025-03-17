import telebot
import requests
import json

# Укажите ваш API-ключ от Новой Почты
NOVA_POSHTA_API_KEY = "cb589626abe2488ac0bd2c750419a496"
# Укажите ваш токен бота
TELEGRAM_BOT_TOKEN = "7840803477:AAFql7Ppyk9bQ8RQI7uoSLnEFvahRpjQkV0"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Функция для создания ТТН через API Новой Почты
def create_ttn(data):
    url = "https://api.novaposhta.ua/v2.0/json/"
    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "InternetDocument",
        "calledMethod": "save",
        "methodProperties": {
            "Sender": data["sender_name"],  # Имя отправителя
            "ContactSender": data["sender_name"],  # Контакт отправителя
            "SendersPhone": data["sender_phone"],  # Телефон отправителя
            "CitySender": data["sender_city"],  # Город отправителя
            "SenderAddress": data["sender_branch"],  # Адрес/Отделение отправителя

            "Recipient": data["recipient_name"],  # Имя получателя
            "ContactRecipient": data["recipient_name"],  # Контакт получателя
            "RecipientsPhone": data["recipient_phone"],  # Телефон получателя
            "CityRecipient": data["recipient_city"],  # Город получателя
            "RecipientAddress": data["recipient_branch"],  # Адрес/Отделение получателя

            "CargoType": "Parcel",  # Тип груза
            "SeatsAmount": data["seats"],  # Количество мест
            "Weight": data["weight"],  # Вес
            "ServiceType": "WarehouseWarehouse",  # Тип сервиса
            "PaymentMethod": "Cash",  # Способ оплаты (наложенный платеж)
            "PayerType": "Recipient",  # Тип плательщика (можно "Sender" или "Recipient")
            "Description": "Отправка посылки",  # Описание отправления (например, посылка)
        }
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if result["success"]:
        ttn_number = result["data"][0]["DocumentNumber"]
        return f"ТТН успешно создана. Номер ТТН: {ttn_number}"
    else:
        error_message = ", ".join(result["errors"])
        return f"Ошибка создания ТТН: {error_message}"

# Хэндлер для обработки сообщений
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Здравствуйте! Отправьте данные для создания ТТН.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Пример разборки сообщения на данные для ТТН
        data = {
            "sender_name": "Иван Иванов",  # Примерное имя отправителя
            "sender_phone": "+380501234567",  # Примерный телефон отправителя
            "sender_city": "Киев",  # Примерный город отправителя
            "sender_branch": "1",  # Примерное отделение отправителя

            "recipient_name": "Петр Петров",  # Примерное имя получателя
            "recipient_phone": "+380671234567",  # Примерный телефон получателя
            "recipient_city": "Одесса",  # Примерный город получателя
            "recipient_branch": "2",  # Примерное отделение получателя

            "seats": 1,  # Количество мест
            "weight": 2,  # Вес (кг)
            "cost": 500,  # Оценочная стоимость
            "cash_on_delivery": 500,  # Наложенный платеж
        }

        response = create_ttn(data)
        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

# Запуск бота
bot.polling(none_stop=True)
