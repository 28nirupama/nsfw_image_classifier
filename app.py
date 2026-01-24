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
        response = requests.get(image_url, timeout=10)
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
        upload_reported_image(buffer, filename, 'allimages')

        # Upload to the respective reported bucket based on the prediction
        if external_prediction['prediction'] == 'NSFW':
            upload_reported_image(buffer, filename, 'nsfwreported')
        elif external_prediction['prediction'] == 'SFW':
            upload_reported_image(buffer, filename, 'sfwreported')
        else:
            upload_reported_image(buffer, filename, 'safereported')

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

        # Return success message for frontend (for localhost)
        return jsonify({"message": "localhost:5000 says: Image reported successfully!"})

    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {str(e)}"}), 500


# -----------------------
# Report Incorrect Prediction
# -----------------------
def get_prediction_from_external_api(image_url):
    prediction_api_url = "https://nsfw-detection.todos.monster/predict"
    response = requests.post(prediction_api_url, json={"image_url": image_url})

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
    app.run(host="0.0.0.0", port=5000, debug=True)
