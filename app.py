from flask import Flask, request, jsonify, render_template
from PIL import Image
from io import BytesIO
import requests
import os
import datetime
import time
import logging
from functools import wraps
from rustfs_test import upload_reported_image  # Upload helper for AWS S3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure the environment variables are loaded correctly
PREDICTION_API_URL = os.getenv("PREDICTION_API_URL")
if not PREDICTION_API_URL:
    raise EnvironmentError("Missing PREDICTION_API_URL. Please check your .env file.")

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

@app.route('/predict-url', methods=['POST'])
@measure_time("PREDICT_URL")
def predict_url():
    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

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
        image.thumbnail((1024, 1024))  # Resize image before saving
        image.save(buffer, format="JPEG")
        buffer.seek(0)  # Ensure the buffer is at the start
        upload_reported_image(buffer, filename, 'allimages')  # Always store in allimages

        # Store the image in the appropriate S3 bucket based on prediction
        if external_prediction['prediction'] == 'NSFW':
            upload_reported_image(buffer, filename, 'nsfwreported')
        elif external_prediction['prediction'] == 'SFW':
            upload_reported_image(buffer, filename, 'sfwreported')

        return jsonify({"message": "nsfw-detection.todos.monster says: Image reported successfully!"})

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch image from URL: {str(e)}")
        return jsonify({"error": f"Failed to fetch image from URL: {str(e)}"}), 400
    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500


@app.route('/report-prediction', methods=['POST'])
def report_prediction():
    data = request.form

    prediction = data.get('prediction')
    source_type = data.get('source_type')
    confidence = data.get('confidence')
    sfw_confidence = data.get('sfw_confidence')
    nsfw_confidence = data.get('nsfw_confidence')
    image_url = data.get('image_url')

    logging.info(f"Reported Prediction - Prediction: {prediction}, Source: {source_type}, Image URL: {image_url}")

    return jsonify({"message": "Prediction reported successfully!"}), 200


def get_prediction_from_external_api(image_url):
    try:
        response = requests.post(PREDICTION_API_URL, json={"image_url": image_url})
        response.raise_for_status()  
        result = response.json()
        return {
            "prediction": result.get("prediction"),
            "sfw_confidence": result.get("sfw_confidence"),
            "nsfw_confidence": result.get("nsfw_confidence"),
        }
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        raise
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}")
        raise
    except ValueError as json_err:
        logging.error(f"Error decoding JSON response: {json_err}")
        raise


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
