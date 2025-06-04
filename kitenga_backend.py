from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import json
import os

app = FastAPI()

# CORS so frontend can talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# === 📜 RONGOHIA: SCRIBE ENTRY ===
class ScribeEntry(BaseModel):
    speaker: str
    text: str
    tone: str
    glyph_id: str
    translate: bool = False

@app.post("/scribe")
async def scribe(entry: ScribeEntry):
    entry_id = str(uuid.uuid4())
    entry_dict = entry.dict()
    entry_dict["entry_id"] = entry_id

    try:
        filepath = "scribe_entries.json"
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []

        data.append(entry_dict)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "message": "Entry saved",
            "entry_id": entry_id
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# === 👁️ KITENGA: OCR ===
class OCRPayload(BaseModel):
    image_base64: str

@app.post("/ocr")
async def ocr(payload: OCRPayload):
    return {
        "status": "success",
        "extracted_text": "Tēnei te kōrero i kitea i te whakapakoko."
    }

# === 🌐 TĀWERA: TRANSLATE ===
class TranslatePayload(BaseModel):
    text: str
    target_language: str

@app.post("/translate")
async def translate(payload: TranslatePayload):
    if payload.target_language == "en":
        return {"translated_text": "This is the text found in the image."}
    elif payload.target_language == "mi":
        return {"translated_text": "Tēnei te kōrero i kitea i te whakapakoko."}
    else:
        return {"translated_text": "Unsupported language."}

# === 🔊 WAIRUA: TTS ===
class TTSPayload(BaseModel):
    text: str
    voice: str = "default"

@app.post("/speak")
async def speak(payload: TTSPayload):
    return {"audio_url": f"/fake/path/to/audio/{uuid.uuid4()}.mp3"}
