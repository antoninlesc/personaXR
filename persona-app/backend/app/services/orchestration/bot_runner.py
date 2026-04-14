import json

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import LLMRunFrame, EndFrame, TextFrame, TranscriptionFrame, MetricsFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.base_transport import TransportParams
from pipecat.processors.audio.vad_processor import VADProcessor

from app.api.dependencies import get_system_prompt

class WebRTCLogSender(FrameProcessor):
    def __init__(self, connection: SmallWebRTCConnection):
        super().__init__()
        self._connection = connection

    async def process_frame(self, frame, direction):
        # 1. Send Transcriptions (User Speech)
        if isinstance(frame, TranscriptionFrame):
            print(f"[DEBUG STT] Transcribed: {frame.text}") 
            msg = json.dumps({"type": "transcription", "text": frame.text}) # Stringify for JS
            try:
                self._connection.send_app_message(msg)
            except Exception as e:
                print(f"[Error] WebRTC Data Channel STT: {e}")
            
        # 2. Send AI Answers (Text from LLM)
        elif isinstance(frame, TextFrame):
            print(f"[DEBUG LLM] Generated: {frame.text}")
            msg = json.dumps({"type": "llm_response", "text": frame.text})
            try:
                self._connection.send_app_message(msg)
            except Exception as e:
                pass

        # 3. Send Metrics
        elif isinstance(frame, MetricsFrame):
            msg = json.dumps({"type": "metrics", "data": frame.data})
            try:
                self._connection.send_app_message(msg)
            except Exception as e:
                pass

        await self.push_frame(frame, direction)
                
async def run_bot(webrtc_connection: SmallWebRTCConnection):
    """
    Orchestrates the Pipecat pipeline.
    Takes the WebRTC connection established by FastAPI and attaches media streams.
    """
    print("Initializing Pipecat Pipeline...")


    system_prompt = get_system_prompt()  # Retrieve the system prompt (can be set via API)
    if not system_prompt:
        print("No Persona loaded.No system prompt found for session. Using default.")
        system_prompt = "You are a concise voice assistant. Respond very briefly in French."

    vad_analyzer = SileroVADAnalyzer()
    vad_processor = VADProcessor(vad_analyzer=vad_analyzer)

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_out_enabled=False
        )
    )

    # 2. Services (The factory workers)
    # STT: Transcribes voice locally
    stt = WhisperSTTService(
        settings=WhisperSTTService.Settings(
            model="small",
            language="fr"
        ),
        device="cpu",
        compute_type="int8"
    )
    
    # LLM: Using Ollama for local POC (Ensure Ollama is running on port 11434)
    llm = OLLamaLLMService(
        settings=OLLamaLLMService.Settings(
            model="llama3.2:1b",
            temperature=0.7
        ),
        base_url="http://localhost:11434/v1"
    )
    
    # Context setup
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    context = LLMContext(messages)
    
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    log_sender_stt = WebRTCLogSender(webrtc_connection)
    log_sender_llm = WebRTCLogSender(webrtc_connection)
    # 3. Pipeline Configuration
    pipeline = Pipeline([
        transport.input(),                  # Receives audio stream from the browser
        vad_processor,                      # Detects speech segments
        stt,                                # Transcribes voice to text
        log_sender_stt,                     # Sends transcriptions back to frontend for real-time display
        user_aggregator,                    # Maintains conversation context
        llm,                                # Generates text response (Logged for now),
        log_sender_llm,                     # Sends transcriptions and LLM responses back to frontend for real-time display
        # tts,                              # Converts text response to audio (To be implemented)
        transport.output(),                 # Sends audio back (Will be connected to TTS soon)
        assistant_aggregator                # Updates context with assistant response
    ])

    # 4. Task Runner
    task = PipelineTask(pipeline)
    runner = PipelineRunner()

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        print("Frontend disconnected. Stopping bot.")
        await task.queue_frames([EndFrame()])

    await task.queue_frames([LLMRunFrame()])  # Initialize context in the pipeline

    print("Pipecat started! Waiting for voice...")
    await runner.run(task)