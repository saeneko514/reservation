from flask import Flask, request, render_template, redirect, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedule"

@app.route('/reserve', methods=['POST'])
def reserve():
    staff = request.form['staff']
    date = request.form['date']
    time = request.form['time']
    userId = request.form['userId']
    name = request.form['name']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. scheduleシートから該当スロットを検索してID取得
    res = requests.get(SHEETY_SCHEDULE_URL)
    schedule_data = res.json()['schedule']
    schedule_id = None
    for row in schedule_data:
        if row['staff'] == staff and row['date'] == date and row['time'] == time:
            schedule_id = row['id']
            break
    if not schedule_id:
        return "該当スケジュールが見つかりません", 400

    # 2. scheduleのstatusを"booked"に更新
    update_url = f"{SHEETY_SCHEDULE_URL}/{schedule_id}"
    requests.put(update_url, json={"schedule": {"status": "booked"}})

    # 3. reservationsシートに予約情報を追加
    reservation_data = {
        "reservation": {
            "userId": userId,
            "name": name,
            "staff": staff,
            "date": date,
            "time": time,
            "registrationDate": now
        }
    }
    requests.post(SHEETY_RESERVATION_URL, json=reservation_data)

    # 4. 予約完了メッセージなど（必要なら）

    # 5. リダイレクトなど
    return redirect(f"/schedule?staff={staff}")
