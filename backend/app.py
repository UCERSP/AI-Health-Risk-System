
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import joblib
from database import get_connection, init_database


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend")
)
MODEL_PATH = os.path.join(BASE_DIR, "health_model.pkl")


# =========================================================
# FLASK APP
# =========================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(app)


# =========================================================
# LOAD ML MODEL
# =========================================================

model = joblib.load(MODEL_PATH)
print("ML model loaded successfully!")


# =========================================================
# DATABASE
# =========================================================

init_database()
print("PostgreSQL database initialized successfully!")


# =========================================================
# BMI CATEGORY
# =========================================================

def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    return "Obesity range"


# =========================================================
# BLOOD PRESSURE CATEGORY
# =========================================================

def get_bp_category(systolic, diastolic):
    if systolic < 120 and diastolic < 80:
        return "Normal"
    elif systolic < 130 and diastolic < 80:
        return "Elevated"
    elif systolic < 140 or diastolic < 90:
        return "High BP - Stage 1 range"
    elif systolic < 180 or diastolic < 120:
        return "High BP - Stage 2 range"
    return "Very high reading"


# =========================================================
# GLUCOSE CATEGORY
# =========================================================

def get_glucose_category(glucose):
    if glucose < 70:
        return "Low glucose reading"
    elif glucose <= 99:
        return "Within typical fasting range"
    elif glucose <= 125:
        return "Elevated fasting-range reading"
    return "High glucose reading"


# =========================================================
# RISK NAME
# =========================================================

def get_risk_name(prediction):
    risk_names = {
        0: "Low Risk",
        1: "Moderate Risk",
        2: "High Risk"
    }
    return risk_names.get(int(prediction), "Unknown Risk")


# =========================================================
# PRECAUTIONS
# =========================================================

def get_precautions(
    risk,
    bmi_category,
    bp_category,
    glucose_category
):
    precautions = []

    if bmi_category == "Underweight":
        precautions.append(
            "Maintain a balanced and nutritious diet and consider "
            "discussing healthy weight goals with a healthcare professional."
        )

    elif bmi_category in ["Overweight", "Obesity range"]:
        precautions.append(
            "Focus on balanced nutrition, regular physical activity, "
            "and healthy weight management."
        )

    if bp_category != "Normal":
        precautions.append(
            "Monitor blood pressure regularly and discuss repeated "
            "elevated readings with a healthcare professional."
        )

    if glucose_category in [
        "Low glucose reading",
        "Elevated fasting-range reading",
        "High glucose reading"
    ]:
        precautions.append(
            "Consider reviewing the glucose reading in the appropriate "
            "context with a healthcare professional."
        )

    if risk == "High Risk":
        precautions.append(
            "The demo risk classification is high. Consider consulting "
            "a qualified healthcare professional for proper evaluation."
        )

    elif risk == "Moderate Risk":
        precautions.append(
            "Monitor the relevant health parameters and discuss "
            "persistent concerns with a healthcare professional."
        )

    if not precautions:
        precautions.append(
            "Continue healthy lifestyle habits and routine health monitoring."
        )

    return precautions


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


# =========================================================
# HEALTH ASSESSMENT
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}

    try:
        name = str(data.get("name", "")).strip()
        age = int(data.get("age", 0))
        height = float(data.get("height", 0))
        weight = float(data.get("weight", 0))
        systolic = int(data.get("systolic", 0))
        diastolic = int(data.get("diastolic", 0))
        glucose = float(data.get("glucose", 0))

        # Validation
        if not name:
            return jsonify({"error": "Please enter your name."}), 400

        if not 1 <= age <= 120:
            return jsonify({"error": "Enter a valid age."}), 400

        if height <= 0 or weight <= 0:
            return jsonify({
                "error": "Height and weight must be positive."
            }), 400

        if glucose <= 0:
            return jsonify({
                "error": "Glucose must be positive."
            }), 400

        if systolic <= 0 or diastolic <= 0:
            return jsonify({
                "error": "Enter valid blood pressure values."
            }), 400

        # BMI
        bmi = round(weight / ((height / 100) ** 2), 2)

        # Individual categories
        bmi_category = get_bmi_category(bmi)
        bp_category = get_bp_category(systolic, diastolic)
        glucose_category = get_glucose_category(glucose)

        # ML prediction
        prediction = model.predict([[
            age,
            bmi,
            systolic,
            diastolic,
            glucose
        ]])[0]

        risk = get_risk_name(prediction)

        # Precautions
        precautions = get_precautions(
            risk,
            bmi_category,
            bp_category,
            glucose_category
        )

        # Explanation
        explanation = (
            f"BMI is in the {bmi_category.lower()} category. "
            f"Blood pressure reading is classified as '{bp_category}'. "
            f"Glucose reading is classified as '{glucose_category}'. "
            f"The demo ML model gives an overall '{risk}' classification "
            f"based on the provided parameters."
        )

        # Save assessment in PostgreSQL.
        # user_id remains NULL until login is implemented.
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO assessments
                    (
                        name,
                        age,
                        bmi,
                        systolic,
                        diastolic,
                        glucose
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    name,
                    age,
                    bmi,
                    systolic,
                    diastolic,
                    glucose
                ))

        # Response
        return jsonify({
            "message": "Assessment saved successfully.",
            "name": name,
            "age": age,
            "bmi": bmi,
            "bmi_category": bmi_category,
            "blood_pressure": f"{systolic}/{diastolic}",
            "bp_category": bp_category,
            "glucose": glucose,
            "glucose_category": glucose_category,
            "prediction": int(prediction),
            "risk": risk,
            "explanation": explanation,
            "precautions": precautions,
            "note": (
                "This is an educational prototype and not a medical diagnosis."
            )
        })

    except (ValueError, TypeError):
        return jsonify({
            "error": "Please enter valid numeric values."
        }), 400


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    app.run(debug=True, port=5000)
