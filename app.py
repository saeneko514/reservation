from flask import Flask, request, render_template, redirect, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedules"

@app.route('/')
def index():
    return render_template('select_staff.html')

@app.route('/api/available_slots')
def available_slots():
    staff = request.args.get('staff')
    if not staff:
        return jsonify({"slots": []})

    response = requests.get(SCHEDULE_ENDPOINT)
    if response.status_code != 200:
        return jsonify({"slots": []})

    all_schedules = response.json().get("schedules", [])
    filtered_slots = []
    for entry in all_schedules:
        if entry["staff"] == staff and entry["status"] == "〇":
            slot = f"{entry['date']} {entry['time']}"
            filtered_slots.append(slot)
    return jsonify({"slots": filtered_slots})

@app.route('/book', methods=['POST'])
def book():
    staff = request.form.get('staff')
    datetime_str = request.form.get('datetime')
    user_name = request.form.get('userName', '名無しユーザー')
    user_id = request.form.get('userId', 'unknown_user')
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    data = {
        "reservation": {
            "userId": user_id,
            "name": user_name,
            "staff": staff,
            "date": datetime_str,
            "registration_date": registration_date
        }
    }

    # 予約登録
    response = requests.post(RESERVATION_ENDPOINT, json=data)
    if response.status_code not in [200, 201]:
        return f"予約に失敗しました（{response.status_code}）: {response.text}"

    # 予約した枠のstatusを「×」に更新
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

    # 予約完了画面へリダイレクト
    return redirect(f'/confirm_booking?staff={staff}&datetime={datetime_str}')

@app.route('/confirm_booking')
def confirm_booking():
    staff = request.args.get('staff')
    datetime_str = request.args.get('datetime')
    return render_template('confirm_booking.html', staff=staff, datetime=datetime_str)

if __name__ == '__main__':
    app.run(debug=True)
