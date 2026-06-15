from datetime import datetime
from app.db.mongo import db
from app.services.file_service import load_signal_from_file
from app.ml.predictor import predict_signal


def save_ecg_result(patient_id, file_url, result):
    record = {
        "patient_id": patient_id,
        "file_url": file_url,
        "prediction": result["final_prediction"],
        "detailed_beats": result.get("detailed_beats", []),  # Aici am facut modificarea
        "percentages": result.get("percentages", {}),
        "created_at": datetime.utcnow()
    }

    db.ecg_results.insert_one(record)
    return record


def analyze_ecg(patient_id: str, file_url: str):
    signal = load_signal_from_file(file_url)

    if len(signal) == 0:
        return {"error": "Invalid ECG signal: empty file"}

    result = predict_signal(signal)
    save_ecg_result(patient_id, file_url, result)

    return result