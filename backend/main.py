import os

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import schemas
from schemas import MainTimeSlotModel, TimeSlotModel, UserAppointmentModel
import models
import services
from typing import List
import sqlitedatabase
from sqlitedatabase import database, engine

sqlitedatabase.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware to allow requests from our React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.getenv('GOOGLE_APPLICATION_CREDENTIALS', "./../gc-speech.json")


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/timeslots/")
async def create_time_slot(time_slot: models.MainTimeSlot):
    return await services.create_time_slot(time_slot=time_slot)


@app.get("/timeslots/")
async def read_time_slots():
    return await services.get_time_slots()


@app.post("/user_appointments/")
async def create_user_appointment(appointment: models.UserAppointment):
    return await services.create_user_appointment(appointment=appointment)


@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    return await services.converse_with_voice_bot(file)


@app.post("/synthesize/")
async def synthesize_speech(text: models.SynthesizeRequest):
    return await services.synthesize_speech(text)


@app.delete("/timeslots/{timeslot_id}/")
async def delete_time_slot(timeslot_id: int):
    return await services.delete_time_slot(timeslot_id)


@app.post("/clear-history/")
async def clear_history():
    return await services.clear_history()
