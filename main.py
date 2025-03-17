import telebot
import requests
import json

NOVA_POSHTA_API_KEY = "cb589626abe2488ac0bd2c750419a496"
TELEGRAM_BOT_TOKEN = "7840803477:AAFql7Ppyk9bQ8RQI7uoSLnEFvahRpjQkV0"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def get_city_ref(city_name):
    """Get city reference by name"""
    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "searchSettlements",
        "methodProperties": {
            "CityName": city_name,
            "Limit": 1
        }
    }
    response = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload)
    data = response.json()
    if data.get('success') and data['data'][0]['Addresses']:
        return data['data'][0]['Addresses'][0]['Ref']
    return None

def get_warehouse_ref(city_ref, warehouse_number):
    """Get warehouse reference by city and number"""
    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {
            "CityRef": city_ref,
            "Page": 1,
            "Limit": 50,
            "Language": "ru"
        }
    }
    response = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload)
    data = response.json()
    if data.get('success'):
        for warehouse in data['data']:
            if str(warehouse_number) in warehouse['Description']:
                return warehouse['Ref']
    return None

def get_counterparty_ref(phone, counterparty_property):
    """Get counterparty reference by phone"""
    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "Counterparty",
        "calledMethod": "getCounterparties",
        "methodProperties": {
            "CounterpartyProperty": counterparty_property,
            "FindByString": phone
        }
    }
    response = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload)
    data = response.json()
    if data.get('success') and data['data']:
        return data['data'][0]['Ref']
    return None

def create_ttn(data):
    # Get reference IDs
    sender_city_ref = get_city_ref(data["sender_city"])
    recipient_city_ref = get_city_ref(data["recipient_city"])
    
    if not sender_city_ref or not recipient_city_ref:
        return {"success": False, "errors": ["City not found"]}

    sender_warehouse_ref = get_warehouse_ref(sender_city_ref, data["sender_branch"])
    recipient_warehouse_ref = get_warehouse_ref(recipient_city_ref, data["recipient_branch"])
    
    if not sender_warehouse_ref or not recipient_warehouse_ref:
        return {"success": False, "errors": ["Warehouse not found"]}

    sender_ref = get_counterparty_ref(data["sender_phone"], "Sender")
    recipient_ref = get_counterparty_ref(data["recipient_phone"], "Recipient")
    
    if not sender_ref or not recipient_ref:
        return {"success": False, "errors": ["Counterparty not found"]}

    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "InternetDocument",
        "calledMethod": "save",
        "methodProperties": {
            "PayerType": data["payer_type"],
            "PaymentMethod": "Cash",
            "CargoType": "Cargo",
            "VolumeGeneral": "0.1",
            "Weight": str(data["weight"]),
            "ServiceType": "WarehouseWarehouse",
            "SeatsAmount": str(data["seats"]),
            "Description": data["cargo_description"],
            "Cost": str(data["cost"]),
            "CitySender": sender_city_ref,
            "Sender": sender_ref,
            "SenderAddress": sender_warehouse_ref,
            "ContactSender": sender_ref,
            "SendersPhone": data["sender_phone"],
            "CityRecipient": recipient_city_ref,
            "Recipient": recipient_ref,
            "RecipientAddress": recipient_warehouse_ref,
            "ContactRecipient": recipient_ref,
            "RecipientsPhone": data["recipient_phone"]
        }
    }

    response = requests.post("https://api.novaposhta.ua/v2.0/json/", json=payload)
    return response.json()

@bot.message_handler(commands=['start'])
def start(message):
    instructions = """
Привет! Для создания ТТН отправьте данные в формате:
    
Отправитель: Имя
Телефон отправителя: +380XXXXXXXXX
Город отправителя: Название
Отделение отправителя: Номер

Получатель: Имя
Телефон получателя: +380XXXXXXXXX
Город получателя: Название
Отделение получателя: Номер

Мест: Количество
Вес: Число кг
Плательщик: Отправитель/Получатель
Стоимость: Сумма
Описание: Текст
"""
    bot.send_message(message.chat.id, instructions)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Here you should parse the message text to extract data
        # This is a simplified example
        data = {
            "sender_name": "Иван Иванов",
            "sender_phone": "+380501234567",
            "sender_city": "Киев",
            "sender_branch": "1",
            "recipient_name": "Петр Петров",
            "recipient_phone": "+380671234567",
            "recipient_city": "Одесса",
            "recipient_branch": "2",
            "seats": "1",
            "weight": "2",
            "payer_type": "Recipient",
            "cost": "500",
            "cargo_description": "Товар"
        }

        # Validate required fields
        required_fields = [
            "sender_phone", "sender_city", "sender_branch",
            "recipient_phone", "recipient_city", "recipient_branch",
            "seats", "weight", "cost", "cargo_description"
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            bot.send_message(
                message.chat.id, 
                f"Не заполнены обязательные поля: {', '.join(missing_fields)}"
            )
            return

        ttn = create_ttn(data)
        if ttn.get('success'):
            bot.send_message(
                message.chat.id, 
                f"Накладная создана. Номер ТТН: {ttn['data'][0]['IntDocNumber']}"
            )
        else:
            errors = ttn.get('errors', ['Неизвестная ошибка'])
            bot.send_message(
                message.chat.id, 
                f"Ошибка создания ТТН: {', '.join(errors)}"
            )
    
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"Произошла ошибка при обработке запроса: {str(e)}"
        )

if __name__ == "__main__":
    bot.polling()
