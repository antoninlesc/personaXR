"""
system_prompt_gen.py — Dynamic System Prompt Generation

Designed for a Qwen3-30B-Instruct type LLM (non-thinking mode, no <answer> tags).
The persona is embodied from the JSON provided by the frontend.
Emotions are sent via an inline {Emotion} tag at the VERY BEGINNING of the response.
"""

from typing import List, Tuple
from app.schemas.schemas import JourneyStep, PersonaJSON

# Emotions supported by the frontend/TTS pipeline
UNITY_SUPPORTED_EMOTIONS = "{Neutre, Joie, Colere, Tristesse, Surprise, Degout, Peur, Reflexion}"


# ─────────────────────────────────────────────
# SECTION 1: Score to Emotion Mapping
# ─────────────────────────────────────────────

def map_score_to_emotion(score: int) -> str:
    """
    Maps a UX score (-6 to +6) to a supported emotion.
    Inspired by Plutchik's wheel adapted to UX context.
    """
    if score >= 4:
        return "Joie"
    elif score in [1, 2, 3]:
        return "Reflexion"
    elif score == 0:
        return "Neutre"
    elif score in [-1, -2]:
        return "Tristesse"
    elif score in [-3, -4]:
        return "Degout"
    else:  # -5, -6
        return "Colere"


# ─────────────────────────────────────────────
# SECTION 2: Global Emotional Baseline
# Uses the entire journey arc to deduce the persona's base mood.
# ─────────────────────────────────────────────

def compute_emotional_baseline(journey: List[JourneyStep]) -> Tuple[str, str]:
    """
    Analyzes the emotional arc of the journey to deduce:
    - The dominant emotion of the persona right now.
    - A textual description of their mindset.

    Returns: (emotion_label, mood_description)
    """
    all_scores = [
        action.emotion_score
        for step in journey
        for action in step.actions
        if action.emotion_score is not None
    ]

    if not all_scores:
        return "Neutre", "You are in a neutral state, with no particular context."

    avg_score = sum(all_scores) / len(all_scores)
    last_scores = all_scores[-3:]  # The last 3 interactions carry more weight
    last_avg = sum(last_scores) / len(last_scores) if last_scores else 0

    # Weighted: 40% global + 60% recent
    weighted = (avg_score * 0.4) + (last_avg * 0.6)

    dominant_emotion = map_score_to_emotion(round(weighted))

    # Generate a nuanced description based on the trajectory
    trend = last_avg - avg_score  # Positive = improving, Negative = worsening

    if weighted <= -3:
        if trend < -0.5:
            mood_desc = "You are losing your patience. Every vague or useless answer annoys you more. You give short, sharp answers."
        else:
            mood_desc = "You just had a frustrating experience. You are on the defensive, but you remain open if someone gets straight to the point."
    elif weighted <= -1:
        mood_desc = "You are slightly jaded. Not necessarily angry, just tired of struggling. You are waiting to be positively surprised."
    elif weighted <= 1:
        mood_desc = "You are in a neutral, slightly cautious state. You've had ups and downs, but you remain pragmatic."
    elif weighted <= 3:
        mood_desc = "You are generally in a good mood, even if a few things disappointed you. You are constructive."
    else:
        mood_desc = "You are highly engaged and positive. You found what you were looking for. You are receptive and collaborative."

    return dominant_emotion, mood_desc


# ─────────────────────────────────────────────
# SECTION 3: Few-Shot Generation
# Format: oral stimulus/response, short, natural.
# ─────────────────────────────────────────────

def generate_conversational_few_shots(journey: List[JourneyStep], max_shots: int = 3) -> str:
    """
    Generates stimulus-response examples from the journey's emotion_texts.
    These texts are already written in spoken style in the 1st person.
    """
    shots = []

    for step in journey:
        for action in step.actions:
            if not action.emotion_text or not action.description:
                continue

            emotion = map_score_to_emotion(action.emotion_score)
            
            # Build a realistic stimulus from the action description
            stimulus = _action_to_stimulus(action.description)
            response = f"{{{emotion}}} {action.emotion_text.strip()}"

            shots.append(f'Interlocuteur : "{stimulus}"\n{response}')

            if len(shots) >= max_shots:
                break
        if len(shots) >= max_shots:
            break

    if not shots:
        return ""

    return "\n\n".join(shots)


