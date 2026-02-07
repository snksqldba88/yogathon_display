# from flask import Flask, render_template_string, jsonify
# import pandas as pd
# from datetime import datetime, timedelta
# import platform
# import threading
# import time
#
# # ================= CONFIG =================
#
# EXCEL_FILE = r"C:\Users\pavithra\Downloads\Slots.xlsx"
# LIVE_COUNT_FILE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiZ_zUqGTGWLCu4Adr3zH6i-phaXqsYPY467l99f1v3rpTLQr9HfKtbSWbfnJUMTPQ6Geq2HzSo_oe/pub?gid=0&single=true&output=csv"
#
# # ================= LOAD DATA =================
#
# df = pd.read_excel(EXCEL_FILE)
# df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
# df = df.dropna(subset=["Start Time"]).reset_index(drop=True)
#
# # ================= SLOT FINDER =================
#
# def find_current_slot():
#     now = datetime.now()
#     slot = None
#     for i in range(len(df)):
#         if df.iloc[i]["Start Time"] <= now:
#             slot = i
#     return slot
#
# # ================= LIVE COUNT =================
#
# def live_counter(csv_url: str) -> int:
#     try:
#         dfc = pd.read_csv(csv_url)
#         if 'Surya Namaskar Count' not in dfc.columns:
#             return 0
#         values = pd.to_numeric(dfc['Surya Namaskar Count'].iloc[1:1000], errors='coerce')
#         return int(values.sum(skipna=True))
#     except:
#         return 0
#
# # ================= BACKGROUND UPDATER =================
#
# state = {
#     "prev": ("-", "-"),
#     "curr": ("-", "-"),
#     "next": ("-", "-"),
#     "countdown": "Event Not Started",
#     "progress": 0,
#     "clock": "",
#     "live": 0
# }
#
#
# def updater():
#     while True:
#         slot = find_current_slot()
#         now = datetime.now()
#
#         if slot is None:
#             state["countdown"] = "Event Not Started"
#         else:
#             state["prev"] = (
#                 df.iloc[slot-1]["Lead Name"] if slot > 0 else "-",
#                 df.iloc[slot-1]["Support Lead"] if slot > 0 else "-"
#             )
#             state["curr"] = (
#                 df.iloc[slot]["Lead Name"],
#                 df.iloc[slot]["Support Lead"]
#             )
#             state["next"] = (
#                 df.iloc[slot+1]["Lead Name"] if slot < len(df)-1 else "-",
#                 df.iloc[slot+1]["Support Lead"] if slot < len(df)-1 else "-"
#             )
#
#             if slot < len(df)-1:
#                 next_time = df.iloc[slot+1]["Start Time"]
#                 remaining = next_time - now
#                 if remaining.total_seconds() < 0:
#                     remaining = timedelta(seconds=0)
#                 state["countdown"] = str(remaining).split(".")[0]
#             else:
#                 state["countdown"] = "Event Finished"
#
#             state["progress"] = round(((slot + 1) / len(df)) * 100, 2)
#
#         state["clock"] = now.strftime("%I:%M:%S %p")
#         state["live"] = live_counter(LIVE_COUNT_FILE)
#
#         time.sleep(1)
#
#
# threading.Thread(target=updater, daemon=True).start()
#
# # ================= FLASK APP =================
#
# app = Flask(__name__)
#
# TEMPLATE = '''
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Event Control Dashboard</title>
#     <style>
#         body { font-family: Segoe UI, Arial; background:#f4f6f7; margin:0; }
#         .container { display:flex; height:100vh; }
#         .left, .right { flex:1; padding:20px; }
#         .block { background:white; border-radius:12px; padding:15px; margin-bottom:15px; }
#         .title { font-size:26px; font-weight:bold; }
#         .value { font-size:34px; font-weight:bold; }
#         .clock { font-size:30px; text-align:center; }
#         .countdown { font-size:28px; text-align:center; color:red; }
#         .progress { height:24px; background:#ddd; border-radius:12px; overflow:hidden; }
#         .progress-bar { height:100%; background:#4CAF50; width:0%; }
#     </style>
# </head>
# <body>
# <div class="container">
#     <div class="left">
#         <div class="clock" id="clock"></div>
#         <div class="countdown" id="countdown"></div>
#         <div class="progress"><div class="progress-bar" id="bar"></div></div>
#
#         <div class="block">
#             <div class="title">PREVIOUS SLOT</div>
#             <div class="value" id="prev_lead"></div>
#             <div id="prev_support"></div>
#         </div>
#         <div class="block" style="background:#d0e6ff">
#             <div class="title">CURRENT SLOT</div>
#             <div class="value" id="curr_lead"></div>
#             <div id="curr_support"></div>
#         </div>
#         <div class="block" style="background:#dbf2d3">
#             <div class="title">NEXT SLOT</div>
#             <div class="value" id="next_lead"></div>
#             <div id="next_support"></div>
#         </div>
#     </div>
#
#     <div class="right">
#         <h2>INSTRUCTIONS</h2>
#         <p>
#         1) Please enable your Video throughout the slot.<br>
#         2) Follow the previous/current/next slot display.<br>
#         3) Start only once your slot begins.<br>
#         4) Inform coordinator if next person hasn't joined.<br>
#         5) Scan QR code and submit your count.
#         </p>
#
#         <h2>Total Surya Namaskar</h2>
#         <div style="font-size:60px; color:green;" id="live"></div>
#     </div>
# </div>
#
# <script>
# async function refreshData(){
#     const r = await fetch('/api/data');
#     const d = await r.json();
#
#     document.getElementById('clock').innerText = d.clock;
#     document.getElementById('countdown').innerText = d.countdown;
#     document.getElementById('bar').style.width = d.progress + '%';
#
#     document.getElementById('prev_lead').innerText = d.prev[0];
#     document.getElementById('prev_support').innerText = d.prev[1];
#     document.getElementById('curr_lead').innerText = d.curr[0];
#     document.getElementById('curr_support').innerText = d.curr[1];
#     document.getElementById('next_lead').innerText = d.next[0];
#     document.getElementById('next_support').innerText = d.next[1];
#     document.getElementById('live').innerText = d.live;
# }
#
# setInterval(refreshData, 1000);
# refreshData();
# </script>
# </body>
# </html>
# '''
#
# @app.route("/")
# def index():
#     return render_template_string(TEMPLATE)
#
# @app.route("/api/data")
# def api_data():
#     return jsonify(state)
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, render_template_string, jsonify
import pandas as pd
from datetime import datetime, timedelta
import platform
import threading
import time

