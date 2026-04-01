import requests
import json
import time

# Configuration
URL_CHAT = "http://localhost:8000/chat/stream"
URL_LOAD = "http://localhost:8000/load-persona"

# 10 Questions conçues pour piéger l'IA sur sa mémoire
questions = [
    "Bonjour, je m'appelle Julien. Je dois remplir mon formulaire fiscal 2042.",
    "C'est la première fois que je le fais, je suis un peu perdu. Tu peux m'aider ?",
    "Au fait, comment je m'appelle déjà ?",  # Test de mémoire à court terme
    "D'accord. Et de quel formulaire précis on parlait juste avant ?", # Test de contexte thématique
    "Je vois une case '1AJ', ça correspond à quoi dans ce document ?",
    "Pff, c'est compliqué tout ça... tu en penses quoi toi de l'administration française ?",
    "Est-ce que je peux faire cette démarche en ligne ?",
    "Et si je me trompe dans les chiffres, je risque quoi ?",
    "Tu peux me lister les 3 points clés dont on vient de parler ?", # Test de synthèse de l'historique
    "Merci pour ton aide ! Au fait, quel est ton métier à toi ?" # Test de mémoire sur le System Prompt (Persona)
]

def run_test():
    print("="*50)
    print("🤖 DÉBUT DU TEST DE MÉMOIRE (10 QUESTIONS)")
    print("="*50)
    
    # L'historique qui va grossir à chaque question
    history = []

    for i, q in enumerate(questions, 1):
        print(f"\n🗣️ [Tour {i}/10] User : {q}")

        payload = {
            "user_message": q,
            "history": history
        }

        try:
            # On appelle l'API en mode stream
            response = requests.post(URL_CHAT, json=payload, stream=True)
            
            if response.status_code != 200:
                print(f"❌ Erreur serveur : {response.status_code}")
                break

            ai_full_text = ""
            current_emotion = "Neutre"

            print(f"🧠 IA : ", end="", flush=True)

            # Lecture du flux SSE
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        try:
                            data_json = json.loads(data_str)
                            if data_json["type"] == "emotion":
                                current_emotion = data_json["value"]
                                print(f"[{current_emotion}] ", end="", flush=True)
                            elif data_json["type"] == "text":
                                chunk = data_json["value"]
                                ai_full_text += chunk
                                print(chunk, end="", flush=True)
                        except json.JSONDecodeError:
                            pass

            print("\n")

            # --- MISE À JOUR DE LA MÉMOIRE ---
            # On ajoute la question de l'utilisateur
            history.append({"role": "user", "content": q})
            # On ajoute la réponse de l'IA (en incluant l'émotion pour qu'elle se rappelle de son humeur !)
            history.append({"role": "assistant", "content": f"{{{current_emotion}}} {ai_full_text}"})

            # Petite pause de 2 secondes pour ne pas surcharger le serveur Ollama
            time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion au serveur : {e}")
            break

if __name__ == "__main__":
    # Avertissement
    print("⚠️ Assurez-vous que FastAPI tourne et qu'une Persona a été chargée (via l'interface HTML) avant de lancer ce script.\n")
    run_test()