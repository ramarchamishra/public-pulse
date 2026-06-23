import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    X_USERNAME = os.getenv("X_USERNAME")
    X_EMAIL = os.getenv("X_EMAIL")
    X_PASSWORD = os.getenv("X_PASSWORD")