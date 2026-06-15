from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from bson import ObjectId

from app.db.mongo import db
from app.models.appointments import AppointmentRequest
from app.services.notification_service import send_notification
from app.services.websocket_manager import manager

router = APIRouter(tags=["Appointments"])


def get_range_dates(range_value: str):
    now = datetime.utcnow()

    if range_value == "this_week":
        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    elif range_value == "last_week":
        start = now - timedelta(days=now.weekday() + 7)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    elif range_value == "this_month":
        start = datetime(now.year, now.month, 1)

        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)

        end = next_month - timedelta(seconds=1)

    elif range_value == "last_month":
        first_this_month = datetime(now.year, now.month, 1)
        last_month_last_day = first_this_month - timedelta(days=1)

        start = datetime(
            last_month_last_day.year,
            last_month_last_day.month,
            1
        )

        end = datetime(
            last_month_last_day.year,
            last_month_last_day.month,
            last_month_last_day.day,
            23,
            59,
            59
        )

    elif range_value == "last_6_months":
        start = now - timedelta(days=180)
        end = now

    elif range_value == "this_year":
        start = datetime(now.year, 1, 1)
        end = datetime(now.year, 12, 31, 23, 59, 59)

    elif range_value == "last_year":
        start = datetime(now.year - 1, 1, 1)
        end = datetime(now.year - 1, 12, 31, 23, 59, 59)

    else:
        return None, None

    return start, end


@router.post("/create")
def create_appointment(data: AppointmentRequest):
    try:
        patient = db.users.find_one({
            "_id": ObjectId(data.patient_id)
        })
    except:
        raise HTTPException(
            status_code=400,
            detail="Invalid patient_id"
        )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    doctor_id = patient.get("doctor_id")

    if not doctor_id:
        raise HTTPException(
            status_code=400,
            detail="No doctor assigned"
        )

    ecg_url = None

    if data.ecg_url == "attach_latest":
        latest_ecg = db.ecg_reader.find_one(
            {
                "patient_id": data.patient_id
            },
            sort=[("timestamp", -1)]
        )

        if latest_ecg:
            ecg_url = latest_ecg.get("file_url")

    appointment = {
        "patient_id": data.patient_id,
        "doctor_id": doctor_id,
        "date": data.date,
        "status": "pending",
        "ecg_url": ecg_url,
        "fcm_token": data.fcm_token,
        "created_at": datetime.utcnow()
    }

    db.appointments.insert_one(appointment)

    return {
        "message": "Appointment request sent"
    }


@router.get("/patient/{patient_id}")
def get_patient_appointments(patient_id: str):
    appointments = db.appointments.find({
        "patient_id": patient_id
    }).sort("date", -1)

    result = []

    for a in appointments:
        result.append({
            "id": str(a["_id"]),
            "date": a.get("date", ""),
            "status": a.get("status", ""),
            "ecg_url": a.get("ecg_url"),
            "has_ecg": a.get("ecg_url") is not None
        })

    return result


@router.get("/doctor/{doctor_id}")
def get_doctor_appointments(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor id"
        )

    appointments = db.appointments.find({
        "doctor_id": ObjectId(doctor_id)
    }).sort("date", -1)

    result = []

    for a in appointments:
        patient = None

        try:
            patient = db.users.find_one({
                "_id": ObjectId(a.get("patient_id"))
            })
        except:
            patient = None

        patient_name = "Unknown Patient"

        if patient:
            patient_name = f'{patient.get("first_name", "")} {patient.get("last_name", "")}'.strip()

        result.append({
            "id": str(a["_id"]),
            "patient_id": a.get("patient_id", ""),
            "patient_name": patient_name,
            "date": a.get("date", ""),
            "status": a.get("status", ""),
            "ecg_url": a.get("ecg_url"),
            "has_ecg": a.get("ecg_url") is not None
        })

    return result


@router.get("/doctor/pending/{doctor_id}")
def get_pending_doctor_appointments(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor id"
        )

    appointments = list(
        db.appointments.find({
            "doctor_id": ObjectId(doctor_id),
            "status": "pending"
        }).sort("date", 1)
    )

    result = []

    for appointment in appointments:
        patient = None

        try:
            patient = db.users.find_one({
                "_id": ObjectId(appointment.get("patient_id"))
            })
        except:
            patient = None

        patient_name = "Unknown Patient"

        if patient:
            patient_name = f'{patient.get("first_name", "")} {patient.get("last_name", "")}'.strip()

        result.append({
            "id": str(appointment["_id"]),
            "patient_id": appointment.get("patient_id", ""),
            "patient_name": patient_name,
            "date": appointment.get("date", ""),
            "status": appointment.get("status", ""),
            "ecg_url": appointment.get("ecg_url"),
            "has_ecg": appointment.get("ecg_url") is not None
        })

    return result


