import React, { useState, useEffect } from 'react';
import API from "./api";

function UserPage() {
    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState(null);
    const [audioURL, setAudioURL] = useState('');
    const [transcription, setTranscription] = useState('');
    const [started, setStarted] = useState(false);

    const startProcess = async () => {
        try {
            // Clear history
            await API.post('/clear-history/');
            console.log('History cleared successfully');
            // Play the initial welcome message
            const welcomeText = "Welcome to Dr. Walnut's Clinic! Would you like to schedule, reschedule, or cancel an appointment?";
            playResponse(welcomeText);

            // Indicate the process has started
            setStarted(true);
            } catch (error) {
                console.error('Failed to clear history:', error);
            }
    };

    const startRecording = async () => {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream);
            setMediaRecorder(recorder);

            let chunks = [];
            recorder.ondataavailable = e => chunks.push(e.data);
            recorder.onstop = async () => {
                const blob = new Blob(chunks, { type: 'audio/wav' });
                chunks = [];
                const audioUrl = URL.createObjectURL(blob);
                setAudioURL(audioUrl);

                // Upload audio file to the backend for transcription
                const formData = new FormData();
                formData.append('file', blob, 'user_audio.wav');
                const response = await API.post('/transcribe/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    responseType: 'blob'  // Important for handling the binary audio response
                });
                try{
                // Creating a URL for the blob response
                const audioUrlResponse = URL.createObjectURL(response.data);
                const audioToPlay = new Audio(audioUrlResponse);
                audioToPlay.play();
                } catch (error) {
                console.error('Error synthesizing text to speech:', error);
                }
            };

            recorder.start();
            setIsRecording(true);
        } else {
            console.error('Audio recording is not supported in this browser.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorder) {
            mediaRecorder.stop();
            setIsRecording(false);
        }
    };

    const playResponse = async (text) => {
        try {
        // Sending the text to the backend to get the synthesized speech
        const response = await API.post('/synthesize/', { text: text }, {
            headers: {
                'Content-Type': 'application/json',
            },
            responseType: 'blob'  // Important for handling the binary audio response
        });

        // Creating a URL for the blob response
        const audioUrl = URL.createObjectURL(response.data);

        // Playing the audio
        const audio = new Audio(audioUrl);
        audio.play();
        } catch (error) {
        console.error('Error synthesizing text to speech:', error);
        }
    };

    return (
        <div className="center-container">
            <h2>User Voice Interface</h2>
            {!started ? (
                <button onClick={startProcess}>Start</button>
            ) : isRecording ? (
                <button onClick={stopRecording}>Stop Recording</button>
            ) : (
                <button onClick={startRecording}>Start Recording</button>
            )}
        </div>
    );
}

export default UserPage;