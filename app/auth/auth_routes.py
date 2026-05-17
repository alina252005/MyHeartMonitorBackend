from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, EmailStr

from app.core.security import verify_password, create_access_token, hash_password
from app.models.user_models import PatientSignup
from app.db.mongo import users_collection

router = APIRouter()


class PhysicianSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    specialization: str
    license_number: str
    hospital_clinic: str
    city: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/signup/patient")
def signup_patient(data: PatientSignup):
    existing_user = users_collection.find_one({
        "email": data.email
    })

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    try:
        doctor_object_id = ObjectId(data.doctor_id)
    except:
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor ID"
        )

    doctor = users_collection.find_one({
        "_id": doctor_object_id,
        "role": "doctor",
        "approval_status": "approved"
    })

    if not doctor:
        raise HTTPException(
            status_code=400,
            detail="Doctor not valid or not approved"
        )

    patient_data = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "password": hash_password(data.password),
        "date_of_birth": data.date_of_birth.isoformat(),
        "gender": data.gender,
        "doctor_id": doctor_object_id,
        "height": data.height,
        "weight": data.weight,
        "known_conditions": data.known_conditions,
        "medication": data.medication,
        "city": data.city,
        "role": "patient",
        "doctor_status": "pending",
        "created_at": datetime.utcnow()
    }

    users_collection.insert_one(patient_data)

    return {
        "message": "Patient account created. Waiting for doctor approval."
    }


@router.post("/signup/physician")
def signup_physician(data: PhysicianSignup):
    if users_collection.find_one({"email": data.email}):
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    physician_dict = data.dict()

    physician_dict.update({
        "password": hash_password(data.password),
        "role": "doctor",
        "is_approved": False,
        "approval_status": "pending",
        "created_at": datetime.utcnow()
    })

    users_collection.insert_one(physician_dict)

    return {
        "message": "Account created successfully. Waiting for admin approval."
    }


@router.get("/doctors")
def search_doctors(search: str = ""):
    query = {
        "role": "doctor",
        "approval_status": "approved"
    }

    if search:
        query["$or"] = [
            {
                "first_name": {
                    "$regex": search,
                    "$options": "i"
                }
            },
            {
                "last_name": {
                    "$regex": search,
                    "$options": "i"
                }
            }
        ]

    doctors_cursor = users_collection.find(query)

    doctors_list = []

    for doc in doctors_cursor:
        doctors_list.append({
            "_id": str(doc["_id"]),
            "full_name": f"{doc.get('first_name', '')} {doc.get('last_name', '')}".strip(),
            "specialty": doc.get("specialization", "General"),
            "city": doc.get("city", "")
        })

    return doctors_list


@router.post("/login")
def login_user(request: LoginRequest):
    user = users_collection.find_one({
        "email": request.email
    })

    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid email or password"
        )

    token_data = {
        "sub": str(user["_id"]),
        "role": user.get("role", "patient")
    }

    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user["_id"]),
        "role": user.get("role", "patient")
    }


@router.get("/me/{user_id}")
def get_user(user_id: str):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user id"
        )

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    role = user.get("role", "")

    if role == "doctor":
        return {
            "id": str(user["_id"]),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", ""),
            "specialization": user.get("specialization", ""),
            "license_number": user.get("license_number", ""),
            "hospital_clinic": user.get("hospital_clinic", ""),
            "city": user.get("city", ""),
            "is_approved": user.get("is_approved", False),
            "approval_status": user.get("approval_status", "")
        }

    if role == "patient":
        return {
            "id": str(user["_id"]),
            "first_name": user.get("first_name", ""),
            "last_name": user.get("last_name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", ""),
            "date_of_birth": user.get("date_of_birth", ""),
            "gender": user.get("gender", ""),
            "height": user.get("height", ""),
            "weight": user.get("weight", ""),
            "known_conditions": user.get("known_conditions", ""),
            "medication": user.get("medication", ""),
            "city": user.get("city", ""),
            "doctor_id": str(user["doctor_id"]) if user.get("doctor_id") else None,
            "doctor_status": user.get("doctor_status", "")
        }

    return {
        "id": str(user["_id"]),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "email": user.get("email", ""),
        "role": role
    }


@router.put("/update/{user_id}")
def update_user(user_id: str, data: dict):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid user id"
        )

    user = users_collection.find_one({
        "_id": ObjectId(user_id)
    })

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    blocked_fields = [
        "_id",
        "password",
        "role",
        "created_at",
        "is_approved",
        "approval_status"
    ]

    for field in blocked_fields:
        data.pop(field, None)

    users_collection.update_one(
        {
            "_id": ObjectId(user_id)
        },
        {
            "$set": data
        }
    )

    return {
        "message": "Profile updated successfully"
    }


@router.put("/change-password/{user_id}")
def change_password(user_id: str, data: ChangePasswordRequest):
    try:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid user id"
            )

        user = users_collection.find_one({
            "_id": ObjectId(user_id)
        })

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        if not verify_password(data.old_password, user["password"]):
            raise HTTPException(
                status_code=400,
                detail="Old password is incorrect"
            )

        if len(data.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters"
            )

        if data.old_password == data.new_password:
            raise HTTPException(
                status_code=400,
                detail="New password must be different"
            )

        users_collection.update_one(
            {
                "_id": ObjectId(user_id)
            },
            {
                "$set": {
                    "password": hash_password(data.new_password)
                }
            }
        )

        return {
            "message": "Password updated successfully"
        }

    except HTTPException as e:
        raise e

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Password update failed"
        )


@router.get("/doctor/{doctor_id}")
def get_doctor(doctor_id: str):
    if not ObjectId.is_valid(doctor_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid doctor id"
        )

    doctor = users_collection.find_one({
        "_id": ObjectId(doctor_id),
        "role": "doctor"
    })

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    return {
        "id": str(doctor["_id"]),
        "first_name": doctor.get("first_name", ""),
        "last_name": doctor.get("last_name", ""),
        "email": doctor.get("email", ""),
        "role": doctor.get("role", ""),
        "specialization": doctor.get("specialization", ""),
        "license_number": doctor.get("license_number", ""),
        "hospital_clinic": doctor.get("hospital_clinic", ""),
        "city": doctor.get("city", ""),
        "is_approved": doctor.get("is_approved", False),
        "approval_status": doctor.get("approval_status", "")
    }