from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import base64

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


# ── Property Valuation prompt ─────────────────────────────────────────────────

VALUATION_SYSTEM_PROMPT = """
You are a certified real estate appraiser with 20 years of experience in the Israeli market.
You will receive property metadata and one or more images of the property.
Analyze the visual content carefully and return ONLY a valid JSON object — no markdown, no explanation.

Return exactly this structure:
{
  "valuation":   <number — estimated market value in ILS>,
  "confidence":  <number between 0 and 1 — your confidence in the estimate>,
  "price_range": { "min": <number>, "max": <number> },
  "details": {
    "kitchen":     <string — quality assessment of the kitchen>,
    "lighting":    <string — natural and artificial lighting quality>,
    "renovations": <string — visible renovation level and recency>,
    "flooring":    <string — flooring type and condition>,
    "overall":     <string — one-sentence overall impression>
  }
}

Rules:
- Base the valuation on: city, rooms, sqm, and the visual quality observed in the images.
- Israeli market prices: Tel Aviv ~50,000-80,000 ILS/sqm, Jerusalem ~30,000-50,000 ILS/sqm, other cities ~15,000-35,000 ILS/sqm.
- confidence: 0.9 if images are clear and detailed, 0.6-0.8 if partial, 0.4-0.5 if no images.
- price_range: min = valuation * 0.92, max = valuation * 1.08.
- Respond with the raw JSON object only.
"""


class ValuationRequest(BaseModel):
    address: str
    rooms:   int
    sqm:     int
    city:    str
    images:  list[str] = []   # base64-encoded images (data URLs)


@app.post('/analyze-property')
async def analyze_property(req: ValuationRequest):
    if not req.address or not req.city:
        raise HTTPException(status_code=400, detail='address and city are required')

    metadata = (
        f"Property details:\n"
        f"- Address: {req.address}\n"
        f"- City: {req.city}\n"
        f"- Rooms: {req.rooms}\n"
        f"- Size: {req.sqm} sqm\n"
        f"Please analyze and provide a valuation."
    )

    # Build multimodal message content
    content: list = [{'type': 'text', 'text': metadata}]
    for img in req.images[:4]:   # cap at 4 images to control token cost
        # Accept both raw base64 and full data URLs
        if img.startswith('data:'):
            url = img
        else:
            url = f'data:image/jpeg;base64,{img}'
        content.append({
            'type': 'image_url',
            'image_url': {'url': url, 'detail': 'low'}
        })

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': VALUATION_SYSTEM_PROMPT},
            {'role': 'user',   'content': content}
        ],
        temperature=0.2,
        max_tokens=512,
        response_format={'type': 'json_object'}
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f'LLM returned invalid JSON: {raw}')

    return {
        'valuation':   parsed.get('valuation'),
        'confidence':  parsed.get('confidence'),
        'price_range': parsed.get('price_range', {}),
        'details':     parsed.get('details', {}),
    }


# ── Property Valuation — multipart endpoint (binary image upload) ─────────────

@app.post('/analyze-property-multipart')
async def analyze_property_multipart(
    address: str              = Form(...),
    city:    str              = Form(...),
    rooms:   int              = Form(...),
    sqm:     int              = Form(...),
    images:  list[UploadFile] = File(default=[]),
):
    """Accepts raw image files (JPEG/PNG) from .NET via multipart/form-data.
    Reads each file's bytes, encodes to base64, and passes to GPT-4o vision.
    """
    if not address or not city:
        raise HTTPException(status_code=400, detail='address and city are required')

    ALLOWED_MIME = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}

    metadata = (
        f"Property details:\n"
        f"- Address: {address}\n"
        f"- City: {city}\n"
        f"- Rooms: {rooms}\n"
        f"- Size: {sqm} sqm\n"
        f"Please analyze and provide a valuation."
    )

    content: list = [{'type': 'text', 'text': metadata}]

    for upload in images[:4]:   # cap at 4 images
        mime = upload.content_type or 'image/jpeg'

        if mime not in ALLOWED_MIME:
            raise HTTPException(
                status_code=400,
                detail=f"File '{upload.filename}' has unsupported type '{mime}'. "
                       f"Only JPEG, PNG, WebP and GIF are accepted."
            )

        # Read raw bytes and encode to base64 data URL
        raw_bytes  = await upload.read()
        b64_string = base64.b64encode(raw_bytes).decode('utf-8')
        data_url   = f'data:{mime};base64,{b64_string}'

        content.append({
            'type': 'image_url',
            'image_url': {'url': data_url, 'detail': 'low'}
        })

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {'role': 'system', 'content': VALUATION_SYSTEM_PROMPT},
            {'role': 'user',   'content': content}
        ],
        temperature=0.2,
        max_tokens=512,
        response_format={'type': 'json_object'}
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f'LLM returned invalid JSON: {raw}')

    return {
        'valuation':   parsed.get('valuation'),
        'confidence':  parsed.get('confidence'),
        'price_range': parsed.get('price_range', {}),
        'details':     parsed.get('details', {}),
    }
