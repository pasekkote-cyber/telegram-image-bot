# main.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Flask работает!"

@app.route("/setwebhook")
def set_webhook():
    return "🛠 Webhook setup page"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 5000)))
