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
            "AfterpaymentOnGoodsCost": data["transfer"]
        }
    }
    response = requests.post(url, json=payload)
    return response.json()

@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Накладные, не отправленные", callback_data="pending"))
    markup.add(InlineKeyboardButton("Накладные в пути", callback_data="in_transit"))
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id == GROUP_FROM)
def handle_order(message):
    try:
        lines = message.text.split('\n')
        order_data = {
            "name": lines[0].replace("ФИО: ", ""),
            "phone": lines[1].replace("Телефон: ", ""),
            "city": lines[2].replace("Мiсто: ", ""),
            "warehouse": lines[3].replace("Номер вiддiлення: ", ""),
            "amount": lines[4].replace("Оцiночна вартiсть: ", ""),
            "transfer": lines[5].replace("Грошовий переказ: ", "")
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

@bot.callback_query_handler(func=lambda call: call.data == "pending")
def show_pending_ttns(call):
    if not created_ttns:
        bot.send_message(call.message.chat.id, "📦 Нет неотправленных накладных")
    else:
        total = sum(float(x["amount"]) for x in created_ttns)
        ttn_list = "\n".join([f"{x['ttn']} – {x['amount']} грн" for x in created_ttns])
        bot.send_message(call.message.chat.id, f"📌 Неотправленные ТТН:\n{ttn_list}\n\n💰 Общая сумма: {total} грн")

@bot.callback_query_handler(func=lambda call: call.data == "in_transit")
def show_sent_ttns(call):
    if not sent_ttns:
        bot.send_message(call.message.chat.id, "🚚 Нет отправленных накладных")
    else:
        total = sum(float(x["amount"]) for x in sent_ttns)
        ttn_list = "\n".join([f"{x['ttn']} – {x['amount']} грн" for x in sent_ttns])
        bot.send_message(call.message.chat.id, f"🚀 В пути:\n{ttn_list}\n\n💰 Общая сумма: {total} грн")

bot.polling(none_stop=True)
