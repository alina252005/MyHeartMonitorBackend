from pymongo import MongoClient
from app.core.config import MONGO_URI, MONGO_DB, MONGO_COLLECTION

client = MongoClient(MONGO_URI)

db = client[MONGO_DB]
ecg_collection = db[MONGO_COLLECTION]
users_collection=db["users"]
ecg_results_collection = db["ecg_results"]
appointments_collection = db["appointments"]