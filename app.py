from flask import Flask, render_template, request, redirect
import requests
from datetime import datetime
import os

app = Flask(__name__)

# 環境変数からShettyやLINEの設定を取得
SHEETY_ID = os.environ.get("SHEETY_ID")
CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")

# Sheetyのエンドポイント
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedules"

# LINEメッセージ送信関数
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
    return render_template('index.html')

@app.route('/select_staff')
def select_staff():
    return render_template('select_staff.html')

@app.route('/api/available_slots')
def api_available_slots():
    staff = request.args.get('staff')
    response = requests.get(SCHEDULE_ENDPOINT)
    if response.status_code != 200:
        return {"slots": []}, 500

    all_schedules = response.json().get("schedules", [])
    filtered_slots = []

    for entry in all_schedules:
        if entry["staff"] == staff and entry["status"] == "○":
            datetime_str = f"{entry['date']} {entry['time']}"
            filtered_slots.append(datetime_str)

    return {"slots": filtered_slots}
    

@app.route('/confirm_booking')
def confirm_booking():
    staff = request.args.get('staff')
    datetime_str = request.args.get('datetime')
    return render_template('confirm_booking.html', staff=staff, datetime=datetime_str)

@app.route('/book', methods=['POST'])
def book():
    staff = request.form['staff']
    datetime_str = request.form['datetime']
    user_name = request.form.get('userName', '名無しユーザー')
    user_id = request.form.get('userId', 'unknown_user')
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # スプレッドシートに予約を記録
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

    # status を × に更新
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

        # LINEに通知
        message_text = f"{user_name}さん、{staff}との予約が完了しました！\n日時：{datetime_str}"
        send_line_message(user_id, message_text)

        return redirect(f"/confirm_booking?staff={staff}&datetime={datetime_str}")
    else:
        return f"予約に失敗しました（{response.status_code}）: {response.text}"

if __name__ == '__main__':
    app.run(debug=True)
