from fastapi import APIRouter, HTTPException
import httpx
import json

router = APIRouter(prefix="/avatar", tags=["Avatar"])

# TODO: COMFY UI URL et integration dans le workflow

@router.post("/generate")
async def generate_avatar(prompt: str):
    """
    Reçoit le prompt depuis Vue.js, l'injecte dans le workflow JSON,
    et commande à ComfyUI de générer l'image.
    """
    # 1. Charger ton workflow exporté (le fichier JSON créé via l'interface ComfyUI)
    with open("app/assets/workflow_api.json", "r") as f:
        workflow = json.load(f)

    # 2. Trouver le nœud qui contient le texte (ex: le nœud n°6 est souvent le Text Encode)
    # Tu devras ajuster l'ID "6" selon ton propre workflow ComfyUI
    workflow["6"]["inputs"]["text"] = f"A professional portrait of {prompt}, facing forward, neutral expression, 8k resolution"

    # 3. Envoyer l'ordre à ComfyUI
    async with httpx.AsyncClient() as client:
        try:
            # On envoie le JSON de configuration à l'API interne de ComfyUI
            response = await client.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
            response.raise_for_status()
            
            data = response.json()
            prompt_id = data.get("prompt_id")
            
            return {
                "status": "generation_started", 
                "prompt_id": prompt_id,
                "message": "ComfyUI calcule l'image..."
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur ComfyUI : {str(e)}")