import os
import uuid
import asyncio
import tempfile
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts

app = FastAPI()

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

def get_html(translations, lang):
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <title>{translations["title"]}</title>
    <style>
        body {{ font-family: sans-serif; max-width: 600px; margin: auto; padding: 2em; }}
        textarea, select {{ width: 100%; margin-bottom: 1em; padding: 0.5em; font-size: 1em; }}
        textarea {{ height: 100px; }}
        button {{ padding: 0.5em 1em; font-size: 1em; cursor: pointer; }}
        #mensaje {{ color: blue; font-weight: bold; }}
        .telegram-btn {{ display: block; width: 100%; box-sizing: border-box; text-align: center; margin-top: 2em; padding: 0.75em 1em; background-color: #0088cc; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        .telegram-btn:hover {{ background-color: #0077b3; }}
    </style>
</head>
<body>
    <h1>{translations["title"]}</h1>
    <label for="texto">{translations["text_label"]}</label>
    <textarea id="texto" placeholder="Escribe el texto aquí..."></textarea>
    <label for="voz">{translations["voice_label"]}</label>
    <select id="voz"><option value="">{translations["loading_voices"]}</option></select>
    <button id="convertirBtn">{translations["button_text"]}</button>
    <p id="mensaje"></p>
    <a href="https://t.me/gema23_32" target="_blank" class="telegram-btn">{translations["telegram_button"]}</a>
    <script>
        const vozSelect = document.getElementById('voz');
        const mensaje = document.getElementById('mensaje');
        const translations = {json.dumps(translations)};

        document.addEventListener('DOMContentLoaded', async () => {{
            try {{
                const response = await fetch('/voices/');
                if (!response.ok) throw new Error(translations.error_loading_voices);
                const voices = await response.json();
                vozSelect.innerHTML = '';
                voices.forEach(voice => {{
                    const option = document.createElement('option');
                    option.value = voice.ShortName;
                    const displayName = voice.FriendlyName || voice.DisplayName || voice.ShortName;
                    option.textContent = displayName + ' (' + voice.Gender + ', ' + voice.Locale + ')';
                    if (voice.ShortName === 'es-MX-JorgeNeural') option.selected = true;
                    vozSelect.appendChild(option);
                }});
            }} catch (error) {{
                vozSelect.innerHTML = '<option value=\\'\\'>' + translations.error_loading_voices + '</option>';
                mensaje.textContent = 'Error: ' + error.message;
            }}
        }});

        document.getElementById('convertirBtn').addEventListener('click', async () => {{
            const texto = document.getElementById('texto').value;
            const voz = vozSelect.value;
            mensaje.textContent = translations.generating_audio;
            try {{
                const response = await fetch('/tts/', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ text: texto, voice: voz }})
                }});
                if (!response.ok) throw new Error(translations.error_generating_audio);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'audio_generado.mp3';
                a.click();
                window.URL.revokeObjectURL(url);
                mensaje.textContent = translations.downloaded_audio;
            }} catch (error) {{
                mensaje.textContent = 'Error: ' + error.message;
            }}
        }});
    </script>
</body>
</html>'''

@app.get("/")
async def read_root(request: Request):
    accept_language = request.headers.get("accept-language", "en")
    lang = accept_language.split(",")[0].split("-")[0]
    
    if lang not in ["es", "en", "pt"]:
        lang = "en"
        
    translations = load_translations(lang)
    
    return HTMLResponse(get_html(translations, lang))

@app.get("/voices/")
async def get_voices():
    try:
        with open("voices.json", "r", encoding="utf-8") as f:
            voices = json.load(f)
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail="No se pudo cargar el archivo de voces.")

@app.post("/tts/")
async def text_to_speech(request: Request):
    try:
        body = await request.json()
        text = body.get("text", "")
        voice = body.get("voice", "")
        
        if not text or not voice:
            raise HTTPException(status_code=400, detail="Faltan parámetros text o voice")
        
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
