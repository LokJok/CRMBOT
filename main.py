import os
import json
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
            "AfterpaymentOnGoodsCost": data["amount"]
        }
    }
    response = requests.post(url, json=payload)
    return response.json()

# Обработчик /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("Накладные, не отправленные", callback_data="pending")
    button2 = InlineKeyboardButton("Накладные в пути", callback_data="in_transit")
    markup.add(button1, button2)
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id == GROUP_FROM)
def handle_order(message):
    try:
        lines = message.text.split('\n')
        order_data = {
            "name": lines[0],
            "phone": lines[1],
            "city": lines[2],
            "warehouse": lines[3],
            "amount": lines[4]
        }
        response = create_np_waybill(order_data)
        if response.get("success"):
            ttn = response["data"][0]["IntDocNumber"]
            created_ttns.append({"ttn": ttn, "amount": order_data["amount"]})
            bot.send_message(GROUP_TTN, f"🚛 Создана ТТН: {ttn}\nСумма: {order_data['amount']} грн")
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

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "pending":
        show_pending_ttns(call.message)
    elif call.data == "in_transit":
        show_sent_ttns(call.message)

bot.polling(none_stop=True)
