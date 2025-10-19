import os
import uuid
import asyncio
import tempfile
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.responses import FileResponse
import edge_tts

app = FastAPI()

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

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

    background_tasks.add_task(cleanup_file, output_path)

    return FileResponse(
        path=output_path,
        media_type="audio/mpeg",
        filename="speech.mp3"
    )