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

    def find_counterparty(self, phone, is_sender=True):
        payload = {
            "apiKey": self.api_key,
            "modelName": "Counterparty",
            "calledMethod": "getCounterparties",
            "methodProperties": {
                "CounterpartyProperty": "Sender" if is_sender else "Recipient",
                "Page": "1",
                "FindByString": phone
            }
        }
        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result["success"] and result["data"]:
                counterparty_ref = result["data"][0]["Ref"]
                contact_payload = {
                    "apiKey": self.api_key,
                    "modelName": "Counterparty",
                    "calledMethod": "getCounterpartyContactPersons",
                    "methodProperties": {
                        "Ref": counterparty_ref
                    }
                }
                contact_response = requests.post(self.base_url, json=contact_payload, timeout=10)
                contact_result = contact_response.json()
                if contact_result["success"] and contact_result["data"]:
                    return counterparty_ref, contact_result["data"][0]["Ref"]
            return None, None
        except requests.exceptions.RequestException as e:
            return None, None

    def create_counterparty(self, name, phone, is_sender=True):
        counterparty
