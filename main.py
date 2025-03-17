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
            "Sender": {
                "Name": data["sender_name"],  # Имя отправителя
                "ContactPerson": data["sender_name"],  # Контактное лицо
                "Phone": data["sender_phone"],  # Телефон отправителя
                "City": data["sender_city"],  # Город отправителя
                "Address": data["sender_branch"],  # Адрес отправителя (отделение)
            },
            "Recipient": {
                "Name": data["recipient_name"],  # Имя получателя
                "ContactPerson": data["recipient_name"],  # Контактное лицо
                "Phone": data["recipient_phone"],  # Телефон получателя
                "City": data["recipient_city"],  # Город получателя
                "Address": data["recipient_branch"],  # Адрес получателя (отделение)
            },
            "CargoType": "Parcel",  # Тип груза
            "SeatsAmount": data["seats"],  # Количество мест
            "Weight": data["weight"],  # Вес
            "ServiceType": "WarehouseWarehouse",  # Тип услуги
            "PaymentMethod": "Cash",  # Метод оплаты
            "Cost": data["cost"],  # Оценочная стоимость
            "CashOnDelivery": data["cash_on_delivery"],  # Наложенный платеж
        }
    }

    response = requests.post(url, json=payload)
    
    # Логируем полный ответ от API Новой Почты для анализа
    print("API Response:", response.json())  # Это поможет понять, в чем ошибка
    
    return response.json()

# Обработчик команд
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Отправь заявку для создания ТТН.")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_order(message):
    try:
        # Пример формата заявки:
        # 📦 Новая заявка
        # Отправитель: Иван Иванов
        # Телефон отправителя: +380501234567
        # Город отправителя: Киев
        # Отделение отправителя: 1
        # Получатель: Петр Петров
        # Телефон получателя: +380671234567
        # Город получателя: Одесса
        # Отделение получателя: 2
        # Количество мест: 1
        # Вес (кг): 2
        # Оценочная стоимость: 500
        # Наложенный платеж: 500
        # Оплата за доставку: Получатель

        # Преобразование данных заявки
        data = {
            "sender_name": message.text.split("\n")[1].split(": ")[1],
            "sender_phone": message.text.split("\n")[2].split(": ")[1],
            "sender_city": message.text.split("\n")[3].split(": ")[1],
            "sender_branch": message.text.split("\n")[4].split(": ")[1],
            
            "recipient_name": message.text.split("\n")[5].split(": ")[1],
            "recipient_phone": message.text.split("\n")[6].split(": ")[1],
            "recipient_city": message.text.split("\n")[7].split(": ")[1],
            "recipient_branch": message.text.split("\n")[8].split(": ")[1],
            
            "seats": int(message.text.split("\n")[9].split(": ")[1]),
            "weight": float(message.text.split("\n")[10].split(": ")[1]),
            "cost": float(message.text.split("\n")[11].split(": ")[1]),
            "cash_on_delivery": float(message.text.split("\n")[12].split(": ")[1]),
        }
        
        # Отправка данных в API для создания ТТН
        response = create_ttn(data)
        
        # Ответ пользователю в случае успеха или ошибки
        if response.get("success"):
            ttn_number = response["data"][0]["DocumentNumber"]
            bot.send_message(message.chat.id, f"ТТН успешно создано! Номер ТТН: {ttn_number}")
        else:
            bot.send_message(message.chat.id, "Ошибка создания ТТН. Попробуйте снова.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

# Запуск бота
bot.polling()
