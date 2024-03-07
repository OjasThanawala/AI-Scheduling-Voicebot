import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import API from "./api";

function DoctorAvailability({ onNewTimeSlot }) {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');

    // Generate time options
    const generateTimeOptions = () => {
        const options = [];
        for (let hour = 8; hour <= 18; hour++) { // Up to 6 PM for end time to be at 7 PM
            // Adding :00 and :30 for each hour
            options.push(`${hour.toString().padStart(2, '0')}:00`);
            options.push(`${hour.toString().padStart(2, '0')}:30`);
        }
        return options;
    };

    // Ensure the selected date is not in the past
    const filterPassedTime = time => {
        const currentDate = new Date();
        const selectedDate = new Date(time);

        return currentDate.getTime() < selectedDate.getTime();
    };

    // Handle form submission
    const handleSubmit = async (event) => {
    event.preventDefault();

    // Construct the date and time format expected by the backend
    const formattedDate = selectedDate.toISOString().split('T')[0]; // Format: YYYY-MM-DD
    const start = new Date(`${formattedDate}T${startTime}`);
    const end = new Date(`${formattedDate}T${endTime}`);

    // Ensure the start time is in the future
    if (start < new Date()) {
        alert("Please add appointments atleast 1 day in advance");
        return;
    }

    // Ensure the end time is at least 1 hour after the start time
    if (end <= start || ((end - start) / (1000 * 60 * 60) < 1)) {
        alert("End time must be at least 1 hour after the start time.");
        return;
    }

    try {
        // Submit the new time slot to the backend
        const response = await API.post('/timeslots/', {
            date: formattedDate,
            start_time: startTime,
            end_time: endTime,
        });

        // Optionally, refresh the time slots in the parent component (AdminPage)
        onNewTimeSlot(); // Assuming you pass this function as a prop from AdminPage

        alert("Time slot added successfully.");
    } catch (error) {
        console.error('Error submitting time slot:', error);
        alert("Failed to add time slot.");
    }
    };

    const timeOptions = generateTimeOptions();

    return (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Date:</label>
            <DatePicker
              selected={selectedDate}
              onChange={date => setSelectedDate(date)}
              minDate={new Date()}
              filterDate={filterPassedTime}
              dateFormat="MMMM d, yyyy"
            />
          </div>
          <div className="form-group">
            <label>Start Time:</label>
            <select value={startTime} onChange={e => setStartTime(e.target.value)} required>
                    {timeOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                    ))}
            </select>
          </div>
          <div className="form-group">
            <label>End Time:</label>
            <select value={endTime} onChange={e => setEndTime(e.target.value)} required>
                    {timeOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                    ))}
            </select>
          </div>
          <button type="submit">Submit Availability</button>
        </form>
        );
};

export default DoctorAvailability;