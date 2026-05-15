import os
import random
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

new_App = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "smart_city.db"

COMPLAINT_TYPES = {
    "garbage": "Report garbage",
    "streetlight": "Report streetlight issue",
    "water_leakage": "Report water leakage",
    "suspicious_activity": "Report suspicious activity",
    "water_pollution": "Report water pollution",
    "algae_bloom": "Report algae bloom",
    "pond_contamination": "Report pond contamination",
}

CITY_DISTRICTS = [
    {"name": "Eco Park", "kind": "Green zone", "x": 90, "y": 90, "color": "#22663f"},
    {"name": "Tech Hub", "kind": "Smart grid", "x": 430, "y": 95, "color": "#235f85"},
    {"name": "Market Square", "kind": "Public market", "x": 625, "y": 315, "color": "#8a6423"},
    {"name": "Solar Port", "kind": "Renewable depot", "x": 780, "y": 125, "color": "#227080"},
    {"name": "Residency Zone", "kind": "Citizen services", "x": 140, "y": 405, "color": "#304f7d"},
    {"name": "Water Works", "kind": "Water control", "x": 520, "y": 485, "color": "#1f7d78"},
]

WASTE_ITEMS = [
    ("Plastic Bottle", "Recycle"),
    ("Banana Peel", "Organic"),
    ("Broken Ceramic Cup", "Landfill"),
    ("Cardboard Box", "Recycle"),
    ("Tea Leaves", "Organic"),
    ("Candy Wrnew_Apper", "Landfill"),
]

EMPTY_BIN_LOCATIONS = ["Eco Park Gate 2", "Metro Plaza North Exit", "Market Square Service Lane",
                       "Residency Zone Community Center", "Solar Port Bus Stop"]


