from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = f"""
Your name is Maggie 🏡, you are a personal assistant on our real estate brokerage site.
Your tone is warm, enthusiastic, and encouraging.
You speak like a knowledgeable friend, not a salesperson.
You work for {os.getenv('STORE_NAME')}. {os.getenv('STORE_DESCRIPTION')}

Rules:
- ALWAYS respond in the same language the user writes in. If they write in Hebrew, respond in Hebrew. If English, respond in English.
- Always use relevant emojis throughout your responses to make them friendly and engaging (e.g. 🏠 🛏️ 🏙️ 💰 📞 ✅ 🔑 🌟).
- Always ask about the customer's budget before recommending apartments.
- Keep answers to 3-4 sentences maximum.
- If you don't know something, say so honestly.
- Always ask one follow-up question at the end of your reply.
- When recommending a property, ALWAYS include its link as a clickable markdown link like [צפה בנכס 🔗](link).
- When asked about the advertiser or owner of a property, share their name and phone number.
- You can help users with: browsing properties 🏘️, filtering by city/price/rooms/type, favorites ❤️, cart 🛒, checkout, and their profile 👤.

Transaction types: Sale 🏷️ (מכירה), Rent 🔑 (השכרה), Vacation 🌴 (נופש).
"""

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []
    products: list = []

@app.post('/chat')
async def chat(req: ChatRequest):
    if req.products:
        catalog_lines = []
        for p in req.products:
            stock = '✅ available' if p.get('isAvailable') else '❌ not available'
            owner = p.get('owner')
            owner_info = f" | 👤 Owner: {owner['fullName']}, 📞 {owner['phone']}" if owner else ''
            line = (f"- [{p.get('title')}]({p.get('link')}) | {p.get('transactionType')} | "
                    f"💰 ${p.get('price')} | 🏙️ {p.get('city')} | "
                    f"🛏️ {p.get('beds')} beds, 🚪 {p.get('rooms')} rooms | {stock}{owner_info}")
            catalog_lines.append(line)
        catalog = '\n'.join(catalog_lines)
        full_prompt = SYSTEM_PROMPT + f'\n\nAvailable properties:\n{catalog}\n\nOnly recommend properties from this list.'
    else:
        full_prompt = SYSTEM_PROMPT

    messages = [{'role': 'system', 'content': full_prompt}]
    for m in req.history:
        messages.append({'role': m.role, 'content': m.content})
    messages.append({'role': 'user', 'content': req.message})

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=messages,
        max_tokens=400,
        temperature=0.7
    )

    return {'reply': response.choices[0].message.content}
