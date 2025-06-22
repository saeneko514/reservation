from flask import Flask, request, jsonify, render_template
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_TOKEN = os.environ.get("SHEETY_TOKEN")
SHEETY_URL = "https://api.sheety.co/91a51e4efb03bbce4a21258eebc3ae12/reservations/reservations"

@app.route("/", methods=["GET"])
def index():
    # 予約フォームや予約一覧表示画面のHTMLを返す
    return render_template("index.html")

@app.route("/reserve", methods=["POST"])
def reserve():
    try:
        data = request.json
        date = data.get("date")
        time = data.get("time")

        headers = {
            "Authorization": f"Bearer {SHEETY_TOKEN}",
            "Content-Type": "application/json"
        }

        # 既存予約一覧を取得して重複チェック
        res_get = requests.get(SHEETY_URL, headers=headers)
        if res_get.status_code != 200:
            return jsonify({"status": "error", "detail": "予約一覧の取得に失敗しました"}), 500

        reservations = res_get.json().get("reservations", [])

        for r in reservations:
            if r.get("date") == date and r.get("time") == time:
                return jsonify({"status": "error", "detail": "その日時はすでに予約があります"}), 400

        # 重複なければ予約登録
        reservation = {
            "reservation": {
                "userId": data.get("userId"),
                "displayName": data.get("displayName"),
                "name": data.get("name"),
                "date": date,
                "time": time,
                "createdAt": datetime.now().isoformat()
            }
        }

        res_post = requests.post(SHEETY_URL, json=reservation, headers=headers)
        if res_post.status_code in [200, 201]:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "detail": res_post.text}), 400

    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500

@app.route("/reservations", methods=["GET"])
def get_reservations():
    date = request.args.get("date")

    headers = {
        "Authorization": f"Bearer {SHEETY_TOKEN}"
    }
    res = requests.get(SHEETY_URL, headers=headers)
    if res.status_code != 200:
        return jsonify({"status": "error", "detail": "予約一覧の取得に失敗しました"}), 500

    reservations = res.json().get("reservations", [])
    if date:
        reservations = [r for r in reservations if r.get("date") == date]

    return jsonify({"status": "success", "reservations": reservations})

if __name__ == "__main__":
    app.run(debug=True)
