from pydantic import BaseModel, Field
from typing import List, Optional

class Action(BaseModel):
    description: Optional[str] = ""
    emotion_score: Optional[int] = 0
    emotion_text: Optional[str] = ""

class JourneyStep(BaseModel):
    step_name: Optional[str] = ""
    channels: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)

class PersonaDetails(BaseModel):
    name: str = "Utilisateur Inconnu"
    job: Optional[str] = "Profession non spécifiée"
    bio: Optional[str] = "Aucune biographie disponible."
    digital_maturity: Optional[int] = 3
    insights: List[str] = Field(default_factory=list)
    expectations: Optional[str] = "Attentes standards."
    frustrations: Optional[str] = "Aucune frustration spécifique."

class PersonaJSON(BaseModel):
    persona: PersonaDetails
    journey: List[JourneyStep] = Field(default_factory=list)

class Message(BaseModel):
    role: str
    content: str

class ChatStreamRequest(BaseModel):
    user_message: str
    history: List[Message] = []