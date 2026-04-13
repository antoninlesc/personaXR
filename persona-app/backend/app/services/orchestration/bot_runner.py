import asyncio
from aiortc import RTCPeerConnection
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import EndFrame
from pipecat.services.whisper import WhisperSTTService
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.base_transport import BaseTransport, TransportParams

from app.api.dependencies import get_system_prompt

class BotRunner:
    async def run_bot(pc: RTCPeerConnection):
        """
        Orchestrates the Pipecat pipeline.
        Takes the WebRTC connection established by FastAPI and attaches media streams.
        """
        print("Initializing Pipecat Pipeline...")


        system_prompt = get_system_prompt()  # Retrieve the system prompt (can be set via API)
        if not system_prompt:
            print("No Persona loaded.No system prompt found for session. Using default.")
            system_prompt = "You are a concise voice assistant. Respond very briefly in French."

        # Creates the connection wrapper for Pipecat
        webrtc_connection = SmallWebRTCConnection(pc)

        transport = SmallWebRTCTransport(
            connection=webrtc_connection,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_out_enabled=False # Video will be activated when MuseTalk is integrated
            )
        )

        # 2. Services (The factory workers)
        # STT: Transcribes voice locally
        stt = WhisperSTTService(model="tiny", device="cpu", compute_type="int8")
        
        # LLM: Using Ollama for local POC (Ensure Ollama is running on port 11434)
        llm = OLLamaLLMService(model="llama3", base_url="http://localhost:11434")
        
        # Context setup
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        context = llm.create_context("default", messages)
        context_aggregator = llm.create_context_aggregator(context)

        # 3. Pipeline Configuration
        pipeline = Pipeline([
            transport.input(),                  #  Receives audio stream from the browser
            stt,                                # Transcribes voice to text
            context_aggregator.user(),          # Maintains conversation context
            llm,                                # Generates text response (Logged for now)
            # tts,                              # Converts text response to audio (To be implemented)
            transport.output(),                 # Sends audio back (Will be connected to TTS soon)
            context_aggregator.assistant()      # Updates context with assistant response
        ])

        # 4. Task Runner
        task = PipelineTask(pipeline)
        runner = PipelineRunner()

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            print("Frontend disconnected. Stopping bot.")
            await task.queue_frames([EndFrame()])

        await task.queue_frames([context_aggregator.user().get_context_frame()])  # Initialize context in the pipeline

        print("Pipecat started! Waiting for voice...")
        await runner.run(task)