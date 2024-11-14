from fastapi import FastAPI, Request, HTTPException
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
import httpx
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from utils.rate_limiter import RateLimiter
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logger()

# Initialize FastAPI application
app = FastAPI(title="Twilio Voice Chatbot")

# Twilio client configuration
try:
    twilio_client = Client(
        os.getenv('TWILIO_ACCOUNT_SID'),
        os.getenv('TWILIO_AUTH_TOKEN')
    )
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
except Exception as e:
    logger.error(f"Twilio initialization error: {e}")
    raise

# Initialize rate limiter
voice_limiter = RateLimiter(int(os.getenv('MAX_CALLS_PER_DAY', 100)))
sms_limiter = RateLimiter(int(os.getenv('MAX_SMS_PER_DAY', 100)))

async def process_with_ollama(user_input: str) -> str:
    """Process user input with Ollama"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{os.getenv('OLLAMA_API_URL')}/generate",
                json={"prompt": user_input},
                timeout=30.0
            )
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'Sorry, I’m unable to understand your input right now.')
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "The system is temporarily unable to process your request, please try again later."
        except Exception as e:
            logger.error(f"Error processing with Ollama: {e}")
            return "Sorry, there was an error processing your request."

@app.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming call"""
    try:
        form_data = await request.form()
        from_number = form_data.get('From')

        # Check rate limit
        if not voice_limiter.can_proceed(from_number):
            response = VoiceResponse()
            response.say("Sorry, you have reached the call limit for today.", language="en")
            response.hangup()
            return str(response)

        response = VoiceResponse()
        gather = Gather(
            input='speech',
            action='/process-speech',
            timeout=3,
            language='en',
            hints=['Hello', 'Help', 'Goodbye']
        )
        gather.say("Welcome to the AI Assistant. How can I help you?", language="en")
        response.append(gather)

        # Redirect to start if the user doesn't speak
        response.redirect('/voice')
        
        return str(response)
    except Exception as e:
        logger.error(f"Error in voice handler: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/process-speech")
async def process_speech(request: Request):
    """Process speech input"""
    try:
        form_data = await request.form()
        user_input = form_data.get('SpeechResult', '')
        
        if not user_input:
            response = VoiceResponse()
            response.say("Sorry, I didn't hear that. Please say it again.", language="en")
            response.redirect('/voice')
            return str(response)

        # Process user input
        llm_response = await process_with_ollama(user_input)
        
        response = VoiceResponse()
        response.say(llm_response, language="en")

        # Continue conversation
        gather = Gather(
            input='speech',
            action='/process-speech',
            timeout=3,
            language='en'
        )
        gather.say("Do you have any other questions?", language="en")
        response.append(gather)
        
        return str(response)
    except Exception as e:
        logger.error(f"Error in speech processor: {e}")
        raise HTTPException(status_code=500, detail="Speech processing error")

@app.post("/sms")
async def handle_sms(request: Request):
    """Handle SMS"""
    try:
        form_data = await request.form()
        message_body = form_data.get('Body', '')
        from_number = form_data.get('From', '')

        # Check rate limit
        if not sms_limiter.can_proceed(from_number):
            return "Sorry, you have reached the SMS limit for today."

        # Process message
        response_text = await process_with_ollama(message_body)
        
        # Send reply
        twilio_client.messages.create(
            body=response_text,
            to=from_number,
            from_=twilio_number
        )
        
        return "Message processed"
    except Exception as e:
        logger.error(f"Error in SMS handler: {e}")
        raise HTTPException(status_code=500, detail="SMS processing error")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Twilio Voice Chatbot")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Twilio Voice Chatbot")