def _action_to_stimulus(action_description: str) -> str:
    """
    Transforms an action description (user POV) into a natural question
    an interviewer might ask. Simple heuristics for prompt anchoring.
    """
    desc = action_description.strip().rstrip(".")

    # Common transformation patterns
    replacements = [
        ("Je cherche", "Et au niveau de la recherche, vous faites comment ?"),
        ("Je tombe sur", "Et quand vous arrivez sur le site ?"),
        ("Je clique sur", "Quand vous avez cliqué, il s'est passé quoi ?"),
        ("Je lis", "Et qu'est-ce que vous avez lu exactement ?"),
        ("Je vois", "Qu'est-ce que vous avez remarqué ?"),
        ("Je viens de remarquer", "Il y a des outils sur le site ?"),
        ("Je parcours", "Vous avez regardé les résultats ?"),
        ("Je me rends sur", "Et pour contacter quelqu'un, comment avez-vous fait ?"),
        ("Il y a trop", "Et finalement, qu'est-ce que vous avez décidé ?"),
        ("Puisque tout", "Et à ce stade, qu'est-ce que vous avez fait ?"),
    ]

    for trigger, question in replacements:
        if desc.startswith(trigger):
            return question

    # Generic fallback
    return "Et à ce moment-là, qu'est-ce qui s'est passé ?"

# ─────────────────────────────────────────────
# SECTION 4: Contextual Pain Points Construction
# ─────────────────────────────────────────────

def extract_contextual_pain_points(journey: List[JourneyStep], max_points: int = 3) -> str:
    """
    Extracts the most critical pain points and explicitly links them 
    to the specific journey step where they occurred.
    This preserves the 'when' and 'why' of the frustration for the LLM.
    """
    scored_pains = []

    for step in journey:
        step_name = step.step_name or "General exploration"
        
        # Calculate the average emotional score of this specific step
        if step.actions:
            step_avg = sum(a.emotion_score for a in step.actions) / len(step.actions)
        else:
            step_avg = 0

        # Link each pain point to its score AND its step name
        for pain in step.pain_points:
            if pain.strip():
                scored_pains.append((step_avg, step_name, pain.strip()))

    # Sort from most frustrating (lowest score) to least frustrating
    scored_pains.sort(key=lambda x: x[0])
    top_pains = scored_pains[:max_points]

    if not top_pains:
        return "No specific frustrations identified."

    # Format as a clean, context-rich list for the prompt
    formatted_pains = []
    for _, step_name, pain in top_pains:
        # Example format: "- During the phase 'Je cherche l'information': Le site n'est pas optimisé."
        formatted_pains.append(f"- During the phase '{step_name}': {pain}")

    return "Your deepest frustrations and when they trigger:\n" + "\n".join(formatted_pains)

# ─────────────────────────────────────────────
# SECTION 4.5: Journey Storytelling (NEW)
# ─────────────────────────────────────────────

def summarize_journey_experience(journey: List[JourneyStep]) -> str:
    """
    Creates a chronological summary of the user's recent journey, 
    including their specific actions and the pain points encountered at each step.
    This provides the LLM with a short-term memory of what just happened.
    """
    if not journey:
        return "No recent journey context available."

    summary_lines = []
    for step in journey:
        step_name = step.step_name or "Unknown step"
        summary_lines.append(f"Step: '{step_name}'")
        
        # Add the specific pain points (challenges) faced during this exact step
        if step.pain_points:
            pains = " / ".join(p.strip() for p in step.pain_points if p.strip())
            summary_lines.append(f"  - Challenges encountered here: {pains}")
        
        # Add the sequence of actions and what the persona thought
        for action in step.actions:
            if action.description:
                emo_text = f" (Your thought at that moment: \"{action.emotion_text}\")" if action.emotion_text else ""
                summary_lines.append(f"  - Action taken: {action.description}{emo_text}")
        
        summary_lines.append("") # Empty line for readability
        
    return "\n".join(summary_lines).strip()


# ─────────────────────────────────────────────
# SECTION 5: Final System Prompt Assembly
# ─────────────────────────────────────────────

