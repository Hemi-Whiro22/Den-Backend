# FastAPI with OCR, Translate, TTS, and Rongo GPT
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, base64, os
import openai
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "the-den-faa84-39e2d1939316.json"

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
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"Translate to {req.target_lang}:\n{req.text}"
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return {"translation": res['choices'][0]['message']['content'].strip()}
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
    openai.api_key = os.getenv("OPENAI_API_KEY")
    scribe_entries.append(entry.dict())
    with open("backend/scribe_entries.json", "w") as f:
        json.dump(scribe_entries, f, indent=2)
    # Rongo Whisper
    rongo_prompt = f"What does this mean: {entry.text}"   # <<<< FIXED LINE
    # If you want multi-line, use triple quotes:
    # rongo_prompt = f"""What does this mean:\n{entry.text}\n"""
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": rongo_prompt}]
    )
    whisper = res['choices'][0]['message']['content'].strip()
    return {"status": "saved", "rongo": whisper}

@app.post("/gpt-whisper")
async def gpt_whisper(request: Request):
    try:
        data = await request.json()
        user_msg = data.get("message", "")

        prompt = f"""You are Rongo, the guiding spirit of The Den.
Interpret this and respond ONLY as JSON like:
{{ "action": "tts", "input": "translateOutput" }}

Whisper: \"{user_msg}\"
"""

        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{ "role": "user", "content": prompt }]
        )

        parsed = json.loads(res.choices[0].message["content"])
        return JSONResponse(content=parsed)

    except Exception as e:
        return JSONResponse(content={ "error": str(e) }, status_code=500)

