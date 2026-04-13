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
    asyncio.create_task(run_bot(connection))

    return JSONResponse({
        "sdp": answer.get("sdp"),
        "type": answer.get("type")
    })