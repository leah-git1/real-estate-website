from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# ── Existing chat prompt ──────────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = f"""
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

# ── Voice search extraction prompt ───────────────────────────────────────────

SEARCH_SYSTEM_PROMPT = """
You are a real estate search parameter extractor.
The user will send a search query in Hebrew or English (voice-to-text).
Your job is to extract the search intent and return ONLY a valid JSON object — no markdown, no explanation, no extra text.

Return exactly this structure (use null for any field not mentioned):
{
  "city":        <string | null>,
  "rooms":       <integer | null>,
  "max_price":   <number | null>,
  "has_balcony": <true | false | null>,
  "has_parking": <true | false | null>
}

Rules:
- Prices are in ILS. Convert spoken amounts: "מיליון" / "million" → multiply by 1,000,000. "אלף" / "thousand" → multiply by 1,000.
- If a feature (balcony / מרפסת, parking / חניה) is explicitly mentioned as desired → true.
- If a feature is explicitly excluded → false.
- If a feature is not mentioned at all → null.
- City names: map Hebrew city names to their English equivalents (e.g. "תל אביב" → "Tel Aviv", "ירושלים" → "Jerusalem", "חיפה" → "Haifa").
- Respond with the raw JSON object only.
"""

# ── Models ────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []
    products: list = []

class ParseSearchRequest(BaseModel):
    transcript: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

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
        full_prompt = CHAT_SYSTEM_PROMPT + f'\n\nAvailable properties:\n{catalog}\n\nOnly recommend properties from this list.'
    else:
        full_prompt = CHAT_SYSTEM_PROMPT

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


@app.post('/parse-search')
async def parse_search(req: ParseSearchRequest):
    if not req.transcript or not req.transcript.strip():
        raise HTTPException(status_code=400, detail='transcript is required')

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': SEARCH_SYSTEM_PROMPT},
            {'role': 'user',   'content': req.transcript}
        ],
        temperature=0,
        max_tokens=256,
        response_format={'type': 'json_object'}
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f'LLM returned invalid JSON: {raw}')

    # Guarantee all expected keys are present
    result = {
        'city':        parsed.get('city'),
        'rooms':       parsed.get('rooms'),
        'max_price':   parsed.get('max_price'),
        'has_balcony': parsed.get('has_balcony'),
        'has_parking': parsed.get('has_parking'),
    }
    return result
