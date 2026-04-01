import httpx
import json
import re
from typing import AsyncGenerator
from fastapi import HTTPException

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "llama3"

    async def generate_chat_stream(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        """
        Streams the LLM response, parses the <thinking> and <answer> tags on the fly,
        and yields JSON chunks for Unity (SSE format).
        """
        
        # 1. Build the sliding window payload
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,  # STREAM ACTIVATED!
            "temperature": 0.7
        }

        # 2. State Machine Variables
        state = "WAITING_FOR_EMOTION"
        buffer = ""

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload, timeout=60.0) as response:
                if response.status_code != 200:
                    # On lit le message d'erreur caché par Ollama
                    error_msg = await response.aread()
                    raise HTTPException(
                        status_code=response.status_code, 
                        detail=f"Erreur Ollama : {error_msg.decode('utf-8')}"
                    )
                
                
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    
                    if "error" in data:
                        print(f"❌ ERREUR OLLAMA : {data['error']}", flush=True)
                        break
                        
                    if data.get("done"):
                        print("✅ Stream terminé.", flush=True)
                        break

                    # On ne récupère QUE le vrai texte, on ignore le "thinking" natif d'Ollama
                    token = data.get("message", {}).get("content", "")
                    
                    if token == "":
                        continue # Si c'est vide (parce qu'il réfléchit en silence), on passe au suivant
                        
                    buffer += token

                    # --- STATE 1: Hide the <thinking> tag ---
                    
                    if "<answer>" in buffer:
                        # Keep only what comes after <answer>
                        buffer = buffer.split("<answer>")[1]

                    # --- STATE 2: Extract the {Emotion} tag ---
                    if state == "WAITING_FOR_EMOTION":
                        # Regex to catch "{Emotion}" even if there are spaces/newlines before
                        match = re.search(r"^\s*\{([a-zA-Z_]+)\}(.*)", buffer, re.DOTALL)
                        
                        if match:
                            emotion = match.group(1)
                            remaining_text = match.group(2)
                            
                            # YIELD 1: Instantly send the emotion to Unity so the animation starts!
                            yield f"data: {json.dumps({'type': 'emotion', 'value': emotion})}\n\n"
                            
                            # If there's already some text generated after the tag, send it
                            if remaining_text.strip():
                                yield f"data: {json.dumps({'type': 'text', 'value': remaining_text})}\n\n"
                                
                            buffer = ""
                            state = "STREAMING_TEXT"
                            
                        # Fallback: if the LLM generates 20 chars without an emotion tag
                        elif len(buffer) > 20 and "{" not in buffer:
                            yield f"data: {json.dumps({'type': 'emotion', 'value': 'Neutre'})}\n\n"
                            yield f"data: {json.dumps({'type': 'text', 'value': buffer})}\n\n"
                            buffer = ""
                            state = "STREAMING_TEXT"

                    # --- STATE 3: Stream the spoken words ---
                    elif state == "STREAMING_TEXT":
                        if "</answer>" in token:
                            # Clean the closing tag and send the final piece
                            clean_token = token.replace("</answer>", "")
                            if clean_token:
                                yield f"data: {json.dumps({'type': 'text', 'value': clean_token})}\n\n"
                            break # End of the LLM's spoken turn
                        else:
                            # YIELD 2: Stream the words one by one as they are generated
                            yield f"data: {json.dumps({'type': 'text', 'value': token})}\n\n"