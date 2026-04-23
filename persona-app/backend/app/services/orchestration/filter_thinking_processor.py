from pipecat.frames.frames import TextFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

class FilterThinkingProcessor(FrameProcessor):
    """
    Filters out the thinking process from Qwen 3.5 
    so the TTS doesn't speak the internal reasoning.
    """
    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            # If the text contains the thinking block, we split and keep only the answer
            if "<answer>" in frame.text:
                clean_text = frame.text.split("\n\n")[-1]
                await self.push_frame(TextFrame(clean_text))
            else:
                await self.push_frame(frame)
        else:
            await self.push_frame(frame, direction)