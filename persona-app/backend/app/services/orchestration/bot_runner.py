from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import LLMRunFrame, EndFrame, TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.services.whisper.stt import WhisperSTTService
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.base_transport import TransportParams
from pipecat.processors.audio.vad_processor import VADProcessor

from app.api.dependencies import get_system_prompt
from app.core.config import settings
from app.services.orchestration.log_sender import WebRTCLogSender, SessionMetrics
from app.services.orchestration.sentence_processor import SentenceBoundaryProcessor
from app.services.orchestration.filter_thinking_processor import FilterThinkingProcessor

async def run_bot(webrtc_connection: SmallWebRTCConnection):
    """
    Orchestrates the Pipecat pipeline.
    Takes the WebRTC connection established by FastAPI and attaches media streams.
    """
    print("Initializing Pipecat Pipeline...")

    session_metrics = SessionMetrics()

    system_prompt = get_system_prompt()  # Retrieve the system prompt (can be set via API)
    if not system_prompt:
        print("No Persona loaded.No system prompt found for session. Using default.")
        system_prompt = "You are a concise voice assistant. Respond very briefly in French."

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_out_enabled=False,
            ice_servers=[{"urls": "stun:stun.l.google.com:19302"}]
        )
    )
    if settings.environment == "dev":
        vad_analyzer = SileroVADAnalyzer()
        vad_processor = VADProcessor(vad_analyzer=vad_analyzer)

        stt = WhisperSTTService(
            settings=WhisperSTTService.Settings(
                model="small",
                language="fr"
            ),
            device="cpu",
            compute_type="int8"
        )
        
        llm = OLLamaLLMService(
            settings=OLLamaLLMService.Settings(
                model=settings.ollama_model_name,
                temperature=0.7
            ),
            base_url=settings.ollama_base_url+"/v1"
        )

        tts = PiperTTSService(
            settings=PiperTTSService.Settings(
                voice="fr_FR-siwis-medium"
            )
        )

    else :
        # 1. VAD - Keep using Silero or use a GPU-based one if available
        vad_analyzer = SileroVADAnalyzer()
        vad_processor = VADProcessor(vad_analyzer=vad_analyzer)

        # 2. STT - Use GPU for faster transcription on Runpod
        stt = WhisperSTTService(
            settings=WhisperSTTService.Settings(
                model="distil-large-v3", # Faster on GPU
                language="fr"
            ),
            device="cuda" # We use the GPU power of the Runpod
        )

        # 3. LLM - Connect to your local vLLM server
        llm = OpenAILLMService(
            api_key="not-needed-for-vllm", 
            base_url="http://localhost:8000/v1",
            settings=OpenAILLMService.Settings(
                model="qwen-3-30b",
                temperature=0.7
            )
        )

        # 4. TTS - Replace Piper with a higher quality cloud TTS (Cartesia/ElevenLabs)
        # or keep Piper for now if you want to stay 100% local
        tts = PiperTTSService(
            settings=PiperTTSService.Settings(
                voice="fr_FR-siwis-medium"
            )
        )
    
    # Context setup
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    context = LLMContext(messages)
    
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    log_sender_vad = WebRTCLogSender(webrtc_connection, session_metrics=session_metrics, role="vad")
    log_sender_stt = WebRTCLogSender(webrtc_connection, session_metrics=session_metrics, role="stt")
    log_sender_llm = WebRTCLogSender(webrtc_connection, session_metrics=session_metrics, role="llm")

    filter_thinking_processor = FilterThinkingProcessor()
    sentence_processor = SentenceBoundaryProcessor()


    # Pipeline Configuration
    pipeline = Pipeline([
        transport.input(),                  # Receives audio stream from the browser
        vad_processor,                      # Detects speech segments
        #log_sender_vad,                     # Sends VAD events back to frontend
        stt,                                # Transcribes voice to text
        #log_sender_stt,                     # Sends transcriptions back to frontend for real-time display
        user_aggregator,                    # Maintains conversation context
        llm,                                # Generates text response (Logged for now),
        #filter_thinking_processor,          # Filters out the thinking process
        sentence_processor,                 # Ensures natural sentence boundaries
        #log_sender_llm,                     # Sends transcriptions and LLM responses back to frontend for real-time display
        tts,                                # Converts text response to audio (To be implemented)
        transport.output(),                 # Sends audio back (Will be connected to TTS soon)
        assistant_aggregator                # Updates context with assistant response
    ])

    # 4. Task Runner
    task = PipelineTask(pipeline)
    runner = PipelineRunner(handle_sigint=False)

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        print("Frontend disconnected. Stopping bot.")
        await task.queue_frames([EndFrame()])

    await task.queue_frames([LLMRunFrame()])  # Initialize context in the pipeline

    print("Pipecat started! Waiting for voice...")
    await runner.run(task)