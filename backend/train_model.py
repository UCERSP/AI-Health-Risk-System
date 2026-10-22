import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


# ============================================================
# AI HEALTH RISK ANALYSIS SYSTEM
# Phase 2 - Demo ML Model
#
# Features:
# [Age, BMI, Systolic BP, Diastolic BP, Glucose]
#
# Labels:
# 0 = Low Risk
# 1 = Moderate Risk
# 2 = High Risk
#
# NOTE:
# This is an educational/demo model.
# It is NOT a medical diagnosis system.
# ============================================================


# ------------------------------------------------------------
# Training data
# [Age, BMI, Systolic BP, Diastolic BP, Glucose]
# ------------------------------------------------------------

X = [
    [18, 19.5, 105, 68, 82],
    [20, 21.2, 110, 70, 85],
    [22, 22.5, 112, 72, 88],
    [25, 23.1, 115, 74, 90],
    [28, 21.8, 118, 76, 92],
    [30, 24.0, 120, 78, 95],
    [32, 22.9, 116, 75, 89],
    [35, 23.8, 119, 77, 94],
    [40, 24.5, 121, 79, 96],
    [45, 25.0, 122, 80, 98],

    [23, 26.5, 128, 82, 102],
    [27, 27.2, 130, 84, 105],
    [31, 26.8, 132, 85, 108],
    [34, 28.1, 134, 86, 110],
    [37, 27.5, 136, 87, 112],
    [42, 28.8, 138, 88, 115],
    [46, 29.2, 140, 90, 118],
    [50, 28.5, 135, 86, 109],
    [54, 29.8, 142, 91, 120],
    [58, 27.9, 137, 89, 116],

    [25, 30.5, 145, 92, 125],
    [29, 31.2, 148, 94, 130],
    [33, 32.0, 150, 95, 135],
    [36, 30.8, 152, 96, 138],
    [39, 33.1, 155, 98, 142],
    [43, 31.8, 148, 94, 136],
    [47, 34.0, 158, 99, 145],
    [51, 32.5, 160, 100, 150],
    [56, 35.2, 162, 101, 155],
    [62, 33.8, 165, 102, 160],

    [19, 20.8, 108, 69, 84],
    [24, 22.1, 114, 73, 87],
    [26, 23.5, 117, 76, 91],
    [29, 25.2, 123, 80, 99],
    [31, 24.8, 126, 81, 101],
    [34, 25.5, 129, 83, 104],
    [38, 26.1, 131, 84, 106],
    [41, 25.7, 133, 85, 107],
    [44, 26.9, 135, 86, 111],
    [48, 27.3, 139, 88, 114],

    [52, 30.1, 144, 91, 123],
    [55, 31.5, 147, 93, 128],
    [59, 30.8, 151, 95, 133],
    [63, 32.2, 154, 97, 140],
    [67, 29.7, 149, 92, 127],
    [70, 31.9, 156, 98, 145],
    [72, 28.9, 143, 90, 122],
    [65, 34.5, 160, 100, 152],
    [57, 33.0, 157, 99, 148],
    [49, 30.9, 146, 92, 126]
]


# ------------------------------------------------------------
# Demo risk labels
#
# 0 = Low Risk
# 1 = Moderate Risk
# 2 = High Risk
# ------------------------------------------------------------

y = [
    0, 0, 0, 0, 0,
    0, 0, 0, 0, 0,

    1, 1, 1, 1, 1,
    1, 1, 1, 1, 1,

    2, 2, 2, 2, 2,
    2, 2, 2, 2, 2,

    0, 0, 0, 1, 1,
    1, 1, 1, 1, 1,

    1, 1, 1, 2, 2,
    2, 2, 2, 2, 2
]


# ------------------------------------------------------------
# Split data into training and testing sets
# ------------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    random_state=42,
    stratify=y
)


# ------------------------------------------------------------
# Create and train Decision Tree model
# ------------------------------------------------------------

model = DecisionTreeClassifier(
    max_depth=4,
    min_samples_leaf=2,
    random_state=42
)

model.fit(X_train, y_train)


# ------------------------------------------------------------
# Evaluate model
# ------------------------------------------------------------

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
matrix = confusion_matrix(y_test, y_pred)


print("\n========================================")
print("AI HEALTH RISK MODEL TRAINING")
print("========================================")

print("\nModel trained successfully!")

print("\nFeatures used:")
print("1. Age")
print("2. BMI")
print("3. Systolic Blood Pressure")
print("4. Diastolic Blood Pressure")
print("5. Glucose")

print("\nRisk classes:")
print("0 = Low Risk")
print("1 = Moderate Risk")
print("2 = High Risk")

print("\nTest Accuracy:")
print(f"{accuracy * 100:.2f}%")

print("\nConfusion Matrix:")
print(matrix)

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        labels=[0, 1, 2],
        target_names=[
            "Low Risk",
            "Moderate Risk",
            "High Risk"
        ],
        zero_division=0
    )
)


# ------------------------------------------------------------
# Test one example
# ------------------------------------------------------------

example = [[28, 22.5, 115, 74, 90]]

example_prediction = model.predict(example)[0]

risk_names = {
    0: "Low Risk",
    1: "Moderate Risk",
    2: "High Risk"
}

print("\nExample Input:")
print("Age = 28")
print("BMI = 22.5")
print("BP = 115/74")
print("Glucose = 90")

print("\nExample Prediction:")
print(risk_names[int(example_prediction)])


# ------------------------------------------------------------
# Save model
# ------------------------------------------------------------

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "health_model.pkl"
)

joblib.dump(model, MODEL_PATH)

print("\n========================================")
print("Model saved successfully!")
print("Location:", MODEL_PATH)
print("========================================")