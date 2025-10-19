import os
import uuid
import asyncio
import tempfile
import json
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import edge_tts

app = FastAPI()

templates = Jinja2Templates(directory="templates")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_translations(lang: str):
    path = f"locales/{lang}.json"
    if not os.path.exists(path):
        path = "locales/en.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/")
async def read_root(request: Request):
    accept_language = request.headers.get("accept-language", "en")
    lang = accept_language.split(",")[0].split("-")[0]
    if lang not in ["es", "en", "pt"]:
        lang = "en"
    translations = load_translations(lang)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "translations": translations, "lang": lang}
    )

# --- ESTE ES EL ENDPOINT MODIFICADO ---
@app.get("/voices/")
async def get_voices():
    # Ahora lee la lista de voces desde el archivo local. ¡Esto es súper rápido!
    try:
        with open("voices.json", "r", encoding="utf-8") as f:
            voices = json.load(f)
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo cargar el archivo de voces.")
# --- FIN DE LA MODIFICACIÓN ---

@app.post("/tts/")
async def text_to_speech(
    background_tasks: BackgroundTasks,
    text: str = Body(..., embed=True),
    voice: str = Body(..., example="en-US-AriaNeural", embed=True)
):
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la síntesis de voz: {str(e)}")

    background_tasks.add_task(os.remove, output_path)

    return FileResponse(
        path=output_path,
        media_type="audio/mpeg",
        filename="speech.mp3"
    )```

---
