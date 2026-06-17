"""
Tests for chat_service.py — covers /chat, /parse-search, /analyze-property, /analyze-property-multipart
Run with:  pytest test_chat_service.py -v
"""
import io
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# ── Import the app ────────────────────────────────────────────────────────────
from chat_service import app

client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_completion(content: str):
    """Build a minimal mock that looks like an openai ChatCompletion response."""
    msg  = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


# ══════════════════════════════════════════════════════════════════════════════
# /chat
# ══════════════════════════════════════════════════════════════════════════════

class TestChat:

    @patch("chat_service.client")
    def test_basic_message_returns_reply(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("שלום! 👋 איך אוכל לעזור?")

        res = client.post("/chat", json={"message": "שלום", "history": [], "products": []})

        assert res.status_code == 200
        assert "reply" in res.json()
        assert res.json()["reply"] == "שלום! 👋 איך אוכל לעזור?"

    @patch("chat_service.client")
    def test_message_with_product_catalog(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("Found a great apartment!")

        products = [
            {
                "title": "דירה בתל אביב",
                "link": "http://localhost:4200/product-details/1",
                "transactionType": "Sale",
                "price": 2500000,
                "city": "Tel Aviv",
                "beds": 2,
                "rooms": 4,
                "isAvailable": True,
                "owner": {"fullName": "ישראל ישראלי", "phone": "050-0000000"},
            }
        ]

        res = client.post("/chat", json={"message": "show me apartments", "history": [], "products": products})

        assert res.status_code == 200
        assert "reply" in res.json()
        # Verify catalog was included in the prompt sent to OpenAI
        call_args = mock_openai.chat.completions.create.call_args
        messages  = call_args.kwargs.get("messages") or call_args.args[0]
        system_msg = next(m for m in messages if m["role"] == "system")
        assert "דירה בתל אביב" in system_msg["content"]

    @patch("chat_service.client")
    def test_message_with_history(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("Sure, here are options in Jerusalem.")

        history = [
            {"role": "user",      "content": "I want an apartment"},
            {"role": "assistant", "content": "Which city?"},
        ]

        res = client.post("/chat", json={"message": "Jerusalem", "history": history, "products": []})

        assert res.status_code == 200
        call_args = mock_openai.chat.completions.create.call_args
        messages  = call_args.kwargs.get("messages") or call_args.args[0]
        roles = [m["role"] for m in messages]
        assert "user" in roles
        assert "assistant" in roles

    @patch("chat_service.client")
    def test_empty_message_still_calls_openai(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("...")
        res = client.post("/chat", json={"message": "", "history": [], "products": []})
        assert res.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# /parse-search
# ══════════════════════════════════════════════════════════════════════════════

class TestParseSearch:

    @patch("chat_service.client")
    def test_hebrew_query_full_params(self, mock_openai):
        payload = {"city": "Tel Aviv", "rooms": 4, "max_price": 2500000, "has_balcony": True, "has_parking": None}
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(payload))

        res = client.post("/parse-search", json={"transcript": "אני מחפש דירה ב-4 חדרים עם מרפסת בתל אביב עד 2.5 מיליון"})

        assert res.status_code == 200
        data = res.json()
        assert data["city"]        == "Tel Aviv"
        assert data["rooms"]       == 4
        assert data["max_price"]   == 2500000
        assert data["has_balcony"] is True
        assert data["has_parking"] is None

    @patch("chat_service.client")
    def test_english_query_partial_params(self, mock_openai):
        payload = {"city": "Jerusalem", "rooms": None, "max_price": 1000000, "has_balcony": None, "has_parking": None}
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(payload))

        res = client.post("/parse-search", json={"transcript": "apartment in Jerusalem up to 1 million"})

        assert res.status_code == 200
        data = res.json()
        assert data["city"]      == "Jerusalem"
        assert data["max_price"] == 1000000
        assert data["rooms"]     is None

    @patch("chat_service.client")
    def test_all_null_when_no_params_given(self, mock_openai):
        payload = {"city": None, "rooms": None, "max_price": None, "has_balcony": None, "has_parking": None}
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(payload))

        res = client.post("/parse-search", json={"transcript": "show me something nice"})

        assert res.status_code == 200
        data = res.json()
        for v in data.values():
            assert v is None

    def test_empty_transcript_returns_400(self):
        res = client.post("/parse-search", json={"transcript": ""})
        assert res.status_code == 400

    def test_whitespace_transcript_returns_400(self):
        res = client.post("/parse-search", json={"transcript": "   "})
        assert res.status_code == 400

    @patch("chat_service.client")
    def test_invalid_json_from_llm_returns_500(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("not valid json at all")

        res = client.post("/parse-search", json={"transcript": "דירה בחיפה"})
        assert res.status_code == 500

    @patch("chat_service.client")
    def test_parking_excluded(self, mock_openai):
        payload = {"city": None, "rooms": 3, "max_price": None, "has_balcony": None, "has_parking": False}
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(payload))

        res = client.post("/parse-search", json={"transcript": "3 room apartment without parking"})
        assert res.status_code == 200
        assert res.json()["has_parking"] is False


# ══════════════════════════════════════════════════════════════════════════════
# /analyze-property  (JSON base64 endpoint)
# ══════════════════════════════════════════════════════════════════════════════

MOCK_VALUATION = {
    "valuation":   3500000,
    "confidence":  0.82,
    "price_range": {"min": 3220000, "max": 3780000},
    "details": {
        "kitchen":     "Modern, renovated",
        "lighting":    "Excellent natural light",
        "renovations": "Fully renovated within last 5 years",
        "flooring":    "Porcelain tiles in good condition",
        "overall":     "Well-maintained apartment in a desirable location",
    }
}


class TestAnalyzeProperty:

    @patch("chat_service.client")
    def test_basic_valuation_no_images(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(MOCK_VALUATION))

        res = client.post("/analyze-property", json={
            "address": "רחוב הרצל 12", "city": "Tel Aviv", "rooms": 4, "sqm": 90, "images": []
        })

        assert res.status_code == 200
        data = res.json()
        assert data["valuation"]   == 3500000
        assert data["confidence"]  == 0.82
        assert "min" in data["price_range"]
        assert "kitchen" in data["details"]

    @patch("chat_service.client")
    def test_valuation_with_base64_image(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(MOCK_VALUATION))

        # Minimal 1×1 white JPEG in base64
        tiny_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAAR" \
                   "CAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AJQAB/9k="

        res = client.post("/analyze-property", json={
            "address": "Dizengoff 50", "city": "Tel Aviv", "rooms": 3, "sqm": 75,
            "images": [tiny_b64]
        })

        assert res.status_code == 200
        # Image should have been passed to OpenAI as image_url content
        call_args = mock_openai.chat.completions.create.call_args
        messages  = call_args.kwargs.get("messages") or call_args.args[0]
        user_content = messages[-1]["content"]
        image_parts = [p for p in user_content if p.get("type") == "image_url"]
        assert len(image_parts) == 1

    @patch("chat_service.client")
    def test_images_capped_at_4(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(MOCK_VALUATION))

        dummy = "data:image/jpeg;base64,abc123"
        res = client.post("/analyze-property", json={
            "address": "Test St 1", "city": "Haifa", "rooms": 2, "sqm": 60,
            "images": [dummy] * 7   # send 7, expect only 4 used
        })

        assert res.status_code == 200
        call_args = mock_openai.chat.completions.create.call_args
        messages  = call_args.kwargs.get("messages") or call_args.args[0]
        user_content = messages[-1]["content"]
        image_parts = [p for p in user_content if p.get("type") == "image_url"]
        assert len(image_parts) == 4

    def test_missing_address_returns_400(self):
        res = client.post("/analyze-property", json={
            "address": "", "city": "Tel Aviv", "rooms": 3, "sqm": 70, "images": []
        })
        assert res.status_code == 400

    def test_missing_city_returns_400(self):
        res = client.post("/analyze-property", json={
            "address": "Some Street 1", "city": "", "rooms": 3, "sqm": 70, "images": []
        })
        assert res.status_code == 400

    @patch("chat_service.client")
    def test_invalid_json_from_llm_returns_500(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("oops not json")

        res = client.post("/analyze-property", json={
            "address": "Tel Aviv St 1", "city": "Tel Aviv", "rooms": 3, "sqm": 80, "images": []
        })
        assert res.status_code == 500


# ══════════════════════════════════════════════════════════════════════════════
# /analyze-property-multipart  (file upload endpoint)
# ══════════════════════════════════════════════════════════════════════════════

def _make_jpeg_bytes() -> bytes:
    """Return minimal valid JPEG bytes (1×1 white pixel)."""
    return bytes([
        0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,
        0x01,0x00,0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,
        0x00,0x08,0x06,0x06,0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,
        0x09,0x08,0x0A,0x0C,0x14,0x0D,0x0C,0x0B,0x0B,0x0C,0x19,0x12,
        0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,0x1A,0x1C,0x1C,0x20,
        0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,0x37,0x29,
        0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,
        0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,
        0x00,0x01,0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x1F,0x00,0x00,
        0x01,0x05,0x01,0x01,0x01,0x01,0x01,0x01,0x00,0x00,0x00,0x00,
        0x00,0x00,0x00,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,
        0x09,0x0A,0x0B,0xFF,0xC4,0x00,0xB5,0x10,0x00,0x02,0x01,0x03,
        0x03,0x02,0x04,0x03,0x05,0x05,0x04,0x04,0x00,0x00,0x01,0x7D,
        0xFF,0xDA,0x00,0x08,0x01,0x01,0x00,0x00,0x3F,0x00,0xFB,0xD4,
        0xFF,0xD9
    ])


class TestAnalyzePropertyMultipart:

    @patch("chat_service.client")
    def test_no_images_returns_valuation(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(MOCK_VALUATION))

        res = client.post("/analyze-property-multipart", data={
            "address": "Herzl 12", "city": "Tel Aviv", "rooms": "4", "sqm": "90"
        })

        assert res.status_code == 200
        assert res.json()["valuation"] == 3500000

    @patch("chat_service.client")
    def test_with_jpeg_upload(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(MOCK_VALUATION))

        jpeg = _make_jpeg_bytes()
        files = [("images", ("photo.jpg", io.BytesIO(jpeg), "image/jpeg"))]

        res = client.post("/analyze-property-multipart",
                          data={"address": "Allenby 30", "city": "Tel Aviv", "rooms": "3", "sqm": "75"},
                          files=files)

        assert res.status_code == 200
        data = res.json()
        assert "price_range" in data
        assert "details"     in data

    @patch("chat_service.client")
    def test_multiple_images_capped_at_4(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion(json.dumps(MOCK_VALUATION))

        jpeg  = _make_jpeg_bytes()
        files = [("images", (f"photo{i}.jpg", io.BytesIO(jpeg), "image/jpeg")) for i in range(6)]

        res = client.post("/analyze-property-multipart",
                          data={"address": "Test 1", "city": "Haifa", "rooms": "2", "sqm": "60"},
                          files=files)

        assert res.status_code == 200
        call_args = mock_openai.chat.completions.create.call_args
        messages  = call_args.kwargs.get("messages") or call_args.args[0]
        user_content = messages[-1]["content"]
        image_parts  = [p for p in user_content if p.get("type") == "image_url"]
        assert len(image_parts) <= 4

    def test_unsupported_file_type_returns_400(self):
        files = [("images", ("video.mp4", io.BytesIO(b"fake"), "video/mp4"))]
        res   = client.post("/analyze-property-multipart",
                            data={"address": "Test 1", "city": "Tel Aviv", "rooms": "2", "sqm": "60"},
                            files=files)
        assert res.status_code == 400

    def test_missing_address_returns_422(self):
        res = client.post("/analyze-property-multipart",
                          data={"city": "Tel Aviv", "rooms": "3", "sqm": "70"})
        assert res.status_code == 422

    def test_missing_city_returns_422(self):
        res = client.post("/analyze-property-multipart",
                          data={"address": "Test St 1", "rooms": "3", "sqm": "70"})
        assert res.status_code == 422

    @patch("chat_service.client")
    def test_invalid_json_from_llm_returns_500(self, mock_openai):
        mock_openai.chat.completions.create.return_value = _mock_completion("broken json {{")

        res = client.post("/analyze-property-multipart",
                          data={"address": "St 1", "city": "Tel Aviv", "rooms": "3", "sqm": "80"})
        assert res.status_code == 500
