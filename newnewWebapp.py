from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime
import os
import requests
from io import StringIO

# ================= CONFIG =================
EXCEL_FILE = "D:/WebApp/files/Slots.xlsx"  # Update path in your VM
LIVE_COUNT_FILE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiZ_zUqGTGWLCu4Adr3zH6i-phaXqsYPY467l99f1v3rpTLQr9HfKtbSWbfnJUMTPQ6Geq2HzSo_oe/pub?gid=0&single=true&output=csv"
QR_IMAGE_FILE = "/static/hovercode.png"  # file in static folder
YOUTUBE_VIDEO_ID = "eyjgAOBzeTE"  # your video ID
SLOT_SOUND_FILE = "/static/beep.mp3"  # optional slot change sound

app = Flask(__name__, static_folder="static", template_folder="templates")

# ================= LOAD SLOTS =================
def load_slots(file_path):
    if not os.path.exists(file_path):
        print(f"⚠️ Excel file not found at {file_path}. Using empty slots.")
        return pd.DataFrame(columns=["Start Time", "Lead Name", "Support Lead"])
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        if "Start Time" in df.columns:
            df["Start Time"] = pd.to_datetime(df["Start Time"], errors='coerce', infer_datetime_format=True)
            df = df.dropna(subset=["Start Time"]).reset_index(drop=True)
        else:
            print("⚠️ 'Start Time' column missing in Excel.")
        print(f"✅ Loaded {len(df)} slots from Excel")
        return df
    except Exception as e:
        print(f"⚠️ Error reading Excel file: {e}")
        return pd.DataFrame(columns=["Start Time", "Lead Name", "Support Lead"])

df = load_slots(EXCEL_FILE)

# ================= HELPERS =================
def slot_to_dict(s):
    """Convert slot row to dict with Lead, Support, Time."""
    if s is None or s.empty:
        return {"Lead Name": "-", "Support Lead": "-", "Time": "--"}
    slot_time = s.get("Start Time", None)
    if isinstance(slot_time, pd.Timestamp):
        time_str = slot_time.strftime("%I:%M %p")
    else:
        time_str = "--"
    return {
        "Lead Name": s.get("Lead Name", "-"),
        "Support Lead": s.get("Support Lead", "-"),
        "Time": time_str
    }

def find_current_slot():
    """Return index of current slot based on local time."""
    if df.empty:
        return 0
    now = datetime.now()
    current_slot_index = 0
    for i, row in df.iterrows():
        slot_time = row["Start Time"]
        if isinstance(slot_time, pd.Timestamp):
            if now >= slot_time:
                current_slot_index = i
            else:
                break
    return current_slot_index

def live_counter(csv_url: str) -> int:
    """Fetch total Surya Namaskar count from Google Sheet."""
    try:
        r = requests.get(csv_url)
        r.raise_for_status()
        df_count = pd.read_csv(StringIO(r.text))
        if 'Surya Namaskar Count' not in df_count.columns:
            return 0
        values = pd.to_numeric(df_count['Surya Namaskar Count'].iloc[1:1000], errors='coerce')
        return int(values.sum(skipna=True))
    except Exception as e:
        print(f"⚠️ Error fetching live count: {e}")
        return 0

# ================= ROUTES =================
@app.route("/")
def dashboard():
    slot = find_current_slot()
    prev_slot = slot_to_dict(df.iloc[slot-1] if slot>0 else None)
    curr_slot = slot_to_dict(df.iloc[slot] if slot is not None else None)
    next_slot = slot_to_dict(df.iloc[slot+1] if slot < len(df)-1 else None)
    count = live_counter(LIVE_COUNT_FILE)

    return render_template("dashboard.html",
        prev_slot=prev_slot,
        curr_slot=curr_slot,
        next_slot=next_slot,
        total_count=count,
        qr_path=QR_IMAGE_FILE,
        youtube_id=YOUTUBE_VIDEO_ID,
        slot_sound=SLOT_SOUND_FILE
    )

@app.route("/data")
def data():
    slot = find_current_slot()
    prev_slot = slot_to_dict(df.iloc[slot-1] if slot>0 else None)
    curr_slot = slot_to_dict(df.iloc[slot] if slot is not None else None)
    next_slot = slot_to_dict(df.iloc[slot+1] if slot < len(df)-1 else None)
    count = live_counter(LIVE_COUNT_FILE)

    return jsonify({
        "prev_slot": prev_slot,
        "curr_slot": curr_slot,
        "next_slot": next_slot,
        "total_count": count
    })

# ================= MAIN =================
if __name__ == "__main__":
    print("🚀 Starting Flask app...")
    app.run(host="0.0.0.0", port=5000, debug=True)
