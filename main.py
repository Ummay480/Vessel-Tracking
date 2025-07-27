import os
from dotenv import load_dotenv
import requests
from twilio.rest import Client
import chainlit as cl
from agents import Agent, Runner, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from datetime import datetime

# Welcome note
print("Welcome to the Vessel Tracking System! This application fetches real-time vessel data from the Maersk API, formats it into a professional message, and sends updates via WhatsApp using Twilio. Enter a vessel ID to get started or use the default ID (MAEU123456789).")

# Load environment variables
load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = "+923249208788"  # Adjusted with country code
RECIPIENT_PHONE = os.getenv("RECIPIENT_PHONE")  # Add recipient number to .env

# Gemini configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Maersk API configuration
MAERSK_CONSUMER_KEY = os.getenv("MAERSK_CONSUMER_KEY")
MAERSK_BEARER_TOKEN = os.getenv("MAERSK_BEARER_TOKEN")
MAERSK_API_URL = "https://api.maersk.com/track/v2"

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize Gemini client
client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url=BASE_URL)
model = OpenAIChatCompletionsModel(model=MODEL, openai_client=client)

# Function to fetch vessel data from Maersk API
def fetch_vessel_data(vessel_id="MAEU123456789"):  # Replace with actual vessel ID
    headers = {
        "Consumer-Key": MAERSK_CONSUMER_KEY,
        "Authorization": f"Bearer {MAERSK_BEARER_TOKEN}"
    }
    try:
        response = requests.get(f"{MAERSK_API_URL}/shipment/{vessel_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        # Extract relevant fields (adjust based on actual API response structure)
        return {
            "vessel_name": data.get("vessel_name", "Unknown Vessel"),
            "location": data.get("current_location", "Unknown Location"),
            "status": data.get("status", "Unknown Status"),
            "eta": data.get("eta", "Unknown ETA"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except requests.RequestException as e:
        return {"error": f"Failed to fetch data: {str(e)}"}

# Define agent to format vessel update message
vessel_formatter = Agent(
    name="vessel_formatter",
    instructions="""Format the provided vessel data into a concise, professional WhatsApp message. 
    Include vessel name, location, status, ETA, and last updated time. Example:
    'Vessel Update: SS Horizon is docked at Port of Singapore. ETA: 2025-07-28 14:00. Last updated: 2025-07-27 07:32:00'""",
    model=model
)

# Define agent to send WhatsApp message
whatsapp_sender = Agent(
    name="whatsapp_sender",
    instructions="""Send the formatted vessel update via WhatsApp using the Twilio client to the recipient's phone number.""",
    model=model
)

# Define main vessel update agent
vessel_update_agent = Agent(
    name="vessel_update_agent",
    instructions="""Fetch vessel data, pass it to the vessel_formatter agent to format the message, 
    then hand off to the whatsapp_sender agent to send the message via WhatsApp.""",
    model=model,
    handoffs=[vessel_formatter, whatsapp_sender]
)

# Function to send WhatsApp message using Twilio
async def send_whatsapp_message(formatted_message):
    try:
        message = twilio_client.messages.create(
            body=formatted_message,
            from_=f"whatsapp:{TWILIO_PHONE_NUMBER}",
            to=f"whatsapp:{RECIPIENT_PHONE}"
        )
        return f"Message sent successfully: {message.sid}"
    except Exception as e:
        return f"Failed to send message: {str(e)}"

# Chainlit callback to handle user input
@cl.on_message
async def handle_message(message: cl.Message):
    # Fetch vessel data (use default vessel_id or extract from user input if provided)
    vessel_id = message.content.strip() if message.content.strip() else "MAEU123456789"
    vessel_data = fetch_vessel_data(vessel_id)
    
    if "error" in vessel_data:
        await cl.Message(content=vessel_data["error"]).send()
        return
    
    # Create input for the agent with vessel data
    agent_input = f"""Process the following vessel data and send a WhatsApp update:
    Vessel Name: {vessel_data['vessel_name']}
    Location: {vessel_data['location']}
    Status: {vessel_data['status']}
    ETA: {vessel_data['eta']}
    Last Updated: {vessel_data['last_updated']}"""
    
    # Run the agent pipeline
    result = await Runner.run(starting_agent=vessel_update_agent, input=agent_input)
    
    # Send the formatted message via WhatsApp
    send_result = await send_whatsapp_message(result.final_output)
    
    # Send response back to Chainlit
    
    await cl.Message(content=f"{result.final_output}\n{send_result}").send()