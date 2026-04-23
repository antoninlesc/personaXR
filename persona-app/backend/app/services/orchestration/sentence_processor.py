import re
from pipecat.frames.frames import TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

class SentenceBoundaryProcessor(FrameProcessor):
    """
    Accumulates incoming text tokens and pushes them forward only when 
    a natural sentence boundary (punctuation) is detected.
    This ensures the TTS engine has enough context for natural prosody.
    """
    def __init__(self):
        super().__init__()
        self._text_buffer = ""
        # Regex to detect sentence boundaries: punctuation followed by a space or end of string
        self._boundary_pattern = re.compile(r'([.?!,;:…\n]+(?:\s|$))')

    async def process_frame(self, frame, direction: FrameDirection):
        
        await super().process_frame(frame, direction)

        if isinstance(frame, TextFrame):
            self._text_buffer += frame.text
            
            # Split the buffer using the boundary pattern
            parts = self._boundary_pattern.split(self._text_buffer)
            
            # If we found at least one boundary (parts length will be > 1)
            if len(parts) > 1:
                # Iterate through parts, combining text and its following punctuation
                for i in range(0, len(parts) - 1, 2):
                    chunk = parts[i] + parts[i+1]
                    if chunk.strip():
                        await self.push_frame(TextFrame(chunk.strip()), direction)
                
                # Keep whatever is left (incomplete sentence) in the buffer
                self._text_buffer = parts[-1]
                
        else:
            # Pass through audio and control frames untouched
            await super().process_frame(frame, direction)