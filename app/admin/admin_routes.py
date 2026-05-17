from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.db.mongo import users_collection

router = APIRouter(tags=["Admin Management"])


@router.get("/pending-physicians")
def get_pending_physicians():

    pending_doctors = list(
        users_collection.find(
            {
                "role": "doctor",
                "approval_status": "pending"
            },
            {
                "password": 0
            }
        )
    )

    for doc in pending_doctors:
        doc["_id"] = str(doc["_id"])

    return pending_doctors


@router.post("/verify-physician/{physician_id}")
def verify_physician(physician_id: str, action: str):

    if not ObjectId.is_valid(physician_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid physician id"
        )

    if action not in ["approve", "deny"]:
        raise HTTPException(
            status_code=400,
            detail="Action must be approve or deny"
        )

    if action == "approve":
        status = "approved"
        is_approved = True
    else:
        status = "denied"
        is_approved = False

    result = users_collection.update_one(
        {
            "_id": ObjectId(physician_id),
            "role": "doctor"
        },
        {
            "$set": {
                "approval_status": status,
                "is_approved": is_approved
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Medicul nu a fost gasit"
        )

    return {
        "message": f"Medicul a fost {status} cu succes"
    }