# ================= CONFIG =================

EXCEL_FILE = r"C:\Users\pavithra\Downloads\Slots.xlsx"
LIVE_COUNT_FILE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiZ_zUqGTGWLCu4Adr3zH6i-phaXqsYPY467l99f1v3rpTLQr9HfKtbSWbfnJUMTPQ6Geq2HzSo_oe/pub?gid=0&single=true&output=csv"

# ================= LOAD DATA =================

df = pd.read_excel(EXCEL_FILE)
df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce")
df = df.dropna(subset=["Start Time"]).reset_index(drop=True)

# ================= SLOT FINDER =================

def find_current_slot():
    now = datetime.now()
    slot = None
    for i in range(len(df)):
        if df.iloc[i]["Start Time"] <= now:
            slot = i
    return slot

# ================= LIVE COUNT =================

def live_counter(csv_url: str) -> int:
    try:
        dfc = pd.read_csv(csv_url)
        if 'Surya Namaskar Count' not in dfc.columns:
            return 0
        values = pd.to_numeric(dfc['Surya Namaskar Count'].iloc[1:1000], errors='coerce')
        return int(values.sum(skipna=True))
    except:
        return 0

# ================= BACKGROUND UPDATER =================

state = {
    "prev": ("-", "-"),
    "curr": ("-", "-"),
    "next": ("-", "-"),
    "countdown": "Event Not Started",
    "progress": 0,
    "clock": "",
    "live": 0
}


