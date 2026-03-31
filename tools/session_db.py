from tools.session_webhook import Webhook as WH
import psycopg2
import os

class DB():
    def __init__(self):
        self.conn = psycopg2.connect(os.environ["DATABASE_URL"])
        self.cursor = self.conn.cursor()

    def send_db(self):
        val = WH.get_webhook()
        self.cursor.execute("""
        INSERT INTO appointments (name, email, appointment_date, duration_minutes, status, confirmation_token)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (val[0], val[1], val[2], val[3], "pending"))
        self.conn.commit()

    

    