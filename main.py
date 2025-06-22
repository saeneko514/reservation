from flask import Flask, request, jsonify, render_template_string
import requests
from datetime import datetime
import os

app = Flask(__name__)


SHEETY_TOKEN = os.environ.get("SHEETY_TOKEN")
SHEETY_URL = "https://api.sheety.co/91a51e4efb03bbce4a21258eebc3ae12/reservations/reservations"

# --- フロント（HTML） ---
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>来店予約</title>
  <script src="https://static.line-scdn.net/liff/edge/2/sdk.js"></script>
</head>
<body>
  <h2>来店予約フォーム</h2>
  <form id="form">
    <input type="text" id="name" placeholder="名前" required><br><br>
    <input type="date" id="date" required><br><br>
    <input type="time" id="time" required><br><br>
    <button type="submit">予約する</button>
  </form>

  <script>
    const API_URL = "/reserve";

    async function init() {
      await liff.init({ liffId: "2007620165-P4vJlaxa" }); //

      if (!liff.isLoggedIn()) liff.login();

      const profile = await liff.getProfile();
      const userId = liff.getContext().userId;

      document.getElementById("form").addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
          userId: userId,
          displayName: profile.displayName,
          name: document.getElementById("name").value,
          date: document.getElementById("date").value,
          time: document.getElementById("time").value
        };

        const res = await fetch(API_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        const result = await res.json();
        if (result.status === "success") {
          alert("予約が完了しました！");
          liff.closeWindow();
        } else {
          alert("エラー：" + result.detail);
        }
      });
    }

    init();
  </script>
</body>
</html>
"""

# --- フォーム表示用ルート ---
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_FORM)

# --- 予約データ受け取りAPI ---
@app.route("/reserve", methods=["POST"])
def reserve():
    data = request.json

    reservation = {
        "reservation": {
            "userId": data["userId"],
            "displayName": data["displayName"],
            "name": data["name"],
            "date": data["date"],
            "time": data["time"],
            "createdAt": datetime.now().isoformat()
        }
    }

    headers = {
        "Authorization": f"Bearer {SHEETY_TOKEN}",
        "Content-Type": "application/json"
    }

    res = requests.post(SHEETY_URL, json=reservation, headers=headers)
    if res.status_code == 201:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "detail": res.text}), 400