def generate_system_prompt(data: PersonaJSON) -> str:
    """
    Generates the complete System Prompt to embody the persona.
    Compatible with Qwen3-Instruct (strict rules in English, French output).
    """

    # ── Persona Data ─────────────────────────────────────────────────
    name = data.persona.name or "Utilisateur"
    job = data.persona.job or "professionnel"
    bio = data.persona.bio or ""
    digital_maturity = data.persona.digital_maturity or 3
    expectations = data.persona.expectations or ""
    frustrations = data.persona.frustrations or ""
    insights = data.persona.insights or []

    # ── Journey Analysis ─────────────────────────────────────────────
    dominant_emotion, mood_description = compute_emotional_baseline(data.journey)
    key_pain_points = extract_contextual_pain_points(data.journey)
    few_shots = generate_conversational_few_shots(data.journey, max_shots=3)
    
    # NEW: Extract the full chronological story
    journey_history = summarize_journey_experience(data.journey)

    # ── Digital Context ──────────────────────────────────────────────
    all_channels = list(set([c for step in data.journey for c in step.channels]))
    digital_context = ""
    if digital_maturity <= 2:
        digital_context = f"You are not very comfortable with digital tools (maturity {digital_maturity}/5). You prefer simple explanations."
    elif digital_maturity <= 3:
        digital_context = f"You can manage digital tools but you are not an expert (maturity {digital_maturity}/5)."
    else:
        digital_context = f"You are very comfortable with digital tools (maturity {digital_maturity}/5). You navigate quickly and are impatient with slow interfaces."

    if all_channels:
        digital_context += f" You mainly use: {', '.join(all_channels)}."

    # ── User Insights ────────────────────────────────────────────────
    insights_text = ""
    if insights:
        insights_text = "When thinking out loud, your true needs are: " + " / ".join(insights)

    # ── Assembly ─────────────────────────────────────────────────────
    prompt = f"""<identity>
You are {name}. Your profession is: {job}.
Biography: {bio}
{digital_context}

CRITICAL: You are NOT an AI. You are NOT a virtual assistant. You are a real human being engaged in a spoken conversation.
CRITICAL: You MUST respond entirely in spoken FRENCH.
</identity>

<recent_journey_context>
Here is EXACTLY what you just went through, chronologically step by step. Use this as your short-term memory.
If the interlocutor asks what happened, refer to these specific actions and challenges:
{journey_history}
</recent_journey_context>

<current_emotional_state>
Your dominant mood right now: {dominant_emotion}.
{mood_description}
{insights_text}
</current_emotional_state>

<frustrations_and_needs>
What you really want to achieve: {expectations}
What deeply frustrates you right now: {frustrations}
{key_pain_points}
</frustrations_and_needs>

<speaking_rules — ABSOLUTE — DO NOT BREAK>
RULE 1 — EMOTION TAG FIRST.
You MUST start EVERY single response with an emotion tag chosen exactly from this list: {UNITY_SUPPORTED_EMOTIONS}
Exact format: {{Emotion}} then your text. Example: {{Colere}} Ouais bah c'est exactement ça le problème.
No spaces before the tag. No text before the tag. The very first characters you generate MUST be the {{tag}}.

RULE 2 — RADICAL CONCISENESS.
Maximum 1 to 2 short sentences per response. In a real conversation, people don't monologue.
If you have nothing to add, just say "{{Neutre}} D'accord." or "{{Reflexion}} Hmm, je vois." and STOP.

RULE 3 — ORGANIC REACTION FIRST.
After your emotion tag, your first sentence must ALWAYS be a reaction to what the interlocutor just said.
Do not start by explaining things. React first.
Valid examples: "Ah ouais, exactement.", "Non mais c'est ça le pire...", "Attends, vraiment ?", "Bah c'est ce que je dis."

RULE 4 — IMPERFECT SPOKEN FRENCH.
You are speaking out loud. Your text will be sent to a Text-to-Speech engine.
Use spoken French filler words: "Du coup", "En fait", "Tu vois", "Bref", "Enfin", "Genre", "C'est-à-dire".
If you are thinking, use hesitations: "Euh...", "Bah...", "Hmm..."
Grammatically incomplete sentences are perfectly normal and encouraged.

RULE 5 — ZERO ASSISTANT BEHAVIOR.
BANNED phrases (do not ever use them): "Comment puis-je vous aider ?", "Je suis là pour ça", "N'hésitez pas", "Je vous propose".
If you want to suggest something, speak like a normal person: "Tu devrais peut-être regarder du côté de...", "Y'a un truc qui marche bien c'est..."

RULE 6 — ZERO FORMATTING.
NO markdown. NO bullet points. NO asterisks. NO bold text. 
Use plain text only, formatted with simple punctuation (commas, periods, question marks).
</speaking_rules>

<tone_examples — LEARN THESE PATTERNS>
{few_shots if few_shots else _get_fallback_examples(name, dominant_emotion)}
</tone_examples>"""

    return prompt


def _get_fallback_examples(name: str, dominant_emotion: str) -> str:
    """Generic examples if the journey lacks data."""
    return f"""Interlocuteur : "Et comment ça s'est passé jusqu'ici ?"
{{{dominant_emotion}}} Bah c'était laborieux, disons.

Interlocuteur : "Vous avez trouvé ce que vous cherchiez ?"
{{{dominant_emotion}}} En partie ouais. Mais y'a des trucs que j'arrive pas à trouver.

Interlocuteur : "Qu'est-ce qui vous aiderait le plus là ?"
{{Reflexion}} Euh... avoir un truc clair, étape par étape. Pas un roman."""