import telebot
import requests
import json
import re

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

def parse_ttn_data(message_text):
    """Parse TTN data from message text"""
    data = {}
    
    # Regular expressions for data extraction
    patterns = {
        'sender_name': r'Отправитель:\s*(.+)',
        'sender_phone': r'Телефон отправителя:\s*(\+?\d+)',
        'sender_city': r'Город отправителя:\s*(.+)',
        'sender_branch': r'Отделение отправителя:\s*(\d+)',
        'recipient_name': r'Получатель:\s*(.+)',
        'recipient_phone': r'Телефон получателя:\s*(\+?\d+)',
        'recipient_city': r'Город получателя:\s*(.+)',
        'recipient_branch': r'Отделение получателя:\s*(\d+)',
        'seats': r'Мест:\s*(\d+)',
        'weight': r'Вес:\s*(\d+(?:\.\d+)?)',
        'payer_type': r'Плательщик:\s*(Отправитель|Получатель)',
        'cost': r'Стоимость:\s*(\d+(?:\.\d+)?)',
        'cargo_description': r'Описание:\s*(.+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, message_text, re.IGNORECASE | re.MULTILINE)
        if match:
            data[key] = match.group(1).strip()
    
    return data

def create_ttn(data):
    # Get reference IDs
    sender_city_ref = get_city_ref(data["sender_city"])
    recipient_city_ref = get_city_ref(data["recipient_city"])
    
    if not sender_city_ref or not recipient_city_ref:
        return {"success": False, "errors": ["Город не найден"]}

    sender_warehouse_ref = get_warehouse_ref(sender_city_ref, data["sender_branch"])
    recipient_warehouse_ref = get_warehouse_ref(recipient_city_ref, data["recipient_branch"])
    
    if not sender_warehouse_ref or not recipient_warehouse_ref:
        return {"success": False, "errors": ["Отделение не найдено"]}

    sender_ref = get_counterparty_ref(data["sender_phone"], "Sender")
    recipient_ref = get_counterparty_ref(data["recipient_phone"], "Recipient")
    
    if not sender_ref or not recipient_ref:
        return {"success": False, "errors": ["Контрагент не найден"]}

    payload = {
        "apiKey": NOVA_POSHTA_API_KEY,
        "modelName": "InternetDocument",
        "calledMethod": "save",
        "methodProperties": {
            "PayerType": "Recipient" if data["payer_type"].lower() == "получатель" else "Sender",
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
📦 Создание накладной Новой Почты 📦

Для создания ТТН отправьте данные в следующем формате:

Отправитель: Иван Иванов
Телефон отправителя: +380501234567
Город отправителя: Киев
Отделение отправителя: 1

Получатель: Петр Петров
Телефон получателя: +380671234567
Город получателя: Одесса
Отделение получателя: 2

Мест: 1
Вес: 2.5
Плательщик: Получатель
Стоимость: 500
Описание: Одежда

❗️ Важно:
- Все поля обязательны
- Номер телефона в формате +380XXXXXXXXX
- Номер отделения указывать цифрами
- Плательщик: укажите "Отправитель" или "Получатель"
- Вес указывать в килограммах
- Стоимость указывать в гривнах
"""
    bot.send_message(message.chat.id, instructions)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Parse message text to extract data
        data = parse_ttn_data(message.text)
        
        # Validate required fields
        required_fields = [
            "sender_name", "sender_phone", "sender_city", "sender_branch",
            "recipient_name", "recipient_phone", "recipient_city", "recipient_branch",
            "seats", "weight", "payer_type", "cost", "cargo_description"
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            missing_fields_ru = {
                "sender_name": "Отправитель",
                "sender_phone": "Телефон отправителя",
                "sender_city": "Город отправителя",
                "sender_branch": "Отделение отправителя",
                "recipient_name": "Получатель",
                "recipient_phone": "Телефон получателя",
                "recipient_city": "Город получателя",
                "recipient_branch": "Отделение получателя",
                "seats": "Количество мест",
                "weight": "Вес",
                "payer_type": "Плательщик",
                "cost": "Стоимость",
                "cargo_description": "Описание"
            }
            missing_fields_names = [missing_fields_ru[field] for field in missing_fields]
            bot.send_message(
                message.chat.id,
                f"❌ Не заполнены обязательные поля:\n" + "\n".join(f"- {field}" for field in missing_fields_names)
            )
            return

        # Create TTN
        ttn = create_ttn(data)
        if ttn.get('success'):
            success_message = f"""
✅ Накладная успешно создана!

📝 Номер ТТН: {ttn['data'][0]['IntDocNumber']}
📦 Отправитель: {data['sender_name']}
📍 Город отправителя: {data['sender_city']}
🏢 Отделение: {data['sender_branch']}

📦 Получатель: {data['recipient_name']}
📍 Город получателя: {data['recipient_city']}
🏢 Отделение: {data['recipient_branch']}

📦 Мест: {data['seats']}
⚖️ Вес: {data['weight']} кг
💰 Стоимость: {data['cost']} грн
"""
            bot.send_message(message.chat.id, success_message)
        else:
            errors = ttn.get('errors', ['Неизвестная ошибка'])
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка создания ТТН:\n" + "\n".join(f"- {error}" for error in errors)
            )
    
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Произошла ошибка при обработке запроса:\n{str(e)}"
        )

if __name__ == "__main__":
    bot.polling()
