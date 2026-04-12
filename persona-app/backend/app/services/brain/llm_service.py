import httpx
import json
import re
import os
import asyncio
import time
from typing import AsyncGenerator, List, Dict
from fastapi import HTTPException
from google import genai
from google.genai import types
from dotenv import load_dotenv
from app.core.config import settings

class BaseLLMService:
    """
    Base class containing the parsing logic.
    Simplified: It expects the LLM to start immediately with {Emotion}.
    """
    async def _parse_and_yield_sse(self, token_generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """
        Takes a stream of raw tokens, extracts the {Emotion} tag instantly,
        and streams the remaining text.
        """
        t0 = time.perf_counter()  # Start timer for debugging
        state = "WAITING_FOR_EMOTION"
        buffer = ""
        full_raw_response = "" # Variable to hold the entire response for debugging

        async for token in token_generator:
            if not token:
                continue

            # --- DEBUG LOGGING ---
            # Accumulate and print the exact raw chunks received from the LLM
            full_raw_response += token
            print(f"[RAW CHUNK] {repr(token)}", flush=True)
            # ---------------------

            if state == "WAITING_FOR_EMOTION":
                buffer += token

                # Regex to extract {Emotion} ANYWHERE in the early buffer (removed the strict ^ start)
                match = re.search(r"\{([a-zA-Z_]+)\}(.*)", buffer, re.DOTALL)
                
                if match:
                    emotion = match.group(1)
                    remaining_text = match.group(2)
                    
                    # Instantly send the emotion to Unity/Frontend
                    yield f"data: {json.dumps({'type': 'emotion', 'value': emotion})}\n\n"
                    
                    # Send any text that came right after the tag
                    if remaining_text.strip():
                        yield f"data: {json.dumps({'type': 'text', 'value': remaining_text})}\n\n"
                        
                    buffer = ""
                    state = "STREAMING_TEXT"
                    
                # Bulletproof fallback: If the LLM generates 40 chars and we STILL don't have a valid tag
                # default to Neutre and start streaming text to prevent UI freezing.
                elif len(buffer) > 40:
                    print(f"\n[WARNING] Fallback triggered! No emotion tag found. Buffer: {repr(buffer)}", flush=True)
                    yield f"data: {json.dumps({'type': 'emotion', 'value': 'Neutre'})}\n\n"
                    yield f"data: {json.dumps({'type': 'text', 'value': buffer})}\n\n"
                    buffer = ""
                    state = "STREAMING_TEXT"

            # --- STATE 2: Stream the spoken words ---
            elif state == "STREAMING_TEXT":
                # Stream the words one by one as they are generated
                yield f"data: {json.dumps({'type': 'text', 'value': token})}\n\n"

        # --- END OF STREAM DEBUG LOGGING ---
        t1 = time.perf_counter()
        print(f"\n[STREAM COMPLETE] Total parser output time: {t1 - t0:.4f} seconds", flush=True)
        print("\n" + "="*50)
        print("FINAL FULL RAW RESPONSE FROM LLM:")
        print(repr(full_raw_response))
        print("="*50 + "\n", flush=True)


    async def generate_chat_stream(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        raise NotImplementedError("Must be implemented by the child class.")


class OllamaService(BaseLLMService):
    """ Service for using a local LLM model via Ollama. """
    def __init__(self, base_url: str = settings.ollama_base_url, model_name: str = "llama3"):
        self.base_url = base_url
        self.model_name = model_name

    async def _token_generator(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "temperature": 0.7
        }

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload, timeout=60.0) as response:
                if response.status_code != 200:
                    error_msg = await response.aread()
                    # Gracefully yield an error instead of crashing the stream
                    print(f"❌ OLLAMA ERROR: {error_msg.decode('utf-8')}", flush=True)
                    yield "{Tristesse} Désolé, mon serveur Ollama local a rencontré une erreur."
                    return # Stop the generator cleanly
                
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    if "error" in data:
                        print(f"❌ OLLAMA ERROR: {data['error']}", flush=True)
                        break
                    if data.get("done"):
                        break

                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token

    async def generate_chat_stream(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        generator = self._token_generator(system_prompt, user_message, history)
        async for chunk in self._parse_and_yield_sse(generator):
            yield chunk


class GeminiService(BaseLLMService):
    """ Service for using the Google Gemini Cloud API via the official SDK. """
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is missing. Please add it to your environment variables.")
        
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    async def _token_generator(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        t_start = time.perf_counter()
        
        contents = []
        for msg in history:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
            )
        
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
        )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        )

        t_setup = time.perf_counter()
        print(f"⏱️ [TIMING] Setup & Payload preparation: {t_setup - t_start:.4f}s", flush=True)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                t_api_call = time.perf_counter()
                
                response_stream = await self.client.aio.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )
                
                t_api_connected = time.perf_counter()
                print(f"⏱️ [TIMING] Request sent, connection established: {t_api_connected - t_api_call:.4f}s", flush=True)
                
                first_token_received = False
                
                async for chunk in response_stream:
                    if chunk.text:
                        # Log the Time To First Token (TTFT)
                        if not first_token_received:
                            t_first_token = time.perf_counter()
                            print(f"⏱️ [TIMING] Time To First Token (TTFT): {t_first_token - t_api_connected:.4f}s (Google Thinking Time)", flush=True)
                            first_token_received = True
                            
                        yield chunk.text
                
                t_done = time.perf_counter()
                print(f"⏱️ [TIMING] Stream finished cleanly. Stream duration: {t_done - t_first_token:.4f}s", flush=True)
                
                # If we reach here, the generation was successful. We can break out of the retry loop.
                break 
                        
            except Exception as e:
                error_str = str(e)
                # Check if the error is related to high demand (HTTP 503)
                if "503" in error_str or "UNAVAILABLE" in error_str or "high demand" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, then 2s
                        print(f"⚠️ [RETRY] Gemini API is overloaded (503). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})", flush=True)
                        await asyncio.sleep(wait_time)
                        continue # Try the loop again
                
                # If we exhausted all retries or hit a different error, handle it gracefully
                print(f"❌ GEMINI SDK ERROR: {error_str}", flush=True)
                
                # INSTEAD OF CRASHING FastAPI, we yield a fake LLM response.
                yield "{Tristesse} Désolé, mon cerveau Google est actuellement surchargé. Veuillez réessayer dans quelques secondes."
                return # Exit the generator cleanly

    async def generate_chat_stream(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        generator = self._token_generator(system_prompt, user_message, history)
        async for chunk in self._parse_and_yield_sse(generator):
            yield chunk

# TODO : Implement the Groq Llama API integration here, following the same pattern as above.
class GroqLlamaService(BaseLLMService):
    """ Placeholder for a future Groq LLM service implementation. """
    async def generate_chat_stream(self, system_prompt: str, user_message: str, history: list) -> AsyncGenerator[str, None]:
        # For now, just yield a dummy response to test the pipeline
        yield "{Tristesse} Désolé, le service Groq n'est pas encore implémenté."

# --- FACTORY ---
def get_llm_service(provider: str = "ollama", **kwargs) -> BaseLLMService:
    if provider.lower() == "gemini":
        return GeminiService(**kwargs)
    elif provider.lower() == "ollama":
        return OllamaService(**kwargs)
    else:
        raise ValueError(f"Provider {provider} is not supported.")