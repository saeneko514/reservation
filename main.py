from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)


SHEETY_TOKEN = os.environ.get("SHEETY_TOKEN")
SHEETY_URL = f"https://api.sheety.co/{SHEETY_TOKEN}/reservations/reservations"

@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json

    reservation = {
        "reservation": {
            "userId": data["userId"],
            "displayName": data["displayName"],
            "name": data["name"],
            "date": data["date"],
            "time": data["time"],
            "createdAt": datetime.now().isoformat()
        }
    }

    headers = {
        "Authorization": f"Bearer {SHEETY_TOKEN}",
        "Content-Type": "application/json"
    }

    res = requests.post(SHEETY_URL, json=reservation, headers=headers)
    if res.status_code == 201:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "detail": res.text}), 400