import os
from tensorflow.keras.models import load_model
import joblib

BASE_DIR = os.path.dirname(__file__)

model_path = os.path.join(BASE_DIR, "ecg_model.h5")
scaler_path = os.path.join(BASE_DIR, "scaler.pkl")

model = load_model(model_path)
scaler = joblib.load(scaler_path)