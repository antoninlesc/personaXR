import os
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.services.parser.pptx_slide1 import parse_pptx
from app.services.parser.pptx_slide2 import parse_slide2
from app.schemas import PersonaJSON, ChatStreamRequest
from app.services.brain.system_prompt_gen import generate_system_prompt
from app.services.brain.llm_service import OllamaService

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Persona Parser API")

# Autorise le frontend Vite (localhost:5173) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

global_system_prompt = ""  # global variable to hold the current system prompt, can be updated via /load-persona endpoint
llm_service = OllamaService()  # Initialize the Ollama service once

@app.post("/parse")
async def parse(pptx: UploadFile = File(...)):
    # file save
    file_path = os.path.join(UPLOAD_DIR, pptx.filename)
    content = await pptx.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # parsing slide 1 (MVP)
    parsed_s1 = parse_pptx(file_path)
    parsed_s2 = parse_slide2(file_path)

    parsed = {
        "persona": parsed_s1,
        "journey": parsed_s2
    }

    return parsed

@app.post("/submit")
async def submit_payload(payload: dict):
    # saving the final JSON
    out_path = os.path.join(OUTPUT_DIR, "persona_submission.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return {"saved_to": out_path}

@app.post("/load-persona")
async def load_persona(data: PersonaJSON):
    # Generate the System Prompt based on the submitted persona and journey data
    system_prompt = generate_system_prompt(data)

    # Save the system prompt to a file for verification
    # prompt_path = os.path.join(OUTPUT_DIR, "system_prompt.txt")
    # with open(prompt_path, "w", encoding="utf-8") as f:
    #     f.write(system_prompt)

    # Update the global system prompt
    global global_system_prompt
    global_system_prompt = system_prompt

    return {"system_prompt_saved_to": "disabled", "system_prompt": system_prompt}

@app.post("/chat/stream")
async def chat_stream(request: ChatStreamRequest):
    if not global_system_prompt:
        raise HTTPException(status_code=400, detail="Persona not loaded.")

    # Call the service and pass the generator to FastAPI's StreamingResponse
    generator = llm_service.generate_chat_stream(
        system_prompt=global_system_prompt,
        user_message=request.user_message,
        history=[msg.model_dump() for msg in request.history]
    )
    
    # "text/event-stream" is the standard content-type for SSE (Server-Sent Events)
    return StreamingResponse(generator, media_type="text/event-stream")