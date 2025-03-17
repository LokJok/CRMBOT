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
            "Sender": data["sender_name"],
            "ContactSender": data["sender_name"],
            "SendersPhone": data["sender_phone"],
            "CitySender": data["sender_city"],
            "SenderAddress": data["sender_branch"],
            
            "Recipient": data["recipient_name"],
            "ContactRecipient": data["recipient_name"],
            "RecipientsPhone": data["recipient_phone"],
            "CityRecipient": data["recipient_city"],
            "RecipientAddress": data["recipient_branch"],
            
            "CargoType": "Parcel",
            "SeatsAmount": data["seats"],
            "Weight": data["weight"],
            "ServiceType": "WarehouseWarehouse",
            "PaymentMethod": "Cash",
            "PayerType": "Recipient" if data["payer"] == "Получатель" else "Sender",
            "Cost": data["cost"],
            "AfterpaymentOnGoodsCost": data["cash_on_delivery"],
            "Description": "Товар"
        }
    }
    response = requests.post(url, json=payload)
    return response.json()

# Функция обработки заявки
def parse_request(message):
    lines = message.text.split('\n')
    try:
        data = {
            "sender_name": lines[1].split(": ")[1],
            "sender_phone": lines[2].split(": ")[1],
            "sender_city": lines[3].split(": ")[1],
            "sender_branch": lines[4].split(": ")[1],
            
            "recipient_name": lines[6].split(": ")[1],
            "recipient_phone": lines[7].split(": ")[1],
            "recipient_city": lines[8].split(": ")[1],
            "recipient_branch": lines[9].split(": ")[1],
            
            "seats": lines[11].split(": ")[1],
            "weight": lines[12].split(": ")[1],
            "cost": lines[13].split(": ")[1],
            "cash_on_delivery": lines[14].split(": ")[1],
            
            "payer": lines[16].split(": ")[1]
        }
        return data
    except IndexError:
        return None

# Обработчик сообщений с заявками
@bot.message_handler(func=lambda message: "📦 Новая заявка" in message.text)
def handle_request(message):
    data = parse_request(message)
    if not data:
        bot.reply_to(message, "⚠ Ошибка! Некорректный формат заявки. Проверьте правильность данных.")
        return
    
    response = create_ttn(data)
    if response.get("success"):
        ttn_number = response["data"][0]["IntDocNumber"]
        bot.reply_to(message, f"✅ ТТН успешно создана! Номер: {ttn_number}")
    else:
        errors = "\n".join(response.get("errors", ["Неизвестная ошибка"]))
        bot.reply_to(message, f"❌ Ошибка создания ТТН:\n{errors}")

bot.polling(none_stop=True)
