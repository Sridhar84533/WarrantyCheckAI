import os
from dotenv import load_dotenv

load_dotenv()


FOUNDRY_PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
FOUNDRY_AGENT_NAME = os.getenv("FOUNDRY_AGENT_NAME", "WarrantyCheckAI")
FOUNDRY_AGENT_VERSION = os.getenv("FOUNDRY_AGENT_VERSION", "1")

FLASK_SECRET_KEY = os.getenv(
    "FLASK_SECRET_KEY",
    "development-secret-key"
)

MAX_UPLOAD_SIZE = int(
    os.getenv("MAX_UPLOAD_SIZE", "10485760")
)

UPLOAD_FOLDER = os.getenv(
    "UPLOAD_FOLDER",
    "uploads"
)


class Config:
    SECRET_KEY = FLASK_SECRET_KEY
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE
    UPLOAD_FOLDER = UPLOAD_FOLDER