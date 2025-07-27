# generate_message.py
import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def generate_update(vessel_data):
    prompt = (
        "Provide a concise, professional update about vessel arrivals at Karachi port "
        f"based on the following data:\n{vessel_data}\n"
        "Keep it brief and informative."
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a maritime update assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150,
    )
    message = response.choices[0].message['content'].strip()
    return message
