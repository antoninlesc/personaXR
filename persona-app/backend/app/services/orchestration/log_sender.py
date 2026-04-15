from dataclasses import dataclass
import json
import time

from pipecat.frames.frames import TextFrame, TranscriptionFrame,UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection


@dataclass
class SessionMetrics:
    last_speech_stop: float = 0.0
    stt_done_time: float = 0.0
    llm_turn_calculated: float = 0.0

class WebRTCLogSender(FrameProcessor):
    def __init__(self, connection, session_metrics: SessionMetrics, role: str):
        super().__init__()
        self._connection = connection
        self.session_metrics = session_metrics
        self.role = role
        
    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if self.role == "vad" and isinstance(frame, UserStoppedSpeakingFrame) and direction == FrameDirection.DOWNSTREAM:
            self.session_metrics.last_speech_stop = time.time()
            
        # ROLE: STT - Catch transcription and calculate STT latency
        if self.role == "stt" and isinstance(frame, TranscriptionFrame):
            print(f"[DEBUG STT] Transcribed: {frame.text}") 
            
            stt_done = time.time()
            self.session_metrics.stt_done_time = stt_done
            speech_stop = self.session_metrics.last_speech_stop
            
            if speech_stop > 0:
                stt_latency = stt_done - speech_stop
                print(f"⏱️ [LATENCY] STT Delta (Transcription - Stop): {stt_latency:.3f} sec")
                try:
                    metrics_msg = json.dumps({"type": "metrics", "data": {"ttfs": stt_latency}})
                    self._connection.send_app_message(metrics_msg)
                except Exception:
                    pass
            
            try:
                msg = json.dumps({"type": "transcription", "text": frame.text})
                self._connection.send_app_message(msg)
            except Exception:
                pass
                
        # ROLE: LLM - Catch AI response and calculate LLM latency
        elif self.role == "llm" and isinstance(frame, TextFrame):
            print(f"[DEBUG LLM] Generated: {frame.text}")
            
            stt_time = self.session_metrics.stt_done_time
            last_calculated_turn = self.session_metrics.llm_turn_calculated
            
            if stt_time > 0 and stt_time != last_calculated_turn:
                # Mark this turn as calculated so we only measure TTFB on the first token
                self.session_metrics.llm_turn_calculated = stt_time 
                
                ttfb = time.time() - stt_time
                print(f"🚀 [LATENCY] Custom LLM TTFB: {ttfb:.3f} sec")
                
                try:
                    metrics_msg = json.dumps({"type": "metrics", "data": {"ttfb": ttfb}})
                    self._connection.send_app_message(metrics_msg)
                except Exception:
                    pass

            # Send the text chunk to the Vue frontend
            try:
                msg = json.dumps({"type": "llm_response", "text": frame.text})
                self._connection.send_app_message(msg)
            except Exception:
                pass

        # Push the frame downstream to keep the pipeline alive
        await self.push_frame(frame, direction)