from pydantic import BaseModel


class TimeSlot(BaseModel):
    date: str
    start_time: str
    end_time: str


class UserAppointment(BaseModel):
    user_name: str
    date: str
    start_time: str
    end_time: str
    timeslot_id: int


class MainTimeSlot(BaseModel):
    date: str
    start_time: str
    end_time: str


class SynthesizeRequest(BaseModel):
    text: str