@router.get("/doctor/patients/{doctor_id}")
def get_doctor_patients(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor id"
        )

    patients = db.users.find({
        "doctor_id": ObjectId(doctor_id),
        "role": "patient"
    }).sort("last_name", 1)

    result = []

    for patient in patients:
        result.append({
            "id": str(patient["_id"]),
            "first_name": patient.get("first_name", ""),
            "last_name": patient.get("last_name", ""),
            "email": patient.get("email", ""),
            "date_of_birth": patient.get("date_of_birth", ""),
            "gender": patient.get("gender", ""),
            "height": patient.get("height", ""),
            "weight": patient.get("weight", ""),
            "known_conditions": patient.get("known_conditions", ""),
            "medication": patient.get("medication", ""),
            "city": patient.get("city", ""),
            "doctor_status": patient.get("doctor_status", "")
        })

    return result


@router.get("/doctor/patient-records/{doctor_id}/{patient_id}")
def get_patient_medical_records(
        doctor_id: str,
        patient_id: str,
        range: str = "this_year"
):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor id"
        )

    if not ObjectId.is_valid(patient_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid patient id"
        )

    patient = db.users.find_one({
        "_id": ObjectId(patient_id),
        "doctor_id": ObjectId(doctor_id),
        "role": "patient"
    })

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found for this doctor"
        )

    start, end = get_range_dates(range)

    if start is None:
        return []

    appointments = list(
        db.appointments.find({
            "patient_id": patient_id
        }).sort("date", -1)
    )

    result = []

    for appointment in appointments:
        try:
            appointment_date = datetime.fromisoformat(
                appointment.get("date", "").replace("Z", "")
            )
        except:
            continue

        if appointment_date < start or appointment_date > end:
            continue

        result.append({
            "id": str(appointment["_id"]),
            "patient_id": appointment.get("patient_id", ""),
            "date": appointment.get("date", ""),
            "status": appointment.get("status", ""),
            "ecg_url": appointment.get("ecg_url"),
            "has_ecg": appointment.get("ecg_url") is not None
        })

    return result


@router.put("/update/{appointment_id}")
async def update_appointment(
        appointment_id: str,
        status: str
):
    if not ObjectId.is_valid(appointment_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid appointment id"
        )

    if status not in ["approved", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    appointment = db.appointments.find_one({
        "_id": ObjectId(appointment_id)
    })

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    db.appointments.update_one(
        {
            "_id": ObjectId(appointment_id)
        },
        {
            "$set": {
                "status": status
            }
        }
    )

    if appointment.get("fcm_token"):
        send_notification(
            token=appointment["fcm_token"],
            status=status
        )

    await manager.send_to_patient(
        appointment["patient_id"],
        {
            "type": "appointment_update",
            "status": status
        }
    )

    return {
        "message": "updated"
    }


@router.get("/doctor/incoming-appointments/{doctor_id}")
def get_incoming_appointments(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor id"
        )

    now = datetime.utcnow()

    appointments = list(
        db.appointments.find({
            "doctor_id": ObjectId(doctor_id),
            "status": "approved"
        }).sort("date", 1)
    )

    result = []

    for appointment in appointments:
        try:
            appointment_date = datetime.fromisoformat(
                appointment.get("date", "").replace("Z", "")
            )
        except:
            continue

        if appointment_date < now:
            continue

        patient = None

        try:
            patient = db.users.find_one({
                "_id": ObjectId(appointment.get("patient_id"))
            })
        except:
            patient = None

        patient_name = "Unknown Patient"

        if patient:
            patient_name = f'{patient.get("first_name", "")} {patient.get("last_name", "")}'.strip()

        result.append({
            "appointment_id": str(appointment["_id"]),
            "patient_id": appointment.get("patient_id", ""),
            "patient_name": patient_name,
            "date": appointment.get("date", ""),
            "status": appointment.get("status", ""),
            "ecg_url": appointment.get("ecg_url"),
            "has_ecg": appointment.get("ecg_url") is not None
        })

    return result