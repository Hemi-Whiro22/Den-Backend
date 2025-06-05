from fastapi import FastAPI, Request, UploadFile, File, Form  # ← tidy imports
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
import json, base64, os
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or lock to your frontend if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "the-den-faa84-39e2d1939316.json"
openai.api_key = os.getenv("OPENAI_API_KEY")

scribe_entries = []  # 🔥 Patch: prevent NameError in /scribe route

class OCRPayload(BaseModel):
    image_base64: str

@app.post("/ocr")
async def ocr(payload: OCRPayload):
    client = vision.ImageAnnotatorClient()
    image_data = base64.b64decode(payload.image_base64)
    image = vision.Image(content=image_data)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    if not texts:
        return { "status": "success", "extracted_text": "No text found." }

    return {
        "status": "success",
        "extracted_text": texts[0].description
    }


# Translate
class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"

@app.post("/translate")
def translate_text(req: TranslateRequest):
    prompt = f"Translate to {req.target_lang}:\n{req.text}"
    res = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return {"translation": res.choices[0].message.content.strip()}

# TTS
class SpeakRequest(BaseModel):
    text: str

@app.post("/speak")
def speak_text(req: SpeakRequest):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    body = {
        "text": req.text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }
    url = "https://api.elevenlabs.io/v1/text-to-speech/TxGEqnHWrfWFTfGW9XjX"
    response = requests.post(url, headers=headers, json=body)
    with open("backend/speak.mp3", "wb") as f:
        f.write(response.content)
    return {"audio_url": "/static/speak.mp3"}

# Scribe Log
class ScribeEntry(BaseModel):
    speaker: str
    text: str
    tone: str = "neutral"
    glyph_id: str = "glyph-auto"
    translate: bool = False

@app.post("/scribe")
def scribe(entry: ScribeEntry):
    scribe_entries.append(entry.dict())
    with open("backend/scribe_entries.json", "w") as f:
        json.dump(scribe_entries, f, indent=2)
    # Rongo Whisper
    rongo_prompt = f"What does this mean: {entry.text}"   # <<<< FIXED LINE
    res = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": rongo_prompt}]
    )
    whisper = res.choices[0].message.content.strip()
    return {"status": "saved", "rongo": whisper}

@app.post("/gpt-whisper")
async def gpt_whisper(request: Request):
    try:
        data = await request.json()
        whisper = data.get("whisper", "")

        res = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": whisper}
            ]
        )
        reply = res.choices[0].message.content.strip()
        return { "response": reply }

    except Exception as e:
        return JSONResponse(content={ "error": str(e) }, status_code=500)
