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
from rustfs_test import upload_reported_image

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

    # Determine the bucket based on prediction
    if result["prediction"] == "NSFW":
        bucket = 'nsfwreported'
    else:
        bucket = 'sfwreported'

    # Upload to the respective bucket
    try:
        filename = f"{result['prediction']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        upload_reported_image(buffer, filename, bucket)  # Upload to correct bucket
        # Also upload to 'allimages' bucket for record-keeping
        upload_reported_image(buffer, filename, 'allimages')

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500



# -----------------------
# Report Incorrect Prediction
# -----------------------
# In app.py, inside the /report route
@app.route('/report', methods=['POST'])
@measure_time("REPORT_IMAGE")
def report():
    predicted_label = request.form.get("prediction")
    source_type = request.form.get("source_type")
    report_type = request.form.get("report_type")  # "nsfw", "sfw", or "safe"

    if not predicted_label or not source_type or not report_type:
        return jsonify({"error": "Invalid report data"})

    # Determine the bucket based on report_type
    if report_type == "nsfw":
        bucket = 'nsfwreported'
    elif report_type == "sfw":
        bucket = 'sfwreported'
    elif report_type == "safe":
        bucket = 'safereported'  # New bucket for safe images
    else:
        return jsonify({"error": "Unknown report type"}), 400

    # Get the image based on source_type (URL or upload)
    image = None
    image_bytes = None

    if source_type == "url":
        image_url = request.form.get("image_url")
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()  # Raise an exception for bad HTTP responses
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Failed to fetch image from URL: {str(e)}"}), 400
    elif source_type == "upload":
        image_bytes = app.config.get("LAST_UPLOADED_IMAGE")
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    else:
        return jsonify({"error": "Unknown source type"})

    # Prepare filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{predicted_label}_{timestamp}.jpg"

    # Save image to memory buffer
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    # Upload to cloud (S3-compatible bucket)
    try:
        upload_reported_image(buffer, filename, bucket)  # Upload to correct bucket
        # Also upload to 'allimages' bucket for record-keeping
        upload_reported_image(buffer, filename, 'allimages')

        return jsonify({"message": "Image reported and uploaded successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

