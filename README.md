# Dr. Walnut's Clinic Voice-Interactive Scheduling Assistant

Welcome to Dr. Walnut's Clinic Voice-Interactive Scheduling Assistant. This application provides a seamless way for patients to schedule, reschedule, or cancel appointments using their voice, and for the clinic's doctor to manage appointment timeslots.

## Workflow Overview

### For Users (Patients):
- On the home page, navigate to the "Patient" portal.
- Upon entering, click on the Start button to interact with the voicebot,which will greet you with a voice message.
- Initiate your query, such as booking an appointment, by clicking "Start Recording."
- The application converts the speech to text using a STT service and processes the query through OpenAI's Chat API.
- Receive a spoken response generated by the TTS service, providing you with the details of your appointment or asking for further information if required. Note that receiving a response has a slight delay. Wait for 3-4 seconds before hearing the response.
- Continue conversing with the voicebot based on the response received, until the intended task is complete.

### For Doctors (Admins):
- Doctors can access the "Doctor" page to manage their availability by adding or removing timeslots.
- All available timeslots are stored in a database and are used by the AI to inform users about the doctor's availability.

## Building the App

This app can be built and run using Docker.
### Pre-requisites:
- Ensure that Docker is installed on your machine and is running.
- Clone the repository from GitHub:
  - git clone https://github.com/OjasThanawala/AI-Scheduling-Voicebot.git
  - cd AI-Scheduling-Voicebot
- This app requires an api-key from OpenAI which will be used to authenticate and run the voicebot. 
  - Please go to https://platform.openai.com/api-keys and generate or use an existing key. 
  - Add this key to the .env file within the /backend directory as the value for OPENAI_API_KEY.
- This app also requires a Google Client Service account key.
  - If you want to use your own key, follow this guide to create a service account and generate they key: https://developers.google.com/workspace/guides/create-credentials#service-account.
  
    - Note that you would need to need create a role which has access to the Google Speech and TextToSpeech APIs (can be found here: https://cloud.google.com/speech-to-text/docs/before-you-begin)
  - Otherwise, contact the repository admin to acquire the necessary JSON file.
  - Place this file in the /backend directory of the repository.
  - Record the file path (e.g., "./gc-account-key.json") and add it to the .env file next to the GOOGLE_APPLICATION_CREDENTIALS key.

## Running the App
Use the provided run.sh script to build and start the Docker container:
- ./run.sh

Alternatively, run the app manually using command:
- docker-compose up --build -d

Once the docker container is ready, access the app at `http://localhost`

For detailed installation and usage instructions, please refer to the [Project Documentation](/docs/Project Documentation.pdf).
For the project timeline, please refert to the [Project Timeline](/docs/Project Timeline.pdf)

Note: Keep all API keys secure and never commit them to public version control repositories.
