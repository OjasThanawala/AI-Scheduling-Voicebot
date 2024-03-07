import React, { useState, useEffect } from 'react';
import DoctorAvailability from './DoctorAvailability';
import API from "./api";

function AdminPage() {
  const [timeSlots, setTimeSlots] = useState([]);

  useEffect(() => {
    // Fetch time slots
    API.get('/timeslots/')
      .then(response => {
        setTimeSlots(response.data);
      })
      .catch(error => console.error('There was an error!', error));
  }, []);

  const refreshTimeSlots = () => {
    // Function to refresh the list of time slots after adding a new one
    API.get('/timeslots/')
      .then(response => {
        setTimeSlots(response.data);
      })
      .catch(error => console.error('There was an error!', error));
  };

  const deleteTimeSlot = (timeslotId) => {
    API.delete(`/timeslots/${timeslotId}/`)
      .then(() => {
        refreshTimeSlots(); // Refresh the list after deletion
      })
      .catch(error => {
        console.error('Error deleting time slot:', error);
        alert(error.response.data.detail); // Show error message from backend
      });
  };

  // Placeholder for admin interface to manage time slots
  return (
    <div>
      <h2>Doctors Availability</h2>
      <h2> Add Time Slots - </h2>
      <DoctorAvailability onNewTimeSlot={refreshTimeSlots} />
      <div>
        <h2> Current Time Slots -</h2>
        {timeSlots.map((slot, index) => (
          <div key={index} className="timeslot-container">
            <div className="timeslot-details">
              <p className="label">Date:</p>
              <p>{slot.date}</p>
              <p className="label">Start Time:</p>
              <p>{slot.start_time}</p>
              <p className="label">End Time:</p>
              <p>{slot.end_time}</p>
              <button className="removeButton" onClick={() => deleteTimeSlot(slot.id)} disabled={slot.is_booked} title={slot.is_booked ? "Cannot remove appointment as it is already booked" : ""}>
              Remove
            </button>
            </div>

          </div>
        ))}
    </div>
</div>
  );
}

export default AdminPage;
