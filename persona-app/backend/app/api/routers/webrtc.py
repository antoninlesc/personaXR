import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
import asyncio
from app.services.orchestration.bot_runner import run_bot

router = APIRouter(prefix="/webrtc", tags=["webrtc"])
#TODO : Rework and analyse this file, it is a first draft to test the connection between the frontend and backend via WebRTC, and to launch the Pipecat pipeline once the connection is established. It will likely need adjustments as we integrate MuseTalk and refine the pipeline logic.
class WebRTCOffer(BaseModel):
    sdp: str
    type: str

@router.post("/connect")
async def webrtc_connect(offer: WebRTCOffer):
    """
    Handles the WebRTC SDP Offer from the frontend,
    creates an RTCPeerConnection, and returns the SDP Answer.
    """
    connection = SmallWebRTCConnection()

    await connection.initialize(sdp=offer.sdp, type=offer.type)
    answer = connection.get_answer()

    # --- CORRECTIF TAILSCALE (SDP Rewrite) ---
    sdp_str = answer.get("sdp")
    tailscale_ip = "100.76.122.76"  # Ton IP Tailscale fixe du Runpod
    
    # 1. Remplacer l'IP dans la ligne de connexion globale
    sdp_str = re.sub(r"(c=IN IP4 )\d+\.\d+\.\d+\.\d+", rf"\g<1>{tailscale_ip}", sdp_str)
    
    # 2. Remplacer l'IP dans les candidats ICE locaux générés par Python
    sdp_str = re.sub(r"(\d+\.\d+\.\d+\.\d+)(.*typ host)", rf"{tailscale_ip}\2", sdp_str)
    # Autre approche regex si la précédente rate selon le formatage exact :
    sdp_str = re.sub(r"(a=candidate.* )\d+\.\d+\.\d+\.\d+( .*typ host)", rf"\g<1>{tailscale_ip}\g<2>", sdp_str)
    
    answer["sdp"] = sdp_str
    print("===================================")
    print("SDP Answer after Tailscale rewrite:")
    print(answer["sdp"])
    print("===================================")
    # ------------------------------------------

    asyncio.create_task(run_bot(connection))

    return JSONResponse({
        "sdp": answer.get("sdp"),
        "type": answer.get("type")
    })