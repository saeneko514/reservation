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
    # スタッフ選択と空き枠表示画面
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
        if entry["staff"] == staff and entry["status"] in ["〇", "○"]:
            time_short = entry['time'][:5]
            slot = f"{entry['date']} {time_short}"
            filtered_slots.append(slot)

    return jsonify({"slots": filtered_slots})

@app.route('/book', methods=['POST'])
def book():
    staff = request.form.get('staff')
    datetime_str = request.form.get('datetime')  # 例： "2025/07/01 14:00"
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

    # 予約登録（POST）
    response = requests.post(RESERVATION_ENDPOINT, json=data)
    if response.status_code not in [200, 201]:
        return f"予約に失敗しました（{response.status_code}）: {response.text}"

    # 予約した枠のstatusを「×」に更新する
    try:
        date_part, time_part = datetime_str.split(' ')  # date_part= "2025/07/01", time_part= "14:00"
    except Exception:
        return "予約日時の形式が不正です。"

    # SheetyのtimeはHH:MM:SSなので、time_partをHH:MM:SS形式に変換
    try:
        time_part_fmt = datetime.strptime(time_part, "%H:%M").strftime("%H:%M:%S")
    except ValueError:
        time_part_fmt = time_part  # 念のため元の文字列保持

    schedule_response = requests.get(SCHEDULE_ENDPOINT)
    if schedule_response.status_code == 200:
        schedules = schedule_response.json().get("schedules", [])
        for s in schedules:
            if s["staff"] == staff and s["date"] == date_part and s["time"] == time_part_fmt:
                schedule_id = s["id"]
                update_data = {"schedule": {"status": "×"}}
                patch_url = f"{SCHEDULE_ENDPOINT}/{schedule_id}"
                patch_response = requests.patch(patch_url, json=update_data)
                # ここでstatus更新結果を確認したい場合はpatch_responseの内容をログ出力可
                break

    return redirect(f'/confirm_booking?staff={staff}&datetime={datetime_str}')

@app.route('/confirm_booking')
def confirm_booking():
    staff = request.args.get('staff')
    datetime_str = request.args.get('datetime')
    return render_template('confirm_booking.html', staff=staff, datetime=datetime_str)

if __name__ == '__main__':
    app.run(debug=True)
