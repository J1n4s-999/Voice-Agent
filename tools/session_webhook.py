# webhook_handler.py

import uuid
import logging
import os

class WebhookHandler:
    def __init__(self):
        self.name = None
        self.email = None
        self.appointment_date = None
        self.duration = None
        self.token = None

    def process(self, data):
        logging.info(f"Webhook empfangen: {data}")

        self.name = data.get("name")
        self.email = data.get("email")
        self.appointment_date = data.get("appointment_date")
        self.duration = data.get("duration_minutes")

        # Token erzeugen
        self.token = str(uuid.uuid4())

        base_url = os.environ.get("PUBLIC_URL", "http://localhost:5000")
        confirm_link = f"{base_url}/confirm/{self.token}"

        logging.info(f"Name: {self.name}")
        logging.info(f"E-Mail: {self.email}")
        logging.info(f"Termin: {self.appointment_date}")
        logging.info(f"Dauer: {self.duration}")
        logging.info(f"Bestätigungslink: {confirm_link}")

        return confirm_link

    def get_data(self):
        return {
            "name": self.name,
            "email": self.email,
            "appointment_date": self.appointment_date,
            "duration": self.duration,
            "token": self.token
        }