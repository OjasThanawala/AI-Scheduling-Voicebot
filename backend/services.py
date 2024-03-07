import json
import os

from sqlalchemy.orm import Session, sessionmaker, relationship
from datetime import datetime, timedelta
import sqlalchemy
from sqlalchemy import create_engine, and_, or_
from google.cloud import speech
from google.cloud import texttospeech

import models
from openai_bot import OpenAIBot
from schemas import TimeSlotModel, MainTimeSlotModel, UserAppointmentModel
from fastapi import HTTPException, UploadFile, File
from sqlitedatabase import database
from fastapi.responses import FileResponse


async def create_time_slot(time_slot):
    try:
        date_obj = datetime.strptime(time_slot.date, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Date format error: {e}")

    # Convert start_time and end_time strings to Python time objects
    try:
        start_time_obj = datetime.strptime(time_slot.start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(time_slot.end_time, "%H:%M").time()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Time format error: {e}")

    # Ensure end_time is after start_time
    if start_time_obj >= end_time_obj:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    # Check for duplicate or overlapping entries
    conflict_query = MainTimeSlotModel.__table__.select().where(
        and_(
            MainTimeSlotModel.date == date_obj,
            or_(
                and_(
                    MainTimeSlotModel.start_time <= start_time_obj,
                    MainTimeSlotModel.end_time > start_time_obj
                ),
                and_(
                    MainTimeSlotModel.start_time < end_time_obj,
                    MainTimeSlotModel.end_time >= end_time_obj
                ),
                and_(
                    start_time_obj <= MainTimeSlotModel.start_time,
                    end_time_obj >= MainTimeSlotModel.end_time
                )
            )
        )
    )
    conflict_result = await database.fetch_one(conflict_query)
    if conflict_result is not None:
        raise HTTPException(status_code=400, detail="Timeslot already added.")

    # Insert into main_time_slots
    main_slot_query = MainTimeSlotModel.__table__.insert().values(
        date=date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj
    )
    main_slot_id = await database.execute(main_slot_query)

    # Calculate and insert each 30-minute slot
    start_datetime = datetime.combine(date_obj, start_time_obj)
    end_datetime = datetime.combine(date_obj, end_time_obj)
    slot_duration = timedelta(minutes=30)

    slots_created = []
    current_slot_start = start_datetime
    while current_slot_start + slot_duration < end_datetime:
        # Insert the current slot into the database
        current_slot_end = current_slot_start + slot_duration
        query = TimeSlotModel.__table__.insert().values(
            date=date_obj,
            start_time=current_slot_start.time(),
            end_time=current_slot_end.time(),
            is_booked=False
        )
        await database.execute(query)

        slots_created.append({
            "date": date_obj.isoformat(),
            "start_time": current_slot_start.time().strftime("%H:%M"),
            "end_time": current_slot_end.time().strftime("%H:%M")
        })

        # Move to the next slot
        current_slot_start += slot_duration

    return {
        "date": date_obj.isoformat(),
        "start_time": start_time_obj.strftime("%H:%M"),
        "end_time": end_time_obj.strftime("%H:%M")
    }


async def get_time_slots():
    query = MainTimeSlotModel.__table__.select()
    return await database.fetch_all(query)


async def delete_time_slot(timeslot_id: int):
    # Fetch the timeslot to check if it's booked
    maintimeslots = MainTimeSlotModel.__table__
    # Fetch the main timeslot by ID to get date, start time, and end time
    main_timeslot_query = maintimeslots.select().where(maintimeslots.c.id == timeslot_id)
    main_timeslot = await database.fetch_one(main_timeslot_query)

    if not main_timeslot:
        raise HTTPException(status_code=404, detail="Main time slot not found")

    date_obj = main_timeslot["date"]
    start_time_obj = main_timeslot["start_time"]
    end_time_obj = main_timeslot["end_time"]

    async with database.transaction():
        # Delete associated 30-minute interval slots from time_slots
        interval_slots_query = TimeSlotModel.__table__.delete().where(
            TimeSlotModel.date == date_obj,
            TimeSlotModel.start_time >= start_time_obj,
            TimeSlotModel.end_time <= end_time_obj
        )
        await database.execute(interval_slots_query)

        # Delete the main timeslot
        delete_main_slot_query = maintimeslots.delete().where(MainTimeSlotModel.id == timeslot_id)
        await database.execute(delete_main_slot_query)

    return {"message": "Main and associated interval time slots deleted successfully"}


async def create_user_appointment(appointment):
    await create_user_appointment_in_db(appointment.user_name, appointment.date, appointment.start_time,
                                        appointment.end_time, appointment.timeslot_id)
    return {"message": "Appointment booked successfully", **appointment.dict()}


async def create_user_appointment_in_db(user_name: str, date: str, start_time: str, end_time: str, timeslot_id: int):
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    start_time_obj = datetime.strptime(start_time, "%H:%M").time()
    end_time_obj = datetime.strptime(end_time, "%H:%M").time()

    query = UserAppointmentModel.__table__.insert().values(
        user_name=user_name,
        date=date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj,
        timeslot_id=timeslot_id
    )
    result = await database.execute(query)
    return result


async def converse_with_voice_bot(file: UploadFile = File(...)):
    if not file.filename.endswith('.wav'):
        raise HTTPException(status_code=400, detail="Only WAV files are accepted")

    # Initialize OpenAIBot here, so it's ready to use in endpoints
    # openai.api_key = "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"
    initial_prompt = get_initial_prompt()
    openai_bot = OpenAIBot(initial_prompt)

    # Save temporary audio file
    temp_file = f"./tmp/{file.filename}"
    with open(temp_file, 'wb+') as f:
        f.write(file.file.read())

    # Initialize Google Cloud Speech client
    client = speech.SpeechClient()
    with open(temp_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        language_code="en-US"
    )

    # Transcribe audio file
    response = client.recognize(config=config, audio=audio)

    # Delete temporary file
    os.remove(temp_file)

    # Process response
    transcription = ""
    for result in response.results:
        transcription += result.alternatives[0].transcript
    print(transcription)

    # Ask OpenAI
    bot_response = openai_bot.ask(transcription)
    print(bot_response)
    try:
        # Extract 'assistant_message_to_the_user' from bot_response
        assistant_response_text = bot_response['assistant_message_to_the_user']

        action = bot_response['action']
        if action:
            if action.lower() == "schedule":
                dateBooked = bot_response['date']
                timeBooked = bot_response['time']
                patientName = bot_response['name']
                if dateBooked and timeBooked and patientName:
                    result = await book_appointment(patientName, dateBooked, timeBooked)
                    print(result)
            elif action.lower() == "reschedule":
                dateBooked = bot_response['date']
                timeBooked = bot_response['time']
                patientName = bot_response['name']
                if dateBooked and timeBooked and patientName:
                    result = await reschedule_appointment(patientName, dateBooked, timeBooked)
                    print(result)
            elif action.lower() == "cancel":
                patientName = bot_response['name']
                if patientName:
                    result = await cancel_appointment(patientName)
                    print(result)

        print(assistant_response_text)
    except json.JSONDecodeError:
        # Handle the case where bot_response is not a valid JSON string
        print("Failed to decode bot_response as JSON.")
        assistant_response_text = "Sorry, I couldn't understand that."
    except KeyError:
        # Handle the case where 'assistant_message_to_the_user' key does not exist
        print("The expected key 'assistant_message_to_the_user' was not found in the bot's response.")
        assistant_response_text = "Sorry, I couldn't process your request."

    voiceMessage = await text_to_speech(assistant_response_text)
    return FileResponse(voiceMessage)


async def text_to_speech(text: str):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # Save the audio to a temporary file and return as a response
    temp_file = "../tmp/output.mp3"
    with open(temp_file, "wb") as out:
        out.write(response.audio_content)
    return temp_file


def get_initial_prompt():
    try:
        with open('history.json', 'r') as file:
            history = json.load(file)
            if history:
                # Convert the list of dictionaries into a string prompt
                initial_prompt = "\n".join(f"{item['role']}: {item['content']}" for item in history)
                return initial_prompt
    except FileNotFoundError:
        return "System: Welcome to Dr. Walnut's Clinic."  # Default prompt if file doesn't exist


async def book_appointment(user_name: str, appointment_date: str, appointment_start_time: str):
    # Convert string dates and times to proper datetime objects
    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d").date()
    start_time_obj = datetime.strptime(appointment_start_time, "%H:%M").time()
    start_datetime_obj = datetime.combine(date_obj, start_time_obj)
    # Add 30 minutes to the datetime object
    end_datetime_obj = start_datetime_obj + timedelta(minutes=30)
    # Extract the time part for the end time
    end_time_obj = end_datetime_obj.time()

    # Find an available timeslot
    timeslot_query = TimeSlotModel.__table__.select().where(
        TimeSlotModel.date == date_obj,
        TimeSlotModel.start_time == start_time_obj,
        TimeSlotModel.end_time == end_time_obj,
        TimeSlotModel.is_booked == False
    )
    timeslot = await database.fetch_one(timeslot_query)

    if not timeslot:
        return {"error": "Timeslot not available or already booked"}

    # Mark the timeslot as booked
    update_query = TimeSlotModel.__table__.update().where(
        TimeSlotModel.id == timeslot["id"]
    ).values(is_booked=True)
    await database.execute(update_query)

    # Create a new UserAppointment
    appointment_query = UserAppointmentModel.__table__.insert().values(
        user_name=user_name,
        date=date_obj,
        start_time=start_time_obj,
        end_time=end_time_obj,  # Assuming end_time is a time object or properly formatted string
        timeslot_id=timeslot["id"]
    )
    print(user_name + " " + appointment_date + " " + appointment_start_time + " " + str(timeslot["id"]))
    await database.execute(appointment_query)

    return {"message": "Appointment booked successfully"}


async def reschedule_appointment(user_name: str, new_date: str, new_start_time: str):
    # First, cancel the existing appointment
    cancel_result = await delete_appointment(user_name)
    if "error" in cancel_result:
        # If there was an error cancelling, return the error
        return cancel_result

    # Book a new appointment with the new date and start time
    booking_result = await book_appointment(user_name, new_date, new_start_time)

    return booking_result


async def cancel_appointment(user_name: str):
    result = await delete_appointment(user_name)
    if "error" in result:
        return {"error": "No existing appointment found"}
    return {"message": "Appointment canceled successfully"}


async def delete_appointment(user_name: str):
    # Find the existing appointment by user_name
    existing_appointment_query = UserAppointmentModel.__table__.select().where(
        UserAppointmentModel.user_name == user_name
    )
    existing_appointment = await database.fetch_one(existing_appointment_query)

    if not existing_appointment:
        return {"error": "No existing appointment found"}

    # Mark the associated timeslot as not booked
    update_timeslot_query = TimeSlotModel.__table__.update().where(
        TimeSlotModel.id == existing_appointment["timeslot_id"]
    ).values(is_booked=False)
    await database.execute(update_timeslot_query)

    # Delete the appointment
    delete_appointment_query = UserAppointmentModel.__table__.delete().where(
        UserAppointmentModel.id == existing_appointment["id"]
    )
    await database.execute(delete_appointment_query)

    return {"message": "Appointment successfully cancelled"}


async def synthesize_speech(text: models.SynthesizeRequest):
    textMessage = text.text
    voiceMessage = await text_to_speech(textMessage)
    return FileResponse(voiceMessage)


async def clear_history():
    try:
        # Check if the file exists before trying to delete it
        if os.path.exists("history.json"):
            # Delete the history.json file
            os.remove("history.json")
            message = "History cleared successfully"
        else:
            # File does not exist; no action needed
            message = "History file does not exist, no action taken"

        print(message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")

    # Fetch all not booked timeslots
    query = TimeSlotModel.__table__.select().where(TimeSlotModel.__table__.c.is_booked == False)
    not_booked_slots = await database.fetch_all(query)

    # Format the timeslots into a JSON string
    timeslots_info = [
        {
            "Date": slot["date"],
            "Start Time": slot["start_time"]
        } for slot in not_booked_slots
    ]

    # Generate the prompt
    initialSystemText = """
    Hi, you are a scheduling assistant for Dr. Walnut's clinic. You need to assist a user to book an appointment at the clinic. As an assistant, you will already have the list of timeslots that the doctor is available at, which will be added at the end of this message. This list will be of type:
    ###
    [
    {"Date": "Date here", "Start Time": "Start time here"
    }
    ]
    ###

    Now, the user has 3 available actions:
    1. Schedule an appointment
    2. Reschedule an existing appointment
    3. Cancel an appointment.
    If you cannot extract an action out of the above  3 options, return a message asking them to provide 1 of the actions from above.
    If you can extract an action, based on the action do the following:
    1 . Schedule - Ask for the date & time the user would like to schedule this appointment.
    2. Reschedule - Ask for the date & time the user would like to reschedule.
    3. Cancel - Ask for the name of the user.
    Based on the user's response, if you cannot extract the date and time or the name of the user, ask them for the same again.
    If you can extract, check whether the date and start time provided are included in the Available Timeslots list. You will iterate through this list and find if there's an available matching date and start time. If not, respond back to the user letting them know that the date or time is not available and provide them with some options of dates/time that are available closest to their previously chosen time.
    If you can extract a valid date and time, and if the action is to schedule or reschedule appointment, you need to ask the user for their name.
    In case of cancel appointment, you only need the name.
    Once you have the time(in case of schedule/reschedule) and name, you need to consolidate this info in a json format with the following fields:

    ###
    date: Extracted date or null if not present. Formate of date: YYYY-MM-DD
    time: Extracted time or null if not present. Format of time: HH:MM
    name: Extracted name or null if not present
    assistant_message_to_the_user: Message that you would like to send back to the user
    context: Anything else you want to say 
    action: SCHEDULE if user action is to schedule an appointment, RESCHEDULE if user action is to REschedule an appointment, CANCEL if user action is to cancel an appointment, UNRELATED in all other cases
    ###

    Make sure that you return the output only as a json. In case the user asks you start again, you can start again but make sure to return the output as a json.
    """
    prompt_text = initialSystemText + "\n\nAvailable timeslots:\n ### \n" + json.dumps(timeslots_info,
                                                                                       default=str) + "\n###\n"
    try:
        history_content = [{"role": "system", "content": prompt_text}]
        with open("history.json", "w") as history_file:
            json.dump(history_content, history_file)
        print(history_content)
        return {"message": "User registered and history updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing registration: {str(e)}")

