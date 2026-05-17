from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional
from datetime import datetime

class PatientSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    date_of_birth: date
    gender: str
    doctor_id: str
    height: float
    weight: float
    known_conditions: Optional[str] = None
    medication: Optional[str] = None
    city: str

