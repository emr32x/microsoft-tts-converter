import os
import uuid
import asyncio
import tempfile
import json
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates # <--- Nuevo

app = FastAPI()

# --- Configuración de Plantillas y CORS ---
templates = Jinja2Templates(directory="templates")
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Cargar traducciones ---
def load_translations(lang: str):
    path = f"locales/{lang}.json"
    if not os.path.exists(path):
        path = "locales/en.json" # Fallback a inglés
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- NUEVO ENDPOINT: Sirve la página web ---
@app.get("/")
async def read_root(request: Request):
    # Detectar el idioma del navegador
    accept_language = request.headers.get("accept-language", "en")
    lang = accept_language.split(",")[0].split("-")[0]
    
    # Seleccionar idioma soportado
    if lang not in ["es", "en", "pt"]:
        lang = "en"
        
    translations = load_translations(lang)
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "translations": translations, "lang": lang}
    )

# --- Tus Endpoints de API existentes ---
@app.get("/voices/")
async def get_voices():
    try:
        voices = await edge_tts.list_voices()
        return sorted(voices, key=lambda v: v['Locale'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    )

def cleanup_file(path: str): # La función de limpieza que usábamos
    if os.path.exists(path):
        os.remove(path)
