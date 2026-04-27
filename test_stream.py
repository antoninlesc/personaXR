import requests
import json
import sys

url = "https://n8m6modr2tx3r0-8000.proxy.runpod.net/v1/chat/completions"

payload = {
    "model": "qwen-3-30b",
    "messages": [
        {"role": "system", "content": "Tu es un assistant vocal."},
        {"role": "user", "content": "Raconte-moi une blague très longue en 5 phrases."}
    ],
    "stream": True,
    "max_tokens": 150
}

print("⏳ Envoi de la requête... attente du premier mot (TTFT)...")

# On fait la requête en demandant explicitement le mode "stream"
response = requests.post(url, json=payload, stream=True)

# On lit la réponse ligne par ligne au fur et à mesure qu'elle arrive via internet
for line in response.iter_lines():
    print(f"Received line: {line}")  # Debug: Affiche la ligne brute reçue
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith("data: ") and line_str != "data: [DONE]":
            # On extrait juste le texte du JSON
            try:
                data = json.loads(line_str[6:])
                content = data["choices"][0]["delta"].get("content", "")
                # On l'imprime à l'écran sans passer à la ligne pour faire l'effet machine à écrire
                sys.stdout.write(content)
                sys.stdout.flush()
            except json.JSONDecodeError:
                pass

print("\n\n✅ Terminé !")