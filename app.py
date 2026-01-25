from flask import Flask, request, jsonify, render_template
from model import predict_pil_image  # Assuming this is your local model
from PIL import Image
from io import BytesIO
import os
import requests
import datetime
import time
import logging
from functools import wraps
from config import config  # Import the centralized configuration class
from rustfs_test import upload_reported_image  # Upload helper for AWS S3

app = Flask(__name__)

# Configure Flask based on environment
app.config['DEBUG'] = config.DEBUG  # Enable debug based on FLASK_ENV

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

# Function to get prediction from external API
def get_prediction_from_api(image_data):
    api_url = config.PREDICTION_API_URL
    response = requests.post(api_url, data=image_data, timeout=config.REQUEST_TIMEOUT)
    return response.json()

@app.route('/predict-url', methods=['POST'])
@measure_time("PREDICT_URL")
def predict_url():
    data = request.get_json()
    image_url = data.get("image_url")

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    try:
        # Fetch image from URL
        response = requests.get(image_url, timeout=config.REQUEST_TIMEOUT)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # Get prediction using the external prediction API
        prediction_result = get_prediction_from_api(image)

        # Define filename
        filename = f"{prediction_result['prediction']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Upload the image to the `allimages` bucket if S3_UPLOAD_ENABLED is True
        if config.S3_UPLOAD_ENABLED:
            buffer = BytesIO()
            image.thumbnail((1024, 1024))  # Resize image before saving
            image.save(buffer, format="JPEG")  # Save image to buffer
            buffer.seek(0)  # Correctly use seek on the buffer (not the image)
            upload_reported_image(buffer, filename, config.S3_BUCKET_ALL_IMAGES)  # Always store in allimages

            # Store the image in the appropriate S3 bucket based on prediction
            if prediction_result['prediction'] == 'NSFW':
                upload_reported_image(buffer, filename, config.S3_BUCKET_NSFW_REPORTED)
            elif prediction_result['prediction'] == 'SFW':
                upload_reported_image(buffer, filename, config.S3_BUCKET_SFW_REPORTED)

        return jsonify({
            "prediction": prediction_result['prediction'],
            "confidence": prediction_result['confidence'],
            "sfw_confidence": prediction_result['sfw_confidence'],
            "nsfw_confidence": prediction_result['nsfw_confidence'],
            "message": "Image classified successfully!"
        })

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch image from URL: {str(e)}")
        return jsonify({"error": f"Failed to fetch image from URL: {str(e)}"}), 400
    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500

@app.route('/predict-upload', methods=['POST'])
@measure_time("PREDICT_UPLOAD")
def predict_upload():
    file = request.files.get('file')  # Get the file from the request

    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        # Process the uploaded image file
        image = Image.open(file).convert("RGB")
        prediction_result = get_prediction_from_api(image)

        # Define filename
        filename = f"{prediction_result['prediction']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"

        # Upload the image to the `allimages` bucket if S3_UPLOAD_ENABLED is True
        if config.S3_UPLOAD_ENABLED:
            buffer = BytesIO()
            image.thumbnail((1024, 1024))  # Resize image before saving
            image.save(buffer, format="JPEG")  # Save image to buffer
            buffer.seek(0)  # Ensure the buffer is at the start before uploading
            upload_reported_image(buffer, filename, config.S3_BUCKET_ALL_IMAGES)  # Always store in allimages

            # Store the image in the appropriate S3 bucket based on prediction
            if prediction_result['prediction'] == 'NSFW':
                upload_reported_image(buffer, filename, config.S3_BUCKET_NSFW_REPORTED)
            elif prediction_result['prediction'] == 'SFW':
                upload_reported_image(buffer, filename, config.S3_BUCKET_SFW_REPORTED)

        return jsonify({
            "prediction": prediction_result['prediction'],
            "confidence": prediction_result['confidence'],
            "sfw_confidence": prediction_result['sfw_confidence'],
            "nsfw_confidence": prediction_result['nsfw_confidence'],
            "message": "Image uploaded and classified successfully!"
        })

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


if __name__ == "__main__":
    print(f"Starting server in {config.FLASK_ENV} mode...")
    print(f"Debug mode: {config.DEBUG}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
