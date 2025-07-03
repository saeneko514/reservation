from flask import Flask, request, render_template, redirect
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedule"

# 秒まで含んだ時間帯リスト（例：10:00:00）
TIME_SLOTS = [f"{h:02}:00:00" for h in range(10, 19)]

@app.route('/')
def index():
    return render_template('index.html')  # スタッフ選択ページ

@app.route('/schedule')
def schedule():
    staff = request.args.get('staff')
    if not staff:
        return "スタッフが指定されていません", 400

    res = requests.get(SCHEDULE_ENDPOINT)
    if res.status_code != 200:
        return f"スケジュール取得エラー: {res.text}", 500

    data = res.json().get('schedule')
    if not data:
        return "スケジュールデータが取得できません", 500

    filtered = [r for r in data if r['staff'] == staff]
    if not filtered:
        return f"スタッフ {staff} のスケジュールが見つかりません", 404

    dates = sorted(set(r['date'] for r in filtered))

    table = {}
    for time in TIME_SLOTS:
        table[time] = {}
        for row in filtered:
            date = row['date']
            status = row.get(time, '')
            if status == "○":
                table[time][date] = "available"
            elif status == "×":
                table[time][date] = "booked"
            else:
                table[time][date] = "none"

    return render_template('table_schedule.html', staff=staff, dates=dates, table=table)


@app.route('/reserve', methods=['POST'])
def reserve():
    staff = request.form['staff']
    date = request.form['date']
    time = request.form['time']
    userId = request.form['userId']
    name = request.form['name']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. scheduleシートから該当行を取得（staffとdateが合うもの）
    res = requests.get(SCHEDULE_ENDPOINT)
    if res.status_code != 200:
        return f"スケジュール取得エラー: {res.text}", 500
    schedule_data = res.json().get('schedule')

    schedule_row = None
    for row in schedule_data:
        if row['staff'] == staff and row['date'] == date:
            schedule_row = row
            break
    if not schedule_row:
        return "該当スケジュールが見つかりません", 400

    schedule_id = schedule_row['id']

    # 2. 該当時間の列を"×"に更新
    update_url = f"{SCHEDULE_ENDPOINT}/{schedule_id}"
    update_data = {
        "schedule": {
            time: "×"
        }
    }
    res = requests.put(update_url, json=update_data)
    if res.status_code != 200:
        return f"スケジュール更新に失敗しました: {res.text}", 500

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
    res = requests.post(RESERVATION_ENDPOINT, json=reservation_data)
    if res.status_code != 201:
        return f"予約登録に失敗しました: {res.text}", 500

    # 4. 予約完了後はスケジュール画面にリダイレクト
    return redirect(f"/schedule?staff={staff}")

if __name__ == '__main__':
    app.run(debug=True)
