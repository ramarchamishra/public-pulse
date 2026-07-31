import os
import torch
from dotenv import load_dotenv

load_dotenv()

class Config:
    X_USERNAME = os.getenv("X_USERNAME")
    X_EMAIL = os.getenv("X_EMAIL")
    X_PASSWORD = os.getenv("X_PASSWORD")
    X_AUTHTOKEN = os.getenv("X_AUTHTOKEN")
    X_TWID = os.getenv("X_TWID")
    X_GUEST_ID = os.getenv("X_GUEST_ID")
    X_GUEST_ID_ADS = os.getenv("X_GUEST_ID_ADS")
    X_PERSONALIZATION_ID = os.getenv("X_PERSONALIZATION_ID")
    X_GUEST_ID_MARKETING = os.getenv("X_GUEST_ID_MARKETING")
    X_CT0 = os.getenv("X_CT0")
    EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"