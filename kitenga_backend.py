from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai, os, json

openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_handler(payload: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": payload.message}]
        )
        content = response.choices[0].message.content

        with open("glyph_log.json", "a") as f:
            f.write(json.dumps({"q": payload.message, "a": content}) + "\n")

        return { "response": content }
    except Exception as e:
        return { "response": f"Error: {str(e)}" }

@app.get("/api/glyphs")
async def get_glyphs():
    try:
        with open("glyph_log.json", "r") as f:
            return [json.loads(line) for line in f.readlines()]
    except:
        return []
