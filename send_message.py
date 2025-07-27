# send_message.py
from twilio.rest import Client
from config import ACCOUNT_SID, AUTH_TOKEN, FROM_WHATSAPP_NUMBER, TO_WHATSAPP_NUMBER

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(body):
    message = client.messages.create(
        body=body,
        from_=FROM_WHATSAPP_NUMBER,
        to=TO_WHATSAPP_NUMBER
    )
    print(f"Message sent with SID: {message.sid}")
