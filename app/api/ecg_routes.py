from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import numpy as np

from app.db.mongo import ecg_collection
from app.services.file_service import download_from_url
from app.services.mqtt_service import send_device_command
from app.services.ecg_ai_service import analyze_ecg

router = APIRouter(tags=["ECG Management"])

class DeviceCommand(BaseModel):
    device_id: str
    command: str
    patient_id: str
    first_name: str
    last_name: str

@router.post("/send-command")
def send_command_to_pi(req: DeviceCommand):
    if req.command not in ["start", "stop"]:
        raise HTTPException(status_code=400, detail="Command must be 'start' or 'stop'")

    try:
        send_device_command(
            device_id=req.device_id,
            command=req.command,
            patient_id=req.patient_id,
            first_name=req.first_name,
            last_name=req.last_name
        )
        return {"message": f"Command '{req.command}' sent successfully to {req.device_id}."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.get("/latest/raw/{patient_id}")
def get_latest_ecg_raw(patient_id: str):
    record = ecg_collection.find_one(
        {"patient_id": patient_id},
        sort=[("timestamp", -1)]
    )

    if not record or "file_url" not in record:
        raise HTTPException(status_code=404, detail="ECG not found")

    local_path = "data/temp_ecg.npy"
    download_from_url(record["file_url"], local_path)
    signal = np.load(local_path)

    return {
        "patient_id": record["patient_id"],
        "timestamp": record["timestamp"],
        "sample_rate": record.get("sample_rate", 250),
        "values": signal.tolist(),
        "file_url": record["file_url"],
        "bpm": record.get("bpm", 0)
    }

@router.get("/raw-by-url")
def get_ecg_raw_by_url(file_url: str = Query(...)):
    record = ecg_collection.find_one({"file_url": file_url})

    if not record:
        raise HTTPException(status_code=404, detail="ECG record not found")

    local_path = "data/temp_attached_ecg.npy"
    download_from_url(file_url, local_path)
    signal = np.load(local_path)

    return {
        "patient_id": record.get("patient_id", ""),
        "timestamp": record.get("timestamp", ""),
        "sample_rate": record.get("sample_rate", 250),
        "values": signal.tolist(),
        "file_url": record.get("file_url", ""),
        "bpm": record.get("bpm", 0)
    }

@router.get("/analyze")
def analyze_ecg_endpoint(
    patient_id: str = Query(...),
    file_url: str = Query(...)
):
    result = analyze_ecg(patient_id, file_url)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "status": "success",
        "data": result
    }