from flask import Flask, request, render_template, redirect, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

SHEETY_ID = os.environ.get("SHEETY_ID")
RESERVATION_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/reservations"
SCHEDULE_ENDPOINT = f"https://api.sheety.co/{SHEETY_ID}/カウンセリング予約/schedule"

@app.route('/schedule')
def get_schedule():
    staff = request.args.get('staff')  # 例: 山田

    # スプレッドシートから全データ取得
    response = requests.get(SHEETY_ENDPOINT)
    data = response.json()['schedule']

    # 指定スタッフの枠だけフィルター
    staff_schedule = [row for row in data if row['staff'] == staff]

    # 日付ごとに整理
    schedule_by_day = {}
    for row in staff_schedule:
        date = row['date']
        if date not in schedule_by_day:
            schedule_by_day[date] = []
        schedule_by_day[date].append({
            'time': row['time'],
            'status': row['status']
        })

    return render_template('schedule.html', staff=staff, schedule_by_day=schedule_by_day)
