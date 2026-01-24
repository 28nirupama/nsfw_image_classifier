from flask import Flask, request, jsonify, render_template
from model import predict_from_url, predict_pil_image
from PIL import Image
from io import BytesIO
import requests
import os
import datetime
import time
import logging
from functools import wraps
from config import config
from rustfs_test import upload_reported_image  # Upload helper for AWS S3

app = Flask(__name__)

# Configure Flask based on environment
app.config['DEBUG'] = config.DEBUG

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
# Predict from URL (External API)
# -----------------------
@app.route('/predict-url', methods=['POST'])
@measure_time("PREDICT_URL")
def predict_url():
    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "No image URL provided"})

    try:
        # Fetch image from URL
        response = requests.get(image_url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # Get prediction from external API
        external_prediction = get_prediction_from_external_api(image_url)

        # Define filename
        filename = f"{external_prediction['prediction']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Upload the image to the `allimages` bucket
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        upload_reported_image(buffer, filename, 'allimages')  # Always store in allimages

        # Store the image in the appropriate S3 bucket based on prediction
        if external_prediction['prediction'] == 'NSFW':
            upload_reported_image(buffer, filename, 'nsfwreported')
        elif external_prediction['prediction'] == 'SFW':
            upload_reported_image(buffer, filename, 'sfwreported')

        # Return success message for frontend (for external API)
        return jsonify({"message": "nsfw-detection.todos.monster says: Image reported successfully!"})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch image from URL: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500


# -----------------------
# Predict from Upload (Local)
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
    buffer.seek(0)  # Ensure buffer is at the start

    try:
        # Generate filename with timestamp
        filename = f"{result['prediction']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Upload to allimages bucket
        upload_reported_image(buffer, filename, 'allimages')

        # Upload to the appropriate bucket based on prediction
        if result["prediction"] == "NSFW":
            upload_reported_image(buffer, filename, 'nsfwreported')
        else:
            upload_reported_image(buffer, filename, 'sfwreported')

        # Return success message for frontend
        return jsonify({"message": "localhost:5000 says: Image reported successfully!"})

    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500


# -----------------------
# Report Incorrect Prediction
# -----------------------
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
            response = requests.get(image_url, timeout=config.REQUEST_TIMEOUT)
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
        return jsonify({"message": "Image reported and uploaded successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500


def get_prediction_from_external_api(image_url):
    response = requests.post(
        config.PREDICTION_API_URL,
        json={"image_url": image_url},
        timeout=config.REQUEST_TIMEOUT
    )

    if response.status_code == 200:
        result = response.json()
        return {
            "prediction": result.get("prediction"),
            "sfw_confidence": result.get("sfw_confidence"),
            "nsfw_confidence": result.get("nsfw_confidence"),
        }
    else:
        raise Exception(f"Error from external API: {response.status_code}")


if __name__ == "__main__":
    print(f"Starting server in {config.FLASK_ENV} mode...")
    print(f"Debug mode: {config.DEBUG}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
