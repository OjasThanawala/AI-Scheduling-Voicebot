from sqlitedatabase import Base
import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship


class TimeSlotModel(Base):
    __tablename__ = "time_slots"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    date = sqlalchemy.Column(sqlalchemy.Date)
    start_time = sqlalchemy.Column(sqlalchemy.Time)
    end_time = sqlalchemy.Column(sqlalchemy.Time)
    is_booked = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    # Relationship (optional, for ORM use)
    appointments = relationship("UserAppointmentModel", back_populates="timeslot")


class UserAppointmentModel(Base):
    __tablename__ = "user_appointments"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)  # Auto-generated unique key
    user_name = sqlalchemy.Column(sqlalchemy.String, index=True)
    date = sqlalchemy.Column(sqlalchemy.Date)
    start_time = sqlalchemy.Column(sqlalchemy.Time)
    end_time = sqlalchemy.Column(sqlalchemy.Time)
    timeslot_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('time_slots.id'))

    # Relationship (optional, for ORM use)
    timeslot = sqlalchemy.orm.relationship("TimeSlotModel", back_populates="appointments")


class MainTimeSlotModel(Base):
    __tablename__ = "main_time_slots"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    date = sqlalchemy.Column(sqlalchemy.Date)
    start_time = sqlalchemy.Column(sqlalchemy.Time)
    end_time = sqlalchemy.Column(sqlalchemy.Time)
