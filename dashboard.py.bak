
from flask import Flask
from datetime import datetime, timezone, timedelta
app = Flask(__name__)
IST = timezone(timedelta(hours=5, minutes=30))
@app.route("/")
def home():
    ist=datetime.now(IST).strftime('%d-%m-%Y %H:%M:%S IST')
    return f"<html><body style='background:#000;color:#0f0;padding:20px;font-family:monospace'><h1>✅ FINAL AGENT LIVE</h1><h2>{ist}</h2><p>IST Fixed - UTC+5:30</p><p>Pipeline: Meta AI -> incoming_changes/ -> Agent (30s) -> Live</p><p>No GitHub needed, direct deploy</p><p>Time: {ist}</p></body></html>"
if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000)
