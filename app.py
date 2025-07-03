from flask import Flask, request, render_template, redirect
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedule"

TIME_SLOTS = [f"{h:02}:00:00" for h in range(10, 19)]  # 10:00:00～18:00:00

# LIFFからの最初のエントリー（index.html）
@app.route('/')
def index():
    return render_template('index.html')  # LIFF初期画面（LIFF SDKでユーザー情報取得）

# スタッフ選択画面
@app.route('/select_staff')
def select_staff():
    userId = request.args.get('userId')
    name = request.args.get('name')
    if not userId or not name:
        return "ユーザー情報が不足しています", 400
    return render_template('select_staff.html', userId=userId, name=name)

# スケジュール表示画面
@app.route('/schedule')
def schedule():
    staff = request.args.get('staff')
    userId = request.args.get('userId')
    name = request.args.get('name')
    if not staff or not userId or not name:
        return "パラメータ不足", 400

    res = requests.get(SCHEDULE_ENDPOINT)
    if res.status_code != 200:
        return "スケジュール取得エラー", 500

    data = res.json().get('schedule', [])
    filtered = [r for r in data if r['staff'] == staff]
    dates = sorted(set(r['date'] for r in filtered))

    # テーブル作成：時間×日付でステータスをセット
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

    return render_template('table_schedule.html',
                           staff=staff, dates=dates, table=table,
                           userId=userId, name=name)

# 予約登録処理
@app.route('/reserve', methods=['POST'])
def reserve():
    staff = request.form['staff']
    date = request.form['date']
    time = request.form['time']
    userId = request.form['userId']
    name = request.form['name']
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # スケジュールデータ取得
    res = requests.get(SCHEDULE_ENDPOINT)
    if res.status_code != 200:
        return "スケジュール取得失敗", 500
    schedule_data = res.json().get('schedule', [])

    # 該当スケジュール行を探す
    schedule_row = None
    for row in schedule_data:
        if row['staff'] == staff and row['date'] == date:
            schedule_row = row
            break
    if not schedule_row:
        return "該当スケジュールが見つかりません", 400

    schedule_id = schedule_row['id']

    # 時間列を「×」に更新
    update_url = f"{SCHEDULE_ENDPOINT}/{schedule_id}"
    update_data = {"schedule": {time: "×"}}
    res = requests.put(update_url, json=update_data)
    if res.status_code != 200:
        return f"スケジュール更新に失敗しました: {res.text}", 500

    # 予約シートに追加
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
    if res.status_code not in (200, 201):
        return f"予約登録に失敗しました: {res.text}", 500

    # 予約完了後はスケジュール画面に戻る（同じユーザー情報付き）
    return redirect(f"/schedule?staff={staff}&userId={userId}&name={name}")

if __name__ == '__main__':
    app.run(debug=True)
