from flask import Flask, request, jsonify
import logging
from tools.session_webhook import WebhookHandler

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

handler = WebhookHandler()

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    confirm_link = handler.process(data)
    return jsonify({"ok": True, "confirm_link": confirm_link}), 200

@app.route("/confirm/<token>", methods=["GET"])
def confirm(token):
    # später: Token prüfen, Termin buchen, DB aktualisieren
    return f"Termin bestätigt für Token: {token}", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)