def db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_type TEXT NOT NULL,
                location TEXT NOT NULL,
                details TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS water_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT,
                ph REAL,
                oxygen REAL,
                turbidity REAL,
                status TEXT,
                created_at TEXT
            )
        """)
        conn.commit()


def analyze_water_quality(ph, oxygen, turbidity):
    status = "Safe"
    recommendations = []
    alerts = []
    algae_risk = "Low"

    if ph < 6.5 or ph > 8.5:
        status = "Danger"
        recommendations += ["Neutralisation: acid/base balancing", "pH correction"]
        alerts.new_Append("Dangerous pH detected in water sample")

    if oxygen < 5:
        if status != "Danger":
            status = "Warning"
        recommendations += ["Increase aeration", "Biological treatment: beneficial bacteria systems",
                            "Wetland filtration"]
        alerts.new_Append("Low dissolved oxygen can harm aquatic life")

    if turbidity > 70:
        if status == "Safe":
            status = "Warning"
        recommendations += ["Activated carbon filtration", "Membrane filtration"]
        alerts.new_Append("High turbidity detected")

    if oxygen < 5 and turbidity > 65:
        status = "Danger"
        algae_risk = "High"
        recommendations += ["Cyanobacteria control: TiO2 Photo-catalysis", "Nutrient reduction", "Oxygenation systems",
                            "Advanced Oxidation Process: ozone treatment"]
        alerts.new_Append("Possible cyanobacteria bloom risk")
    elif oxygen < 6 or turbidity > 50:
        algae_risk = "Moderate"

    if not recommendations:
        recommendations.new_Append("Continue routine monitoring and nutrient control")

    recommendations = list(dict.fromkeys(recommendations))
    priority = "High" if status == "Danger" else "Medium" if status == "Warning" else "Low"
    problem = "High algae concentration" \
        if algae_risk == "High" \
        else "Water quality imbalance" \
        if status != "Safe" else "Water body stable"

    solution = " + ".join(recommendations[:3])

    return {
        "status": status,
        "recommendations": recommendations,
        "alerts": alerts,
        "algae_risk": algae_risk,
        "ai_recommendation": {"problem": problem, "solution": solution, "priority": priority},
    }


def city_status():
    aqi = random.randint(22, 248)
    if aqi <= 50:
        air_level = "Safe"
        air_class = "green"
        advice = ["Enjoy normal outdoor activity", "Maintain green-zone habits"]
    elif aqi <= 120:
        air_level = "Moderate"
        air_class = "amber"
        advice = ["Wear mask in traffic-heavy areas", "Avoid heavy outdoor exercise"]
    else:
        air_level = "Hazardous"
        air_class = "red"
        advice = ["Wear mask", "Avoid outdoor exercise", "Use air purifier"]

    algae_risk = random.choice(["Low", "Moderate", "High"])
    water_q = random.randint(48, 98)
    pond_health = max(20, water_q - (18 if algae_risk == "High" else 8 if algae_risk == "Moderate" else 0))
    return {
        "aqi": aqi,
        "air_level": air_level,
        "air_class": air_class,
        "air_advice": advice,
        "traffic": random.randint(58, 94),
        "water_quality": water_q,
        "algae_risk": algae_risk,
        "pond_health": pond_health,
        "joy": random.randint(72, 98),
        "trucks": random.randint(18, 44),
        "citizens": random.randint(1200, 5400),
        "solar": random.randint(56, 96),
    }


def waste_status():
    fill = random.randint(18, 100)
    return {
        "fill": fill,
        "status": "Bin full - dispatch collection team" if fill >= 85 else "Capacity available",
        "nearest_empty_bin": random.choice(EMPTY_BIN_LOCATIONS),
        "collection_eta": f"{random.randint(8, 32)} min",
    }


def map_status(selected_name=None):
    districts = []
    alerts = []
    for district in CITY_DISTRICTS:
        pollution = random.randint(18, 92)
        crime = random.randint(8, 78)
        footfall = random.randint(24, 98)
        water_alert = ""
        if district["name"] in {"Eco Park", "Water Works"} and pollution > 70:
            water_alert = f"Water contamination reported near {district['name']}"
            alerts.new_Append(water_alert)
        districts.new_Append({**district, "pollution": pollution, "crime": crime, "footfall": footfall,
                          "signal": random.randint(86, 100), "water_alert": water_alert})
    if random.random() > 0.55:
        alerts.new_Append("Possible cyanobacteria bloom risk in Eco Park pond")
    selected = next((d for d in districts if d["name"] == selected_name), districts[0])
    return districts, selected, alerts


def recent_complaints():
    with db() as conn:
        rows = conn.execute("SELECT * FROM complaints ORDER BY id DESC LIMIT 8").fetchall()
    return [{**dict(row), "type_label": COMPLAINT_TYPES.get(row["complaint_type"], row["complaint_type"])} for row in
            rows]


def recent_water_quality():
    with db() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM water_quality ORDER BY id DESC LIMIT 6").fetchall()]


@new_App.route("/")
def home():
    zoom = int(request.args.get("zoom", 100))
    zoom = max(70, min(160, zoom))
    selected_district = request.args.get("district")
    status = city_status()
    districts, selected, alerts = map_status(selected_district)
    waste = waste_status()
    current_item, correct_bin = random.choice(WASTE_ITEMS)
    carbon_monoatomic = None
    message = request.args.get("message", "")
    water_result = None
    return render_template(
        "index.html",
        complaint_types=COMPLAINT_TYPES,
        status=status,
        districts=districts,
        selected=selected,
        alerts=alerts,
        waste=waste,
        complaints=recent_complaints(),
        water_history=recent_water_quality(),
        water_result=water_result,
        current_item=current_item,
        correct_bin=correct_bin,
        carbon=carbon_monoatomic,
        zoom=zoom,
        message=message,
    )


@new_App.post("/complaint")
def complaint():
    complaint_type = request.form.get("complaint_type", "")
    location = request.form.get("location", "").strip()
    details = request.form.get("details", "").strip()
    if complaint_type in COMPLAINT_TYPES and location and details:
        with db() as conn:
            conn.execute("INSERT INTO complaints (complaint_type, location, details, created_at) VALUES (?, ?, ?, ?)",
                         (complaint_type, location, details, datetime.now().strftime("%d %b %Y, %I:%M %p")))
            conn.commit()
        return redirect(url_for("home", message="Report saved to SQLite"))
    return redirect(url_for("home", message="Please complete the complaint form"))


@new_App.post("/water-quality")
def water_quality():
    location = request.form.get("location", "Eco Park pond")
    ph = float(request.form.get("ph", 7.0))
    oxygen = float(request.form.get("oxygen", 6.5))
    turbidity = float(request.form.get("turbidity", 35))
    result = analyze_water_quality(ph, oxygen, turbidity)
    with db() as conn:
        conn.execute(
            "INSERT INTO water_quality (location, ph, oxygen, turbidity, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (location, ph, oxygen, turbidity, result["status"], datetime.now().strftime("%d %b %Y, %I:%M %p")))
        conn.commit()
    return render_template("water_result.html", result=result, location=location, ph=ph, oxygen=oxygen,
                           turbidity=turbidity, history=recent_water_quality())


@new_App.post("/sort-waste")
def sort_waste():
    item = request.form.get("item", "Waste item")
    correct = request.form.get("correct", "Recycle")
    choice = request.form.get("choice", "Recycle")
    if choice == correct:
        message = f"Correct. {item} belongs in {correct}."
    else:
        message = f"Almost. {item} should go to {correct}."
    return redirect(url_for("home", message=message))


@new_App.post("/carbon")
def carbon():
    travel = float(request.form.get("travel", 12))
    power = float(request.form.get("power", 8))
    meals = float(request.form.get("meals", 3))
    total = round(travel * 0.18 + power * 0.52 + meals * 0.9, 1)
    return redirect(url_for("home", message=f"Estimated daily footprint: {total} kg CO2e"))


@new_App.post("/sos")
def sos():
    return redirect(
        url_for("home", message="Demo SOS sent: nearby police station and city control room have been alerted"))


init_db()

if __name__ == "__main__":
    new_App.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8010)), debug=True)
