"""
emotion_tag_processor.py

Detects {Emotion} or [Emotion] tags ANYWHERE in the LLM stream.
Sends the emotion to the frontend via WebRTC and strips it so TTS doesn't read it.
Handles chunked streaming seamlessly (State Machine approach).
"""

import re
from pipecat.frames.frames import TextFrame, Frame, TransportMessageFrame, LLMFullResponseStartFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

class EmotionTagProcessor(FrameProcessor):
    """
    Continuously scans the LLM text stream for emotion tags.
    Allows mid-sentence emotion changes and ensures no stray brackets reach the TTS.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._buffer = ""
        self._inside_tag = False  # State tracker for open brackets
        self.raw_llm_turn = ""

    def reset_turn(self):
        """Called at the start of a new user speaking turn."""
        self._buffer = ""
        self._inside_tag = False
        self.raw_llm_turn = ""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMFullResponseStartFrame):
            self.reset_turn()  # Clear state at the start of each new LLM response turn
            await self.push_frame(frame, direction)
            return

        if not isinstance(frame, TextFrame):
            # Pass non-text frames unmodified
            await self.push_frame(frame, direction)
            return

        self.raw_llm_turn += frame.text  # Keep track of the full raw LLM output for this turn (for logging/debugging

        self._buffer += frame.text
        clean_text_to_push = ""

        # Continuous parsing loop for the current buffer
        while True:
            if not self._inside_tag:
                # ── STATE 1: Looking for an opening bracket ──
                match = re.search(r'[\{\[]', self._buffer)
                if match:
                    # Append everything before the bracket to the clean text
                    clean_text_to_push += self._buffer[:match.start()]
                    # Keep the buffer from the bracket onwards
                    self._buffer = self._buffer[match.start():]
                    self._inside_tag = True
                else:
                    # No bracket found, all buffer is clean text
                    clean_text_to_push += self._buffer
                    self._buffer = ""
                    break
            else:
                # ── STATE 2: Inside a tag, looking for the closing bracket ──
                match = re.search(r'[\}\]]', self._buffer)
                if match:
                    # Extract the emotion word (excluding the brackets)
                    emotion = self._buffer[1:match.start()].strip().upper()
                    
                    if emotion:
                        await self._send_emotion_frame(emotion, direction)
                    
                    # Remove the entire tag from the buffer, switch state
                    self._buffer = self._buffer[match.end():]
                    self._inside_tag = False
                else:
                    # Safety net: If a bracket is opened but not closed after 25 chars
                    # (e.g., the LLM hallucinated a math equation), abort tag parsing
                    if len(self._buffer) > 25:
                        clean_text_to_push += self._buffer[0]
                        self._buffer = self._buffer[1:]
                        self._inside_tag = False
                    else:
                        # Wait for the next TextFrame to bring the closing bracket
                        break
        
        # Push the cleaned text downstream to the TTS
        if clean_text_to_push:
            await self.push_frame(TextFrame(clean_text_to_push), direction)

    async def _send_emotion_frame(self, emotion: str, direction: FrameDirection):
        """Packages the emotion into a TransportMessageFrame for the frontend."""
        try:
            payload = {
                "type": "emotion", 
                "value": emotion
            }
            await self.push_frame(TransportMessageFrame(message=payload), direction)
        except Exception as e:
            print(f"[EmotionTagProcessor] Error sending TransportMessageFrame: {e}", flush=True)