def updater():
    while True:
        slot = find_current_slot()
        now = datetime.now()

        if slot is None:
            state["countdown"] = "Event Not Started"
        else:
            state["prev"] = (
                df.iloc[slot-1]["Lead Name"] if slot > 0 else "-",
                df.iloc[slot-1]["Support Lead"] if slot > 0 else "-"
            )
            state["curr"] = (
                df.iloc[slot]["Lead Name"],
                df.iloc[slot]["Support Lead"]
            )
            state["next"] = (
                df.iloc[slot+1]["Lead Name"] if slot < len(df)-1 else "-",
                df.iloc[slot+1]["Support Lead"] if slot < len(df)-1 else "-"
            )

            if slot < len(df)-1:
                next_time = df.iloc[slot+1]["Start Time"]
                remaining = next_time - now
                if remaining.total_seconds() < 0:
                    remaining = timedelta(seconds=0)
                state["countdown"] = str(remaining).split(".")[0]
            else:
                state["countdown"] = "Event Finished"

            state["progress"] = round(((slot + 1) / len(df)) * 100, 2)

        state["clock"] = now.strftime("%I:%M:%S %p")
        state["live"] = live_counter(LIVE_COUNT_FILE)

        time.sleep(1)


threading.Thread(target=updater, daemon=True).start()

# ================= FLASK APP =================

app = Flask(__name__, static_folder="static")

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Event Control Dashboard</title>
    <style>
        body { font-family: Segoe UI, Arial; background:#f4f6f7; margin:0; }
        .container { display:flex; height:100vh; }
        .left, .right { flex:1; padding:20px; }
        .block { background:white; border-radius:12px; padding:15px; margin-bottom:15px; }
        .title { font-size:26px; font-weight:bold; }
        .value { font-size:34px; font-weight:bold; }
        .clock { font-size:30px; text-align:center; }
        .countdown { font-size:28px; text-align:center; color:red; }
        .progress { height:24px; background:#ddd; border-radius:12px; overflow:hidden; }
        .progress-bar { height:100%; background:#4CAF50; width:0%; }
    </style>
</head>
<body>
<div class="container">
    <div class="left">
        <div class="clock" id="clock"></div>
        <div class="countdown" id="countdown"></div>
        <div class="progress"><div class="progress-bar" id="bar"></div></div>

        <div class="block">
            <div class="title">PREVIOUS SLOT</div>
            <div class="value" id="prev_lead"></div>
            <div id="prev_support"></div>
        </div>
        <div class="block" style="background:#d0e6ff">
            <div class="title">CURRENT SLOT</div>
            <div class="value" id="curr_lead"></div>
            <div id="curr_support"></div>
        </div>
        <div class="block" style="background:#dbf2d3">
            <div class="title">NEXT SLOT</div>
            <div class="value" id="next_lead"></div>
            <div id="next_support"></div>
        </div>
    </div>

    <div class="right">
        <h2>INSTRUCTIONS</h2>
        <p>
        1) Please enable your Video throughout the slot.<br>
        2) Follow the previous/current/next slot display.<br>
        3) Start only once your slot begins.<br>
        4) Inform coordinator if next person hasn't joined.<br>
        5) Scan QR code and submit your count.
        </p>

        <img src="/static/hovercode.png" width="260"><br><br>

        <h2>Total Surya Namaskar</h2>
        <div style="font-size:60px; color:green;" id="live"></div>
    </div>
</div>

<script>
async function refreshData(){
    const r = await fetch('/api/data');
    const d = await r.json();

    document.getElementById('clock').innerText = d.clock;
    document.getElementById('countdown').innerText = d.countdown;
    document.getElementById('bar').style.width = d.progress + '%';

    document.getElementById('prev_lead').innerText = d.prev[0];
    document.getElementById('prev_support').innerText = d.prev[1];
    document.getElementById('curr_lead').innerText = d.curr[0];
    document.getElementById('curr_support').innerText = d.curr[1];
    document.getElementById('next_lead').innerText = d.next[0];
    document.getElementById('next_support').innerText = d.next[1];
    document.getElementById('live').innerText = d.live;
}

setInterval(refreshData, 1000);
refreshData();
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/api/data")
def api_data():
    return jsonify(state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
