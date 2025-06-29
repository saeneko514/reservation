from flask import Flask, request, render_template, redirect, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedule"

@app.route('/')
def index():
    return render_template('index.html')  # トップ画面用のテンプレート


@app.route('/schedule')
def schedule():
    staff = request.args.get('staff')
    res = requests.get(SCHEDULE_ENDPOINT)
    data = res.json()['schedule']

    # staffで絞り込み
    filtered = [r for r in data if r['staff'] == staff]

    # 日付一覧を取得（重複除去＆ソート）
    dates = sorted(set(r['date'] for r in filtered))

    # 時間帯一覧（10:00〜23:00想定）
    time_slots = [f"{h:02}:00" for h in range(10, 24)]

    # 表形式データ作成（時間×日付でstatusをセット）
    table = {}
    for time in time_slots:
        table[time] = {}
        for date in dates:
            slot = next((r for r in filtered if r['date'] == date and r['time'] == time), None)
            table[time][date] = slot['status'] if slot else 'none'

    return render_template('table_schedule.html', staff=staff, dates=dates, table=table)


@app.route('/reserve', methods=['POST'])
def reserve():
    staff = request.form['staff']
    date = request.form['date']
    time = request.form['time']
    userId = request.form['userId']
    name = request.form['name']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. scheduleシートから該当スロットを検索してID取得
    res = requests.get(SCHEDULE_ENDPOINT)
    schedule_data = res.json()['schedule']
    schedule_id = None
    for row in schedule_data:
        if row['staff'] == staff and row['date'] == date and row['time'] == time:
            schedule_id = row['id']
            break
    if not schedule_id:
        return "該当スケジュールが見つかりません", 400

    # 2. scheduleのstatusを"booked"に更新
    update_url = f"{SCHEDULE_ENDPOINT}/{schedule_id}"
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
    requests.post(RESERVATION_ENDPOINT, json=reservation_data)

    # 4. 予約完了メッセージなど（必要なら）

    # 5. リダイレクトなど
    return redirect(f"/schedule?staff={staff}")
