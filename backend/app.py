
import os
import re
import hmac
import secrets
import joblib

from datetime import timedelta
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection, init_database


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
MODEL_PATH = os.path.join(BASE_DIR, "health_model.pkl")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)
CORS(app)

model = joblib.load(MODEL_PATH)
print("ML model loaded successfully!")

init_database()
print("Database initialized successfully!")


def get_bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    return "Obesity range"


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


def get_glucose_category(glucose):
    if glucose < 70:
        return "Low glucose reading"
    elif glucose <= 99:
        return "Within typical fasting range"
    elif glucose <= 125:
        return "Elevated fasting-range reading"
    return "High glucose reading"


def get_risk_name(prediction):
    return {
        0: "Low Risk",
        1: "Moderate Risk",
        2: "High Risk"
    }.get(int(prediction), "Unknown Risk")


def get_precautions(risk, bmi_category, bp_category, glucose_category):
    precautions = []

    if bmi_category == "Underweight":
        precautions.append(
            "Maintain a balanced and nutritious diet and consider discussing "
            "healthy weight goals with a healthcare professional."
        )
    elif bmi_category in ["Overweight", "Obesity range"]:
        precautions.append(
            "Focus on balanced nutrition, regular physical activity, "
            "and healthy weight management."
        )

    if bp_category != "Normal":
        precautions.append(
            "Monitor blood pressure regularly and discuss repeated elevated "
            "readings with a healthcare professional."
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
            "Monitor the relevant health parameters and discuss persistent "
            "concerns with a healthcare professional."
        )

    if not precautions:
        precautions.append(
            "Continue healthy lifestyle habits and routine health monitoring."
        )

    return precautions


def row_value(row, key, index):
    """Read a database result from PostgreSQL or SQLite."""
    if isinstance(row, dict):
        return row[key]
    return row[index]


def current_user_id():
    return session.get("user_id")


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name or len(name) > 100:
        return jsonify({"error": "Enter a name (up to 100 characters)."}), 400

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
        return jsonify({"error": "Enter a valid email address."}), 400

    if len(password) < 8 or len(password) > 128:
        return jsonify({"error": "Password must be 8–128 characters long."}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (email,)
                )
                if cursor.fetchone():
                    return jsonify({
                        "error": "An account with this email already exists."
                    }), 409

                cursor.execute("""
                    INSERT INTO users (name, email, password_hash)
                    VALUES (%s, %s, %s)
                """, (name, email, password_hash))

                cursor.execute(
                    "SELECT id, name, email FROM users WHERE email = %s",
                    (email,)
                )
                user = cursor.fetchone()

        user_id = row_value(user, "id", 0)
        session.clear()
        session.permanent = True
        session["user_id"] = user_id
        session["user_name"] = row_value(user, "name", 1)
        session["user_email"] = row_value(user, "email", 2)

        return jsonify({
            "message": "Account created successfully.",
            "user": {
                "id": user_id,
                "name": session["user_name"],
                "email": session["user_email"]
            }
        }), 201

    except Exception:
        app.logger.exception("Signup failed")
        return jsonify({"error": "Signup could not be completed. Please try again."}), 500


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not email or not password:
        return jsonify({"error": "Enter your email and password."}), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, email, password_hash
                    FROM users
                    WHERE email = %s
                """, (email,))
                user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid email or password."}), 401

        user_id = row_value(user, "id", 0)
        name = row_value(user, "name", 1)
        saved_email = row_value(user, "email", 2)
        password_hash = row_value(user, "password_hash", 3)

        if not check_password_hash(password_hash, password):
            return jsonify({"error": "Invalid email or password."}), 401

        session.clear()
        session.permanent = True
        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = saved_email

        return jsonify({
            "message": "Login successful.",
            "user": {
                "id": user_id,
                "name": name,
                "email": saved_email
            }
        })

    except Exception:
        app.logger.exception("Login failed")
        return jsonify({"error": "Login could not be completed. Please try again."}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    response = jsonify({"message": "Logged out successfully."})
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/api/me", methods=["GET"])
def me():
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"logged_in": False}), 200

    return jsonify({
        "logged_in": True,
        "user": {
            "id": user_id,
            "name": session.get("user_name", ""),
            "email": session.get("user_email", "")
        }
    })


@app.route("/api/history", methods=["GET"])
def history():
    user_id = current_user_id()
    if user_id is None:
        return jsonify({"error": "Please log in to view your history."}), 401

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, age, bmi, systolic, diastolic,
                           glucose, created_at
                    FROM assessments
                    WHERE user_id = %s
                    ORDER BY created_at DESC, id DESC
                """, (user_id,))
                rows = cursor.fetchall()

        records = []
        for row in rows:
            created_at = row_value(row, "created_at", 7)
            records.append({
                "id": row_value(row, "id", 0),
                "name": row_value(row, "name", 1),
                "age": row_value(row, "age", 2),
                "bmi": row_value(row, "bmi", 3),
                "systolic": row_value(row, "systolic", 4),
                "diastolic": row_value(row, "diastolic", 5),
                "glucose": row_value(row, "glucose", 6),
                "created_at": str(created_at) if created_at else None
            })

        return jsonify({"records": records})

    except Exception:
        app.logger.exception("History retrieval failed")
        return jsonify({"error": "History could not be loaded."}), 500


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

        if not name:
            return jsonify({"error": "Please enter your name."}), 400
        if not 1 <= age <= 120:
            return jsonify({"error": "Enter a valid age."}), 400
        if height <= 0 or weight <= 0:
            return jsonify({"error": "Height and weight must be positive."}), 400
        if glucose <= 0:
            return jsonify({"error": "Glucose must be positive."}), 400
        if systolic <= 0 or diastolic <= 0:
            return jsonify({"error": "Enter valid blood pressure values."}), 400

        bmi = round(weight / ((height / 100) ** 2), 2)
        bmi_category = get_bmi_category(bmi)
        bp_category = get_bp_category(systolic, diastolic)
        glucose_category = get_glucose_category(glucose)

        prediction = model.predict([[
            age, bmi, systolic, diastolic, glucose
        ]])[0]
        risk = get_risk_name(prediction)

        precautions = get_precautions(
            risk, bmi_category, bp_category, glucose_category
        )

        explanation = (
            f"BMI is in the {bmi_category.lower()} category. "
            f"Blood pressure reading is classified as '{bp_category}'. "
            f"Glucose reading is classified as '{glucose_category}'. "
            f"The demo ML model gives an overall '{risk}' classification "
            f"based on the provided parameters."
        )

        # Only save a personal record when the user is logged in.
        user_id = current_user_id()
        if user_id is not None:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO assessments
                        (user_id, name, age, bmi, systolic, diastolic,
                         glucose, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    """, (
                        user_id, name, age, bmi, systolic,
                        diastolic, glucose
                    ))

        return jsonify({
            "message": (
                "Assessment saved to your history."
                if user_id is not None
                else "Demo assessment complete. Log in to save personal history."
            ),
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
            ),
            "saved_to_history": user_id is not None
        })

    except (ValueError, TypeError):
        return jsonify({"error": "Please enter valid numeric values."}), 400
    except Exception:
        app.logger.exception("Assessment failed")
        return jsonify({"error": "Assessment could not be completed."}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
