from flask import Flask, render_template, request, send_file, redirect, session
import tensorflow as tf
import numpy as np
from PIL import Image
import sqlite3
import os

from recommendations import recommendations
from pdf_generator import generate_report
import google.generativeai as genai
from gemini_config import API_KEY

app = Flask(__name__)

app.secret_key = "crop_disease_secret_key"

genai.configure(api_key=API_KEY)

gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

# Store latest prediction for PDF generation
last_prediction = {}

# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load trained model
model = tf.keras.models.load_model(
    "models/crop_disease_model.h5"
)

# Class names
CLASSES = [
    'Potato___Early_blight',
    'Potato___Late_blight',
    'Potato___healthy',
    'Tomato_Early_blight',
    'Tomato_Late_blight',
    'Tomato_healthy'
]


# =========================
# REGISTER
# =========================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("crop_disease.db")
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()

            return redirect('/login')

        except:

            return "Username already exists!"

        finally:

            conn.close()

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("crop_disease.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session['username'] = username

            return redirect('/')

        return "Invalid Username or Password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/login')


# =========================
# HOME
# =========================
@app.route('/')
def home():

    if 'username' not in session:
        return redirect('/login')

    return render_template(
        "index.html",
        username=session['username']
    )


# =========================
# PREDICT
# =========================
@app.route('/predict', methods=['POST'])
def predict():

    if 'username' not in session:
        return redirect('/login')

    global last_prediction

    file = request.files['image']

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    img = Image.open(filepath).convert("RGB")

    img = img.resize((224, 224))

    img = np.array(img) / 255.0

    img = np.expand_dims(img, axis=0)

    prediction = model.predict(img)

    predicted_class = CLASSES[np.argmax(prediction)]

    confidence = float(np.max(prediction)) * 100

    info = recommendations[predicted_class]

    last_prediction = {
        "disease": predicted_class,
        "confidence": round(confidence, 2),
        "fertilizer": info["fertilizer"],
        "treatment": info["treatment"]
    }

    conn = sqlite3.connect("crop_disease.db")

    cursor = conn.cursor()

    cursor.execute("""
INSERT INTO predictions
(disease, confidence, fertilizer, treatment, username)
VALUES (?, ?, ?, ?, ?)
""", (
    predicted_class,
    confidence,
    info["fertilizer"],
    info["treatment"],
    session['username']
))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        disease=predicted_class,
        confidence=round(confidence, 2),
        fertilizer=info["fertilizer"],
        treatment=info["treatment"],
        image_path=filepath
    )


# =========================
# PDF REPORT
# =========================
@app.route('/download-report')
def download_report():

    if 'username' not in session:
        return redirect('/login')

    filename = "crop_report.pdf"

    generate_report(
        filename,
        last_prediction["disease"],
        last_prediction["confidence"],
        last_prediction["fertilizer"],
        last_prediction["treatment"]
    )

    return send_file(
        filename,
        as_attachment=True
    )


# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("crop_disease.db")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM predictions
    WHERE username = ?
    """, (session['username'],))

    total_predictions = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COUNT(*)
    FROM predictions
    WHERE username = ?
    AND disease LIKE '%healthy%'
    """, (session['username'],))

    healthy_count = cursor.fetchone()[0]

    diseased_count = total_predictions - healthy_count

    cursor.execute("""
    SELECT disease,
           ROUND(confidence, 2),
           prediction_date
    FROM predictions
    WHERE username = ?
    ORDER BY id DESC
    LIMIT 10
    """, (session['username'],))

    recent_predictions = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_predictions=total_predictions,
        healthy_count=healthy_count,
        diseased_count=diseased_count,
        recent_predictions=recent_predictions
    )


# =========================
# HISTORY
# =========================
@app.route('/history')
def history():

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("crop_disease.db")

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id,
           disease,
           ROUND(confidence, 2),
           fertilizer,
           treatment,
           prediction_date
    FROM predictions
    WHERE username = ?
    ORDER BY id DESC
    """, (session['username'],))

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )

# =========================
# AI FARMING ASSISTANT
# =========================
@app.route('/assistant', methods=['GET', 'POST'])
def assistant():

    if 'username' not in session:
        return redirect('/login')

    response = ""

    if request.method == 'POST':

        question = request.form['question']

        prompt = f"""
You are an expert agriculture assistant.

Help farmers with:

- Crop diseases
- Fertilizers
- Pesticides
- Irrigation
- Soil health
- Organic farming
- Yield improvement

Farmer Question:

{question}

Give practical and simple advice.
"""

        try:

            result = gemini_model.generate_content(prompt)

            response = result.text

        except Exception as e:

            response = f"Error: {str(e)}"

    return render_template(
        "assistant.html",
        response=response
    )

if __name__ == "__main__":
    app.run(debug=True)