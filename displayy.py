from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime
import pytz
import os

# ================= CONFIG =================
EXCEL_FILE = "/home/ubuntu/yogathon_display/files/Slots.xlsx"
LIVE_COUNT_FILE = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSiZ_zUqGTGWLCu4Adr3zH6i-phaXqsYPY467l99f1v3rpTLQr9HfKtbSWbfnJUMTPQ6Geq2HzSo_oe/pub?gid=0&single=true&output=csv"
QR_IMAGE_FILE = "hovercode.png"
YOUTUBE_VIDEO_ID = "eyjgAOBzeTE"

TIMEZONE = pytz.timezone("America/New_York")

app = Flask(__name__, static_folder="static", template_folder="templates")

# ================= LOAD SLOTS =================
def load_slots(file_path):
    if not os.path.exists(file_path):
        print("Excel file missing")
        return pd.DataFrame()

    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()

    today = datetime.now(TIMEZONE).date()

    df["Start Time"] = pd.to_datetime(df["Start Time"], errors="coerce").dt.time

    df["Start DateTime"] = df["Start Time"].apply(
        lambda t: TIMEZONE.localize(datetime.combine(today, t)) if pd.notna(t) else None
            )

    df = df.dropna(subset=["Start DateTime"])
    df = df.sort_values("Start DateTime").reset_index(drop=True)

    print("Slots Loaded:\n", df[["Start Time","Lead Name","Support Lead"]].head())

    return df


df = load_slots(EXCEL_FILE)

EVENT_START = df["Start Time"].min()
EVENT_END   = df["Start Time"].max()

# ================= HELPERS =================
def format_time(dt):
    return dt.strftime("%I:%M %p") if pd.notna(dt) else "-"


def slot_to_dict(s):
    if s is None or s.empty:
        return {"time":"-","lead":"-","support":"-"}

    return {
        "time": format_time(s["Start DateTime"]),
        "lead": str(s.get("Lead Name","-")),
        "support": str(s.get("Support Lead","-"))
    }


def find_current_slot():
    if df.empty:
        return 0

    now = datetime.now(TIMEZONE)

    idx = 0
    for i, row in df.iterrows():
        if now >= row["Start DateTime"]:
            idx = i
        else:
            break

    return idx


def live_counter(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        if "Surya Namaskar Count" not in df.columns:
            print("Sheet Columns:", df.columns.tolist())
            return 0

        values = pd.to_numeric(df["Surya Namaskar Count"], errors="coerce")
        return int(values.sum(skipna=True))

    except Exception as e:
        print("Google sheet error:", e)
        return 0


# ================= ROUTES =================
@app.route("/")
def dashboard():
    slot = find_current_slot()

    return render_template("dashboard.html",
        prev = slot_to_dict(df.iloc[slot-1] if slot>0 else None),
        curr = slot_to_dict(df.iloc[slot] if slot<len(df) else None),
        next = slot_to_dict(df.iloc[slot+1] if slot<len(df)-1 else None),
        total_count = live_counter(LIVE_COUNT_FILE),
        event_start = EVENT_START.isoformat(),
        event_end   = EVENT_END.isoformat(),
        qr_path     = QR_IMAGE_FILE,
        youtube_id = YOUTUBE_VIDEO_ID
    )

@app.route("/data")
def data():
    slot = find_current_slot()
    return jsonify({
        "prev": slot_to_dict(df.iloc[slot-1] if slot>0 else None),
        "curr": slot_to_dict(df.iloc[slot] if slot<len(df) else None),
        "next": slot_to_dict(df.iloc[slot+1] if slot<len(df)-1 else None),
        "total": live_counter(LIVE_COUNT_FILE),
        "slot_index": slot
    })

# ================= MAIN =================
if __name__ == "__main__":
    print("🚀 Dashboard running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)

