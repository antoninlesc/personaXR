
from pipecat.frames.frames import LLMMessagesFrame, Frame, LLMFullResponseStartFrame
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

class ContextSlidingWindowProcessor(FrameProcessor):
    def __init__(self, emotion_processor=None, max_messages: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.max_messages = max_messages
        self.emotion_processor = emotion_processor

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # ── Duck Typing : On intercepte n'importe quelle frame qui descend vers le LLM
        # et qui transporte un contexte (messages). A la place de faire du FrameType checking rigide, on vérifie simplement la présence d'un attribut "messages" ou "context.messages".
        messages = None
        if direction == FrameDirection.DOWNSTREAM:
            if hasattr(frame, "messages"):
                messages = frame.messages
            elif hasattr(frame, "context") and hasattr(frame.context, "messages"):
                messages = frame.context.messages

        if messages is not None:

            # --- 1. THE RE-INJECTION HACK (V2) ---
            for i in range(len(messages)-1, -1, -1):
                if messages[i]['role'] == 'assistant':
                    if self.emotion_processor and hasattr(self.emotion_processor, 'raw_llm_turn'):
                        raw_text = self.emotion_processor.raw_llm_turn
                        if raw_text and raw_text.strip():
                            messages[i]['content'] = raw_text
                    break        
            
            # --- 2. THE SLIDING WINDOW ---
            if len(messages) > self.max_messages + 1:
                system_prompt = messages[0]
                recent_messages = messages[-self.max_messages:]
                
                # Astuce : On modifie la liste "in-place" (.clear() + .extend()) 
                # pour ne pas altérer l'objet Frame original généré par Pipecat.
                messages.clear()
                messages.extend([system_prompt] + recent_messages)
                
            # On laisse passer la frame modifiée
            await self.push_frame(frame, direction)
        else:
            # On laisse passer toutes les autres frames (Audio, STT, etc.)
            await self.push_frame(frame, direction)