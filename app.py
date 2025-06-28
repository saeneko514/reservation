from flask import Flask, render_template, request, redirect, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")

RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedules"

def send_line_message(user_id, message_text):
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=body
    )
    return response

@app.route('/')
def index():
    return render_template('select_staff_and_slots.html')  # 1画面完結版

@app.route('/api/available_slots')
def api_available_slots():
    staff = request.args.get('staff')
    response = requests.get(SCHEDULE_ENDPOINT)
    if response.status_code != 200:
        return jsonify({"slots": []}), 500

    all_schedules = response.json().get("schedules", [])
    filtered_slots = []

    for entry in all_schedules:
        if entry["staff"] == staff and entry["status"] == "○":
            datetime_str = f"{entry['date']} {entry['time']}"
            filtered_slots.append(datetime_str)

    return jsonify({"slots": filtered_slots})

@app.route('/book', methods=['POST'])
def book():
    staff = request.form['staff']
    datetime_str = request.form['datetime']
    user_name = request.form.get('userName', '名無しユーザー')
    user_id = request.form.get('userId', 'unknown_user')
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 予約記録
    data = {
        "reservation": {
            "userId": user_id,
            "name": user_name,
            "staff": staff,
            "date": datetime_str,
            "registration_date": registration_date
        }
    }
    response = requests.post(RESERVATION_ENDPOINT, json=data)

    # 予約成功ならスケジュールの status を × に更新
    if response.status_code in [200, 201]:
        date_part, time_part = datetime_str.split(' ')
        schedule_response = requests.get(SCHEDULE_ENDPOINT)
        if schedule_response.status_code == 200:
            schedules = schedule_response.json().get("schedules", [])
            for s in schedules:
                if s["staff"] == staff and s["date"] == date_part and s["time"] == time_part:
                    schedule_id = s["id"]
                    update_data = {"schedule": {"status": "×"}}
                    patch_url = f"{SCHEDULE_ENDPOINT}/{schedule_id}"
                    requests.patch(patch_url, json=update_data)
                    break

        return redirect('/')
    else:
        return f"予約に失敗しました（{response.status_code}）: {response.text}"

if __name__ == '__main__':
    app.run(debug=True)
