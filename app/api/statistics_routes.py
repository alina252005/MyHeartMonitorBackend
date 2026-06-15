from fastapi import APIRouter
from datetime import datetime, timedelta
from bson import ObjectId
from app.db.mongo import ecg_collection
from app.db.mongo import ecg_results_collection
from app.db.mongo import appointments_collection

router = APIRouter()



def get_range(range_value):

    now = datetime.utcnow()

    if range_value == "this_week":

        start = now - timedelta(days=now.weekday())
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        fmt = "%Y-%m-%d"

    elif range_value == "last_week":

        start = now - timedelta(days=now.weekday() + 7)
        end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        fmt = "%Y-%m-%d"

    elif range_value == "this_month":

        start = datetime(now.year, now.month, 1)

        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)

        end = next_month - timedelta(seconds=1)
        fmt = "%Y-%m-%d"

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

        fmt = "%Y-%m-%d"

    elif range_value == "last_6_months":

        start = now - timedelta(days=180)
        end = now
        fmt = "%Y-%m"

    elif range_value == "this_year":

        start = datetime(now.year, 1, 1)

        end = datetime(
            now.year,
            12,
            31,
            23,
            59,
            59
        )

        fmt = "%Y-%m"

    elif range_value == "last_year":

        start = datetime(now.year - 1, 1, 1)

        end = datetime(
            now.year - 1,
            12,
            31,
            23,
            59,
            59
        )

        fmt = "%Y-%m"

    else:
        return None, None, None

    return start, end, fmt


@router.get("/ecg-count/{patient_id}")
def get_ecg_count(patient_id: str, range: str):

    start, end, fmt = get_range(range)

    if not start:
        return []

    pipeline = [
        {
            "$match": {
                "patient_id": patient_id,
                "timestamp": {
                    "$gte": start,
                    "$lte": end
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": fmt,
                        "date": "$timestamp"
                    }
                },
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    return list(ecg_collection.aggregate(pipeline))


CLASSES = [0, 1, 2, 3, 4]
@router.get("/ml-evolution/{patient_id}")
def get_ml_evolution(patient_id: str, range: str):

    start, end, fmt = get_range(range)

    if not start:
        return []

    pipeline = [
        {
            "$match": {
                "patient_id": patient_id,
                "created_at": {
                    "$gte": start,
                    "$lte": end
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "date": {
                        "$dateToString": {
                            "format": fmt,
                            "date": "$created_at"
                        }
                    },
                    "prediction": "$prediction"
                },
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$group": {
                "_id": "$_id.date",
                "data": {
                    "$push": {
                        "prediction": "$_id.prediction",
                        "count": "$count"
                    }
                },
                "total": {
                    "$sum": "$count"
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    raw = list(ecg_results_collection.aggregate(pipeline))

    result = []

    for item in raw:

        counts = {
            str(c): 0 for c in CLASSES
        }

        for d in item["data"]:

            cls = str(d["prediction"])

            if cls not in counts:
                cls = "4"

            counts[cls] += d["count"]

        result.append({
            "_id": item["_id"],
            "total": item["total"],
            "data": counts
        })

    return result


@router.get("/bpm-evolution/{patient_id}")
def get_bpm_evolution(patient_id: str, range: str):

    start, end, fmt = get_range(range)

    if not start:
        return []

    pipeline = [
        {
            "$match": {
                "patient_id": patient_id,
                "timestamp": {
                    "$gte": start,
                    "$lte": end
                },
                "bpm": {
                    "$ne": None
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": fmt,
                        "date": "$timestamp"
                    }
                },
                "avg_bpm": {
                    "$avg": "$bpm"
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    data = list(ecg_collection.aggregate(pipeline))

    result = []

    for item in data:

        result.append({
            "_id": item["_id"],
            "avg_bpm": round(item["avg_bpm"], 1)
        })

    return result


@router.get("/appointments-count/{patient_id}")
def get_appointments_count(patient_id: str, range: str):

    start, end, fmt = get_range(range)

    if not start:
        return []

    pipeline = [
        {
            "$match": {
                "patient_id": patient_id
            }
        },
        {
            "$addFields": {
                "realDate": {
                    "$dateFromString": {
                        "dateString": "$date",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },
        {
            "$match": {
                "realDate": {
                    "$ne": None,
                    "$gte": start,
                    "$lte": end
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": fmt,
                        "date": "$realDate"
                    }
                },
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    return list(appointments_collection.aggregate(pipeline))


@router.get("/doctor/appointments-overview/{doctor_id}")
def get_doctor_appointments_overview(doctor_id: str, range: str):

    start, end, fmt = get_range(range)

    if not start:
        return []

    if not ObjectId.is_valid(doctor_id):
        return []

    pipeline = [
        {
            "$match": {
                "doctor_id": ObjectId(doctor_id)
            }
        },
        {
            "$addFields": {
                "realDate": {
                    "$dateFromString": {
                        "dateString": "$date",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },
        {
            "$match": {
                "realDate": {
                    "$ne": None,
                    "$gte": start,
                    "$lte": end
                }
            }
        },
        {
            "$project": {
                "_id": {
                    "$toString": "$_id"
                },
                "label": {
                    "$dateToString": {
                        "format": "%Y-%m-%d %H:%M",
                        "date": "$realDate"
                    }
                },
                "count": {
                    "$literal": 1
                },
                "status": "$status"
            }
        },
        {
            "$sort": {
                "label": 1
            }
        }
    ]

    return list(appointments_collection.aggregate(pipeline))

@router.get("/doctor/status-distribution/{doctor_id}")
def get_doctor_status_distribution(doctor_id: str, range: str):

    start, end, fmt = get_range(range)

    if not start:
        return {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "total": 0
        }

    if not ObjectId.is_valid(doctor_id):
        return {
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "total": 0
        }

    pipeline = [
        {
            "$match": {
                "doctor_id": ObjectId(doctor_id)
            }
        },
        {
            "$addFields": {
                "realDate": {
                    "$dateFromString": {
                        "dateString": "$date",
                        "onError": None,
                        "onNull": None
                    }
                }
            }
        },
        {
            "$match": {
                "realDate": {
                    "$ne": None,
                    "$gte": start,
                    "$lte": end
                }
            }
        },
        {
            "$group": {
                "_id": "$status",
                "count": {
                    "$sum": 1
                }
            }
        }
    ]

    raw = list(appointments_collection.aggregate(pipeline))

    result = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "total": 0
    }

    for item in raw:

        status = item["_id"]
        count = item["count"]

        if status in result:
            result[status] = count
            result["total"] += count

    return result