import os

# Load .env file if python-dotenv is available (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()  # automatically loads .env from project root
except ImportError:
    pass  # python-dotenv not installed, rely on system environment variables

class Config:
    """Unified configuration for local development and Docker/production."""

    # ----------------------------
    # Environment settings
    # ----------------------------
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')  # 'development' or 'production'
    DEBUG = FLASK_ENV == 'development'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

    # ----------------------------
    # AWS S3 Configuration
    AWS_ENDPOINT_URL = os.getenv('AWS_ENDPOINT_URL') or os.getenv('STORAGE_ENDPOINT_URL', 'https://storage.todos.monster')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    # ----------------------------
    # S3 Bucket Names
    # ----------------------------
    S3_BUCKET_ALL_IMAGES = os.getenv('S3_BUCKET_ALL_IMAGES', 'allimages')
    S3_BUCKET_NSFW_REPORTED = os.getenv('S3_BUCKET_NSFW_REPORTED', 'nsfwreported')
    S3_BUCKET_SFW_REPORTED = os.getenv('S3_BUCKET_SFW_REPORTED', 'sfwreported')
    S3_BUCKET_NOTSAFE_REPORTED = os.getenv('S3_BUCKET_NOTSAFE_REPORTED', 'notsafereported')
    S3_BUCKET_SAFE_REPORTED = os.getenv('S3_BUCKET_SAFE_REPORTED', 'safereported')

    # ----------------------------
    # Model & Prediction settings
    # ----------------------------
    MODEL_PATH = os.getenv('MODEL_PATH', 'resnet50_nsfw_finetuned.pt')
    NSFW_THRESHOLD = float(os.getenv('NSFW_THRESHOLD', 0.8))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 10))

    # ----------------------------
    # Feature flags
    # ----------------------------
    # Controls whether images should be uploaded to S3 or skipped
    S3_UPLOAD_ENABLED = os.getenv('S3_UPLOAD_ENABLED', 'True').lower() in ('true', '1', 'yes')

    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        missing = []
        if not cls.AWS_ACCESS_KEY_ID:
            missing.append('AWS_ACCESS_KEY_ID')
        if not cls.AWS_SECRET_ACCESS_KEY:
            missing.append('AWS_SECRET_ACCESS_KEY')

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        print(f"S3_UPLOAD_ENABLED: {cls.S3_UPLOAD_ENABLED}")  
        

    @classmethod
    def is_development(cls):
        return cls.FLASK_ENV == 'development'

    @classmethod
    def is_production(cls):
        return cls.FLASK_ENV == 'production'


# ----------------------------
# Singleton instance for easy access
# ----------------------------
config = Config()