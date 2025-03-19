import requests
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os

class NovaPoshtaBot:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.novaposhta.ua/v2.0/json/"

    def parse_message(self, message):
        try:
            lines = message.strip().split('\n')
            data = {}
            for line in lines:
                key, value = line.split(': ', 1)
                data[key] = value
            
            phone_pattern = r"^\+?380[0-9]{9}$"
            sender_phone = data["Отправитель"].split(',')[1].strip()
            recipient_phone = data["Получатель"].split(',')[1].strip()
            
            if not re.match(phone_pattern, sender_phone):
                return "Ошибка: Неверный формат телефона отправителя. Используйте формат 380XXXXXXXXX"
            if not re.match(phone_pattern, recipient_phone):
                return "Ошибка: Неверный формат телефона получателя. Используйте формат 380XXXXXXXXX"

            return {
                "sender_name": data["Отправитель"].split(',')[0].strip(),
                "sender_phone": sender_phone,
                "recipient_name": data["Получатель"].split(',')[0].strip(),
                "recipient_phone": recipient_phone,
                "sender_city": data["Город отправителя"],
                "recipient_city": data["Город получателя"],
                "sender_warehouse": data["Отделение отправителя"],
                "recipient_warehouse": data["Отделение получателя"],
                "weight": float(data["Вес"].split()[0]),
                "description": data["Описание"]
            }
        except Exception as e:
            return f"Ошибка парсинга сообщения: {str(e)}"

    def create_counterparty(self, name, phone, is_sender=True):
        payload = {
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "save",
            "methodProperties": {
                "FirstName": name.split()[0],
                "MiddleName": name.split()[1] if len(name.split()) > 1 else "",
                "LastName": name.split()[2] if len(name.split()) > 2 else "",
                "Phone": phone,
                "CounterpartyType": "PrivatePerson",
                "CounterpartyProperty": "Sender" if is_sender else "Recipient"
            }
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result["success"]:
                return result["data"][0]["Ref"], result["data"][0]["ContactPerson"]["data"][0]["Ref"]
            return None, None
        except requests.exceptions.RequestException as e:
            return None, None

    def create_ttn(self, parsed_data):
        try:
            # Создаем или получаем контрагентов
            sender_ref, contact_sender_ref = self.create_counterparty(
                parsed_data["sender_name"], 
                parsed_data["sender_phone"], 
                is_sender=True
            )
            if not sender_ref or not contact_sender_ref:
                return "Ошибка: Не удалось создать отправителя"

            recipient_ref, contact_recipient_ref = self.create_counterparty(
                parsed_data["recipient_name"], 
                parsed_data["recipient_phone"], 
                is_sender=False
            )
            if not recipient_ref or not contact_recipient_ref:
                return "Ошибка: Не удалось создать получателя"

            # Получаем Ref городов и отделений
            sender_city_ref = self.get_city_ref(parsed_data["sender_city"])
            if not sender_city_ref:
                return "Ошибка: Не найден город отправителя"
                
            recipient_city_ref = self.get_city_ref(parsed_data["recipient_city"])
            if not recipient_city_ref:
                return "Ошибка: Не найден город получателя"
            
            sender_warehouse_ref = self.get_warehouse_ref(sender_city_ref, parsed_data["sender_warehouse"])
            if not sender_warehouse_ref:
                return "Ошибка: Не найдено отделение отправителя"
                
            recipient_warehouse_ref = self.get_warehouse_ref(recipient_city_ref, parsed_data["recipient_warehouse"])
            if not recipient_warehouse_ref:
                return "Ошибка: Не найдено отделение получателя"

            payload = {
                "apiKey": self.api_key,
                "modelName": "InternetDocument",
                "calledMethod": "save",
                "methodProperties": {
                    "PayerType": "Recipient",
                    "PaymentMethod": "Cash",
                    "DateTime": "20.03.2025",
                    "CargoType": "Cargo",
                    "Weight": str(parsed_data["weight"]),
                    "ServiceType": "WarehouseWarehouse",
                    "SeatsAmount": "1",
                    "Description": parsed_data["description"],
                    "Sender": sender_ref,
                    "SenderAddress": sender_warehouse_ref,
                    "ContactSender": contact_sender_ref,
                    "SendersPhone": parsed_data["sender_phone"],
                    "Recipient": recipient_ref,
                    "RecipientAddress": recipient_warehouse_ref,
                    "ContactRecipient": contact_recipient_ref,
                    "RecipientsPhone": parsed_data["recipient_phone"]
                }
            }

            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result["success"]:
                return f"Накладная создана! Номер ТТН: {result['data'][0]['IntDocNumber']}"
            else:
                return f"Ошибка API: {result['errors']}"
                
        except requests.exceptions.RequestException as e:
            return f"Ошибка сети: {str(e)}. Проверьте подключение к интернету."
        except Exception as e:
            return f"Неизвестная ошибка: {str(e)}"

    def get_city_ref(self, city_name):
        try:
            payload = {
                "apiKey": self.api_key,
                "modelName": "Address",
                "calledMethod": "getCities",
                "methodProperties": {
                    "FindByString": city_name
                }
            }
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["success"] and data["data"]:
                return data["data"][0]["Ref"]
            return None
        except requests.exceptions.RequestException:
            return None

    def get_warehouse_ref(self, city_ref, warehouse_number):
        try:
            payload = {
                "apiKey": self.api_key,
                "modelName": "Address",
                "calledMethod": "getWarehouses",
                "methodProperties": {
                    "CityRef": city_ref,
                    "FindByString": warehouse_number
                }
            }
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data["success"] and data["data"]:
                return data["data"][0]["Ref"]
            return None
        except requests.exceptions.RequestException:
            return None

# Telegram Bot часть
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для создания накладных Новой Почты.\n"
        "Отправь мне данные в таком формате:\n"
        "Отправитель: Имя Фамилия, 380XXXXXXXXX\n"
        "Получатель: Имя Фамилия, 380XXXXXXXXX\n"
        "Город отправителя: название\n"
        "Город получателя: название\n"
        "Отделение отправителя: номер\n"
        "Отделение получателя: номер\n"
        "Вес: число кг\n"
        "Описание: текст\n\n"
        "Для помощи используй /help"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Как использовать бота:\n"
        "1. Отправьте данные в указанном формате.\n"
        "2. Телефон должен быть в формате 380XXXXXXXXX (12 цифр).\n"
        "3. Вес указывайте в кг (например, 2.5 кг).\n"
        "Пример:\n"
        "Отправитель: Иван Иванов, 380671234567\n"
        "Получатель: Петр Петров, 380681234567\n"
        "Город отправителя: Киев\n"
        "Город получателя: Одесса\n"
        "Отделение отправителя: 1\n"
        "Отделение получателя: 2\n"
        "Вес: 2.5 кг\n"
        "Описание: Книги\n\n"
        "Если что-то не работает, проверьте формат данных или связь с интернетом."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    nova_bot = context.bot_data["nova_bot"]
    
    parsed_data = nova_bot.parse_message(message)
    if isinstance(parsed_data, dict):
        result = nova_bot.create_ttn(parsed_data)
        await update.message.reply_text(result)
    else:
        await update.message.reply_text(parsed_data)

def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    NOVA_POSHTA_API_KEY = os.getenv("NOVA_POSHTA_API_KEY")

    if not TELEGRAM_TOKEN or not NOVA_POSHTA_API_KEY:
        raise ValueError("Необходимо указать TELEGRAM_TOKEN и NOVA_POSHTA_API_KEY в переменных окружения")

    nova_bot = NovaPoshtaBot(NOVA_POSHTA_API_KEY)
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.bot_data["nova_bot"] = nova_bot

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
