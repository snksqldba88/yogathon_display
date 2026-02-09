from flask import Flask, render_template, jsonify, url_for
import pandas as pd
from datetime import datetime, time
import os

# ================= CONFIG =================
EXCEL_FILE = "D:/WebApp/files/Slots.xlsx"
LIVE_COUNT_FILE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiZ_zUqGTGWLCu4Adr3zH6i-phaXqsYPY467l99f1v3rpTLQr9HfKtbSWbfnJUMTPQ6Geq2HzSo_oe/pub?gid=0&single=true&output=csv"
QR_IMAGE_FILE = "hovercode.png"

app = Flask(__name__, static_folder="static", template_folder="templates")

# ================= LOAD SLOTS =================
def load_slots(file_path):
    if not os.path.exists(file_path):
        print(f"⚠️ Excel file not found at {file_path}. Using empty slots.")
        return pd.DataFrame(columns=["Lead Name", "Support Lead", "Start Time"])
    try:
        df = pd.read_excel(file_path)
        df.columns = df.columns.str.strip()
        # convert Start Time safely
        if "Start Time" in df.columns:
            df["Start Time"] = pd.to_datetime(df["Start Time"], errors='coerce', infer_datetime_format=True)
            # if all NaT, fallback to parsing as time only
            if df["Start Time"].isna().all():
                df["Start Time"] = pd.to_datetime(df["Start Time"].astype(str), format="%H:%M", errors="coerce")
            df = df.dropna(subset=["Start Time"]).reset_index(drop=True)
        else:
            print("⚠️ 'Start Time' column missing in Excel.")
        print(f"✅ Loaded {len(df)} slots from Excel")
        return df
    except Exception as e:
        print(f"⚠️ Error reading Excel file: {e}")
        return pd.DataFrame(columns=["Lead Name", "Support Lead", "Start Time"])

df = load_slots(EXCEL_FILE)

# ================= EVENT TIME =================
EVENT_START = df["Start Time"].min() if not df.empty else None
EVENT_END = df["Start Time"].max() if not df.empty else None

# ================= HELPERS =================
def slot_to_dict(s):
    if s is None or s.empty:
        return {"Lead Name": "-", "Support Lead": "-"}
    return {"Lead Name": s.get("Lead Name", "-"), "Support Lead": s.get("Support Lead", "-")}

def find_current_slot():
    if df.empty:
        return None
    now = datetime.now()
    # compute slot based on time only (hour and minute)
    current_slot_index = 0
    for i, row in df.iterrows():
        slot_time = row["Start Time"]
        # if slot_time has a date, compare full datetime
        if isinstance(slot_time, pd.Timestamp):
            if now >= slot_time:
                current_slot_index = i
            else:
                break
        else:
            # fallback: just compare hour and minute
            slot_time_only = time(slot_time.hour, slot_time.minute)
            now_time_only = time(now.hour, now.minute)
            if now_time_only >= slot_time_only:
                current_slot_index = i
            else:
                break
    return current_slot_index

def live_counter(csv_url: str) -> int:
    try:
        df_count = pd.read_csv(csv_url)
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
        event_start=EVENT_START,
        event_end=EVENT_END
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
