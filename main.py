import os
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from database import db, create_document, get_documents
from schemas import Service, Appointment

app = FastAPI(title="Salon Naročanje API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENING_HOURS = {
    "ponedeljek": {"period": "dopoldne", "start": "08:00", "end": "12:00"},
    "torek": {"period": "dopoldne", "start": "08:00", "end": "12:00"},
    "sreda": {"period": "popoldne", "start": "14:00", "end": "19:00"},
    "četrtek": {"period": "popoldne", "start": "14:00", "end": "19:00"},
    "petek": {"period": "popoldne", "start": "14:00", "end": "19:00"},
    "sobota": {"period": "popoldne", "start": "14:00", "end": "18:00"},
}

SERVICES: List[Service] = [
    Service(key="striženje", title="Striženje", min_duration=15, max_duration=30, step=15, price_from=15),
    Service(key="barvanje", title="Barvanje", min_duration=90, max_duration=240, step=30, price_from=40),
]

class AvailabilityRequest(BaseModel):
    date: str  # YYYY-MM-DD
    service: str
    duration_minutes: int

class AvailabilitySlot(BaseModel):
    start: str
    end: str

@app.get("/")
def read_root():
    return {"message": "Salon API je pripravljen"}

@app.get("/api/services", response_model=List[Service])
def list_services():
    return SERVICES

@app.get("/api/opening-hours")
def opening_hours():
    return OPENING_HOURS

@app.post("/api/availability", response_model=List[AvailabilitySlot])
def get_availability(payload: AvailabilityRequest):
    try:
        date_obj = datetime.strptime(payload.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Neveljaven datum")

    weekday = ["ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja"][date_obj.weekday()]
    if weekday == "nedelja" or weekday not in OPENING_HOURS:
        return []

    window = OPENING_HOURS[weekday]
    start_dt = datetime.combine(date_obj.date(), datetime.strptime(window["start"], "%H:%M").time())
    end_dt = datetime.combine(date_obj.date(), datetime.strptime(window["end"], "%H:%M").time())

    # Fetch existing appointments for that date
    existing = get_documents("appointment", {"date": payload.date}) if db else []

    # Build time slots every 15 minutes
    step = timedelta(minutes=15)
    needed = timedelta(minutes=payload.duration_minutes)
    slots: List[AvailabilitySlot] = []

    t = start_dt
    while t + needed <= end_dt:
        slot_start = t
        slot_end = t + needed
        # check overlap with existing
        conflict = False
        for ap in existing:
            ap_start = datetime.strptime(f"{ap['date']} {ap['start_time']}", "%Y-%m-%d %H:%M")
            ap_end = datetime.strptime(f"{ap['date']} {ap.get('end_time', ap['start_time'])}", "%Y-%m-%d %H:%M")
            if not (slot_end <= ap_start or slot_start >= ap_end):
                conflict = True
                break
        if not conflict:
            slots.append(AvailabilitySlot(start=slot_start.strftime("%H:%M"), end=slot_end.strftime("%H:%M")))
        t += step

    return slots

@app.post("/api/appointments")
def create_appointment(appt: Appointment):
    # Compute end_time
    try:
        start_dt = datetime.strptime(f"{appt.date} {appt.start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Neveljaven datum ali ura")

    appt.end_time = (start_dt + timedelta(minutes=appt.duration_minutes)).strftime("%H:%M")

    # Check within opening hours
    weekday = ["ponedeljek", "torek", "sreda", "četrtek", "petek", "sobota", "nedelja"][start_dt.weekday()]
    if weekday == "nedelja" or weekday not in OPENING_HOURS:
        raise HTTPException(status_code=400, detail="Ta dan ne delamo")
    window = OPENING_HOURS[weekday]
    wnd_start = datetime.combine(start_dt.date(), datetime.strptime(window["start"], "%H:%M").time())
    wnd_end = datetime.combine(start_dt.date(), datetime.strptime(window["end"], "%H:%M").time())

    if start_dt < wnd_start or (start_dt + timedelta(minutes=appt.duration_minutes)) > wnd_end:
        raise HTTPException(status_code=400, detail="Izven delovnega časa")

    # Overlap check
    existing = get_documents("appointment", {"date": appt.date}) if db else []
    for ap in existing:
        ap_start = datetime.strptime(f"{ap['date']} {ap['start_time']}", "%Y-%m-%d %H:%M")
        ap_end = datetime.strptime(f"{ap['date']} {ap['end_time']}", "%Y-%m-%d %H:%M")
        if not ((start_dt + timedelta(minutes=appt.duration_minutes)) <= ap_start or start_dt >= ap_end):
            raise HTTPException(status_code=409, detail="Termin je že zaseden")

    # Save
    doc_id = create_document("appointment", appt.model_dump()) if db else None
    return {"status": "ok", "id": doc_id, "end_time": appt.end_time}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
    }
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
