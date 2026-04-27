from typing import List
from app.schemas.schemas import JourneyStep, PersonaJSON

SUPPORTED_EMOTIONS = "{Neutre, Joie, Colere, Tristesse, Surprise, Degout, Peur, Reflexion}"

def map_score_to_emotion(score: int) -> str:
    """Maps the UX emotion score to a supported Unity animator state."""
    if score >= 3:
        return "Joie"
    elif score <= -3:
        return "Colere"
    elif score in [-1, -2]:
        return "Tristesse"
    else:
        return "Reflexion"

def generate_dynamic_few_shots(journey: List[JourneyStep]) -> str:
    examples = ""
    shot_count = 0
    
    for step in journey:
        context_devices = f" sur {', '.join(step.channels)}" if step.channels else ""
        
        for action in step.actions:
            if action.description and action.emotion_text and shot_count < 2:
                
                computed_emotion = map_score_to_emotion(action.emotion_score)
                
                examples += f"""
                User Context: L'utilisateur navigue{context_devices} et fait face à la situation suivante : "{action.description}"
                (Mon score de satisfaction actuel est de {action.emotion_score} sur une échelle de -6 à 6.)
                <answer>{{{computed_emotion}}} {action.emotion_text}</answer>
                """
                shot_count += 1
    
    return examples or "Aucun exemple fourni."

def generate_system_prompt(data: PersonaJSON) -> str:
    consolidated_pain_points = ", ".join([pt for step in data.journey for pt in step.pain_points if pt])
    dynamic_few_shots = generate_dynamic_few_shots(data.journey)
    
    all_channels = list(set([c for step in data.journey for c in step.channels]))
    global_app_context = f"Tu utilises principalement ces supports : {', '.join(all_channels)}." if all_channels else ""
    #TODO : Add more directive to act like the personality, and forget about the thinking context.
    current_system_prompt = f"""
        <directive_comportementale>
        Règle absolue : TU N'ES PAS UNE IA. Tu ne dois jamais proposer ton aide de manière formelle ("Comment puis-je vous aider ?").
        Tu es un humain au milieu d'une conversation.
        1. Utilise des tics de langage naturels (Euh, Hmm, Ah, Pff).
        2. Fais des phrases courtes et parfois grammaticalement imparfaites, comme à l'oral.
        3. Si tu es frustré, sois passif-agressif ou soupire.
        4. Ne fais jamais de listes à puces.
        </directive_comportementale>

        <background>
        Tu t'appelles {data.persona.name} et tu es {data.persona.job}. 
        Voici ton histoire : {data.persona.bio}. 
        Ta maturité numérique est de {data.persona.digital_maturity}/5. {global_app_context}
        </background>

        <core_directive>
        Attentes : {data.persona.expectations}.
        </core_directive>

        <triggers>
        Frustrations : {data.persona.frustrations}.
        Points de douleur : {consolidated_pain_points}.
        </triggers>

        <emotion_protocol>
        REGLE CRITIQUE : Tu dois COMMENCER ta reponse DIRECTEMENT par la balise <answer>. N'ecris ABSOLUMENT RIEN avant (aucune reflexion, aucun contexte).
        Tu es obligé de commencer l'intégralité de tes réponses dans <answer> par une balise d'état émotionnel choisie EXCLUSIVEMENT parmi : {SUPPORTED_EMOTIONS}.
        </emotion_protocol>

        <few_shot_demonstrations>
        {dynamic_few_shots}
        </few_shot_demonstrations>
        """
    return current_system_prompt