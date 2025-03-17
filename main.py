import telebot
import requests
import json

# Укажите ваш API-ключ от Новой Почты
NOVA_POSHTA_API_KEY = ""cb589626abe2488ac0bd2c750419a496""
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
            "Sender": {
                "Name": data["sender_name"],
                "Phone": data["sender_phone"],
                "City": data["sender_city"],
                "SenderAddress": data["sender_branch"]
            },
            "Recipient": {
                "Name": data["recipient_name"],
                "Phone": data["recipient_phone"],
                "City": data["recipient_city"],
                "RecipientAddress": data["recipient_branch"]
            },
            "CargoType": "Parcel",
            "SeatsAmount": data["seats"],
            "Weight": data["weight"],
            "ServiceType": "WarehouseWarehouse",
            "PaymentMethod": "Cash",
            "PayerType": data["payer_type"],
            "Cost": data["cost"],
            "CargoDescription": data["cargo_description"]
        }
    }

    response = requests.post(url, json=payload)
    return response.json()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправьте данные для создания ТТН в формате: \n...")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Предположим, что данные передаются в виде строки
    data = {
        "sender_name": "Иван Иванов",
        "sender_phone": "+380501234567",
        "sender_city": "Киев",
        "sender_branch": "Отделение №1",
        "recipient_name": "Петр Петров",
        "recipient_phone": "+380671234567",
        "recipient_city": "Одесса",
        "recipient_branch": "Отделение №2",
        "seats": 1,
        "weight": 2,
        "payer_type": "Recipient",
        "cost": 500,
        "cargo_description": "Товар"
    }

    ttn = create_ttn(data)
    if ttn['success']:
        bot.send_message(message.chat.id, f"Накладная создана. Номер ТТН: {ttn['data'][0]['IntDocNumber']}")
    else:
        bot.send_message(message.chat.id, f"Ошибка создания ТТН: {', '.join(ttn['errors'])}")

bot.polling()
