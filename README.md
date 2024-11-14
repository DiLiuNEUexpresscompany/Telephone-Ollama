# Telephone-Ollama

This project demonstrates how to integrate Twilio's telephony API with a locally hosted Large Language Model (LLM) API, specifically Ollama, using FastAPI. The project enables interactive voice and SMS-based conversations with a chatbot, with message handling and rate limiting implemented to manage user requests.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Voice Interaction**: Users can call the chatbot, and it responds based on input processed through the Ollama LLM.
- **SMS Interaction**: Users can text the chatbot, and it replies with the processed response.
- **Rate Limiting**: Manages the number of calls and SMS per user per day to prevent abuse.
- **Logging**: Tracks application events, errors, and API calls for easier debugging and monitoring.

## Prerequisites

- Python 3.8 or later
- Twilio account (for telephony and SMS API)
- [ngrok](https://ngrok.com/) (for exposing localhost to the internet)
- Ollama API (hosted locally, or customize to use an alternative LLM API if needed)

## Installation

1. Clone the repository:
```
git clone https://github.com/DiLiuNEUexpresscompany/Telephone-Ollama
cd Telephony-Ollama  
```
2. Install Python dependencies:
```
pip install -r requirements.txt
```

3. Install and configure ngrok:
- Download and install ngrok from [ngrok download page](https://ngrok.com/download).
- Start ngrok to expose your localhost: `ngrok http 8000`

## Configuration

1. Environment Variables:
- Create a `.env` file in the project root directory with the following content:
  ```
  TWILIO_ACCOUNT_SID=your_account_sid
  TWILIO_AUTH_TOKEN=your_auth_token
  TWILIO_PHONE_NUMBER=your_twilio_phone_number
  OLLAMA_API_URL=http://localhost:11434
  MAX_CALLS_PER_DAY=100
  MAX_SMS_PER_DAY=100
  ```
2. Twilio Webhooks:
- In your Twilio console, navigate to Phone Numbers > Manage > Active Numbers.
- Set Voice & Fax webhook to your ngrok URL followed by `/voice`, e.g., `https://<ngrok-id>.ngrok-free.app/voice`.
- Set Messaging webhook to your ngrok URL followed by `/sms`, e.g., `https://<ngrok-id>.ngrok-free.app/sms`.
- Ensure the HTTP method is set to `POST`.

## Running the Project

1. Start the FastAPI application:
```
uvicorn main:app --reload
```
2. Start ngrok (in a separate terminal):
```
ngrok http 11434
```
3. Verify Twilio Webhooks:
- Ensure your Twilio console is configured with the ngrok URL, as described in the Configuration section above.

## Usage

- Voice Interaction:
- Call the Twilio number associated with your account.
- The chatbot will answer and ask how it can assist. The response will be processed through the Ollama LLM and returned as speech.

- SMS Interaction:
- Send an SMS to the Twilio number.
- The chatbot will process the message through the Ollama LLM and reply via SMS with the generated response.

## Project Structure
```
Telephony-Ollama/
├── .env                     # Environment variables for sensitive information
├── main.py                  # Main application file for FastAPI, Twilio, and Ollama integration
├── requirements.txt         # Python dependencies
├── utils/
│   ├── logger.py            # Logging configuration
│   └── rate_limiter.py      # Rate limiter for managing API calls
└── README.md                # Project documentation
```
## Troubleshooting

- **ngrok Tunnel Not Found**: If you receive a "Tunnel not found" error, restart ngrok and update the Twilio webhook URLs with the new ngrok URL.
- **403 Forbidden Error on SMS/Voice**: Ensure the `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are correct, and that the Twilio account is set to allow the destination number (for trial accounts, only verified numbers can be used).
- **Ollama API 404 Error**: Check that the Ollama API URL is correct and that the server is running. Use `http://localhost:11434` if Ollama is hosted locally.
- **Rate Limit Issues**: If you hit the rate limit, adjust `MAX_CALLS_PER_DAY` and `MAX_SMS_PER_DAY` in `.env` or update the rate limiter logic as needed.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

