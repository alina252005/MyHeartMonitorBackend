from fastapi import FastAPI
from app.services.firebase_init import init_firebase
from app.api.ecg_routes import router as ecg_router
from app.auth.auth_routes import router as auth_router
from app.admin.admin_routes import router as admin_router
from app.api.appointments_routes import router as appointments_router
from app.api.ws_routes import router as ws_router
from app.api.statistics_routes import router as statistics_router

init_firebase()

app = FastAPI(title="ECG Server")

app.include_router(ecg_router, prefix="/ecg")
app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router, prefix="/admin")
app.include_router(appointments_router, prefix="/appointments")
app.include_router(ws_router)

app.include_router(statistics_router, prefix="/statistics")
@app.get("/")
def root():
    return {"status": "server running"}