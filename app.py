from flask import Flask, request, jsonify, render_template
from model import predict_from_url, predict_pil_image
from PIL import Image
from io import BytesIO
import requests
import os
import datetime
import time
import logging
import json
from functools import wraps


app = Flask(__name__)

# Folder to store reported images
REPORT_DIR = "reported_images"
os.makedirs(REPORT_DIR, exist_ok=True)

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/access.log"),
        logging.FileHandler("logs/errors.log"),
        logging.StreamHandler()
    ]
)
def measure_time(route_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return f(*args, **kwargs)
            finally:
                duration = (time.time() - start) * 1000
                logging.info(f"{route_name} | {duration:.2f} ms")
        return wrapper
    return decorator


@app.route('/')
def home():
    return render_template("index.html")


# -----------------------
# Predict from URL
# -----------------------
@app.route('/predict', methods=['POST'])
@measure_time("PREDICT_URL")
def predict():
    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "No image URL provided"})

    result = predict_from_url(image_url)
    return jsonify(result)


# -----------------------
# Predict from Upload
# -----------------------
@app.route('/predict-upload', methods=['POST'])
@measure_time("PREDICT_UPLOAD")
def predict_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['file']
    image = Image.open(file).convert("RGB")

    result = predict_pil_image(image)

    # Save image temporarily for reporting
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    app.config["LAST_UPLOADED_IMAGE"] = buffer.getvalue()

    return jsonify(result)


# -----------------------
# Report Incorrect Prediction
# -----------------------
@app.route('/report', methods=['POST'])
@measure_time("REPORT_IMAGE")
def report():

    predicted_label = request.form.get("prediction")
    source_type = request.form.get("source_type")

    if not predicted_label or not source_type:
        return jsonify({"error": "Invalid report data"})

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = os.path.join(REPORT_DIR, f"predicted_{predicted_label.lower()}")
    os.makedirs(save_dir, exist_ok=True)

    if source_type == "url":
        image_url = request.form.get("image_url")
        response = requests.get(image_url, timeout=10)
        image = Image.open(BytesIO(response.content)).convert("RGB")

    elif source_type == "upload":
        image_bytes = app.config.get("LAST_UPLOADED_IMAGE")
        image = Image.open(BytesIO(image_bytes)).convert("RGB")

    else:
        return jsonify({"error": "Unknown source type"})

    filename = f"{predicted_label}_{timestamp}.jpg"
    image.save(os.path.join(save_dir, filename))

    return jsonify({"message": "Image reported successfully"})




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

