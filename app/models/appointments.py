from pydantic import BaseModel

class AppointmentRequest(BaseModel):
    patient_id: str
    date: str
    ecg_url: str | None = None
    fcm_token: str | None = None