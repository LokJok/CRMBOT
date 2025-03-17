import os
import json
import re
import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN", "7840803477:AAFql7Ppyk9bQ8RQI7uoSLnEFvahRpjQkV0")
NP_API_KEY = os.getenv("NP_API_KEY", "cb589626abe2488ac0bd2c750419a496")
GROUP_FROM = -1002343109699  # Группа, откуда получать заявки
GROUP_TTN = -1002684087753  # Группа, куда отправлять ТТН

# Данные отправителя
SENDER_NAME = "Курочка Давид Ігорович"
SENDER_PHONE = "+380931168786"
SENDER_CITY = "м. Фастів"
SENDER_ADDRESS = "вул Ярослава мудрого 51"
SENDER_WAREHOUSE = "1"

bot = telebot.TeleBot(BOT_TOKEN)

# Хранение накладных
created_ttns = []
sent_ttns = []

def create_np_waybill(data):
    url = "https://api.novaposhta.ua/v2.0/json/"
    payload = {
        "apiKey": NP_API_KEY,
        "modelName": "InternetDocument",
        "calledMethod": "save",
        "methodProperties": {
            "Sender": SENDER_NAME,
            "SenderPhone": SENDER_PHONE,
            "CitySender": SENDER_CITY,
            "SenderAddress": SENDER_ADDRESS,
            "SenderWarehouse": SENDER_WAREHOUSE,
            "Recipient": data["name"],
            "RecipientPhone": data["phone"],
            "CityRecipient": data["city"],
            "RecipientWarehouse": data["warehouse"],
            "CargoType": "Parcel",
            "Weight": "0.5",
            "ServiceType": "WarehouseWarehouse",
            "PaymentMethod": "Cash",
            "PayerType": "Recipient",
            "Cost": data["amount"],
            "Description": "Святкова скарбничка",
            "AfterpaymentOnGoodsCost": data["transfer"]
        }
    }
    response = requests.post(url, json=payload)
    return response.json()

@bot.message_handler(func=lambda message: message.chat.id == GROUP_FROM)
def handle_order(message):
    try:
        order_data = {}
        
        match_name = re.search(r"ФИО:\s*(.+)", message.text)
        match_phone = re.search(r"Телефон:\s*(.+)", message.text)
        match_city = re.search(r"Мiсто:\s*(.+)", message.text)
        match_warehouse = re.search(r"Номер вiддiлення:\s*(\d+)", message.text)
        match_cost = re.search(r"Оцiночна вартiсть:\s*(\d+)", message.text)
        match_transfer = re.search(r"Грошовий переказ:\s*(\d+)", message.text)

        if not all([match_name, match_phone, match_city, match_warehouse, match_cost, match_transfer]):
            bot.send_message(message.chat.id, "❌ Некорректная форма заявки. Пожалуйста, укажите все данные правильно.")
            return

        order_data["name"] = match_name.group(1).strip()
        order_data["phone"] = match_phone.group(1).strip()
        order_data["city"] = match_city.group(1).strip()
        order_data["warehouse"] = match_warehouse.group(1).strip()
        order_data["amount"] = match_cost.group(1).strip()
        order_data["transfer"] = match_transfer.group(1).strip()

        response = create_np_waybill(order_data)
        
        if response.get("success"):
            ttn = response["data"][0]["IntDocNumber"]
            created_ttns.append({"ttn": ttn, "amount": order_data["amount"]})
            bot.send_message(GROUP_TTN, f"🚛 Создана ТТН: {ttn}\nСумма: {order_data['amount']} грн\nГрошовий переказ: {order_data['transfer']} грн")
        else:
            bot.send_message(GROUP_TTN, "❌ Ошибка создания ТТН")
    
    except Exception as e:
        bot.send_message(GROUP_TTN, f"❌ Ошибка обработки: {str(e)}")

@bot.message_handler(commands=['pending'])
def show_pending_ttns(message):
    if not created_ttns:
        bot.send_message(message.chat.id, "📦 Нет неотправленных накладных")
    else:
        total = sum(float(x["amount"]) for x in created_ttns)
        ttn_list = "\n".join([f"{x['ttn']} – {x['amount']} грн" for x in created_ttns])
        bot.send_message(message.chat.id, f"📌 Неотправленные ТТН:\n{ttn_list}\n\n💰 Общая сумма: {total} грн")

@bot.message_handler(commands=['in_transit'])
def show_sent_ttns(message):
    if not sent_ttns:
        bot.send_message(message.chat.id, "🚚 Нет отправленных накладных")
    else:
        total = sum(float(x["amount"]) for x in sent_ttns)
        ttn_list = "\n".join([f"{x['ttn']} – {x['amount']} грн" for x in sent_ttns])
        bot.send_message(message.chat.id, f"🚀 В пути:\n{ttn_list}\n\n💰 Общая сумма: {total} грн")

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "👋 Привет! Я бот для создания накладных Новой Почты. Отправьте заявку в формате:")
    bot.send_message(message.chat.id, "ФИО: Иван Иванов\nТелефон: +380501234567\nМiсто: Київ\nНомер вiддiлення: 1\nОцiночна вартiсть: 250\nГрошовий переказ: 250")

bot.polling(none_stop=True)
