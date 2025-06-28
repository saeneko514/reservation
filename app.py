from flask import Flask, render_template, request, redirect, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# APIエンドポイント
RESERVATION_ENDPOINT = "https://api.sheety.co/xxx/reservations"
SCHEDULE_ENDPOINT = "https://api.sheety.co/xxx/schedules"

@app.route("/")
def index():
    return render_template("select_staff.html")

@app.route("/api/available_slots")
def available_slots():
    staff = request.args.get("staff")
    response = requests.get(SCHEDULE_ENDPOINT)
    if response.status_code == 200:
        schedules = response.json().get("schedules", [])
        available = [f"{s['date']} {s['time'][:5]}" for s in schedules if s['staff'] == staff and s['status'] == "○"]
        return jsonify({"slots": available})
    return jsonify({"slots": []})

@app.route("/book", methods=["POST"])
def book():
    staff = request.form["staff"]
    datetime_str = request.form["datetime"]
    user_name = request.form.get("userName", "")
    user_id = request.form.get("userId", "")

    reservation_data = {
        "reservation": {
            "userId": user_id,
            "name": user_name,
            "staff": staff,
            "date": datetime_str,
            "registration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }

    response = requests.post(RESERVATION_ENDPOINT, json=reservation_data)

    if response.status_code in [200, 201]:
        date_part, time_part = datetime_str.split(' ')
        time_part = datetime.strptime(time_part, "%H:%M").strftime("%H:%M")

        schedule_response = requests.get(SCHEDULE_ENDPOINT)
        if schedule_response.status_code == 200:
            schedules = schedule_response.json().get("schedules", [])
            for s in schedules:
                try:
                    sheet_time = datetime.strptime(s["time"], "%H:%M:%S").strftime("%H:%M")
                except ValueError:
                    sheet_time = s["time"]

                if s["staff"] == staff and s["date"] == date_part and sheet_time == time_part:
                    schedule_id = s["id"]
                    update_data = {"schedule": {"status": "×"}}
                    patch_url = f"{SCHEDULE_ENDPOINT}/{schedule_id}"
                    patch_response = requests.patch(patch_url, json=update_data)
                    print("スケジュール更新結果:", patch_response.status_code, patch_response.text)
                    break

        return redirect(f"/confirm_booking?staff={staff}&datetime={datetime_str}")
    else:
        return f"予約に失敗しました（{response.status_code}）: {response.text}"

@app.route("/confirm_booking")
def confirm_booking():
    staff = request.args.get("staff")
    datetime_str = request.args.get("datetime")
    return render_template("confirm_booking.html", staff=staff, datetime=datetime_str)

if __name__ == "__main__":
    app.run(debug=True)
