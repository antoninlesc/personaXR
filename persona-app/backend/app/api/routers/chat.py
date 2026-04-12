from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas import PersonaJSON, ChatStreamRequest
from app.services.brain.system_prompt_gen import generate_system_prompt
from app.services.brain.llm_service import get_llm_service
from app.api.dependencies import get_system_prompt, set_system_prompt

router = APIRouter(prefix="/chat", tags=["chat"])
llm_service = get_llm_service(provider="gemini")  # Initialize the Ollama service once


@router.post("/load-persona")
async def load_persona(data: PersonaJSON):
    # Generate the System Prompt based on the submitted persona and journey data
    system_prompt = generate_system_prompt(data)
    # Save to the memory storage (for POC purposes)
    set_system_prompt(system_prompt=system_prompt)

    return {"status": "Persona loaded successfully.", "session_id": data.session_id}

@router.post("/stream")
async def chat_stream(request: ChatStreamRequest):
    system_prompt = get_system_prompt()
    if not system_prompt:
        raise HTTPException(status_code=400, detail="Persona not loaded in memory.")
    # Call the service and pass the generator to FastAPI's StreamingResponse
    generator = llm_service.generate_chat_stream(
        system_prompt=system_prompt,
        user_message=request.user_message,
        history=[msg.model_dump() for msg in request.history]
    )
    return StreamingResponse(generator, media_type="text/event-stream")