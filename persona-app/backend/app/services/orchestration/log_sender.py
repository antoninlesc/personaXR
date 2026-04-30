import json

from pipecat.frames.frames import TextFrame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameProcessor


class WebRTCLogSender(FrameProcessor):
    def __init__(self, connection, role: str):
        super().__init__()
        self._connection = connection
        self.role = role


    def _send(self, payload: dict) -> None:
        """Fire-and-forget send; silently drops if the channel is closed."""
        try:
            self._connection.send_app_message(json.dumps(payload))
        except Exception:
            pass


    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
 
        # ROLE: STT - Catch transcription and calculate STT latency
        if self.role == "stt" and isinstance(frame, TranscriptionFrame):
            self._send({"type": "transcription", "text": frame.text})
                
        # ROLE: LLM - Catch AI response and calculate LLM latency
        elif self.role == "llm" and isinstance(frame, TextFrame):
            self._send({"type": "llm_response", "text": frame.text})

        # Push the frame downstream to keep the pipeline alive
        await self.push_frame(frame, direction)