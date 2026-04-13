from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription
import asyncio
from app.services.orchestration.bot_runner import run_bot

router = APIRouter(prefix="/webrtc", tags=["webrtc"])
#TODO : Rework and analyse this file, it is a first draft to test the connection between the frontend and backend via WebRTC, and to launch the Pipecat pipeline once the connection is established. It will likely need adjustments as we integrate MuseTalk and refine the pipeline logic.
class WebRTCOffer(BaseModel):
    sdp: str
    type: str

# Keep track of active peer connections
peer_connections = set()

@router.post("/connect")
async def webrtc_connect(offer: WebRTCOffer):
    """
    Handles the WebRTC SDP Offer from the frontend,
    creates an RTCPeerConnection, and returns the SDP Answer.
    """
    # 1. Create a new Peer Connection for this client
    pc = RTCPeerConnection()
    peer_connections.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"🌐 WebRTC Connection State: {pc.connectionState}")
        if pc.connectionState in ["failed", "closed"]:
            peer_connections.discard(pc)

    # 2. Parse the incoming offer from the frontend
    session_description = RTCSessionDescription(sdp=offer.sdp, type=offer.type)
    await pc.setRemoteDescription(session_description)

    # 3. Create an answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # 4. Start the Pipecat orchestration logic in the background
    # Pass the PeerConnection to Pipecat so it can attach its audio/video tracks
    asyncio.create_task(run_bot(pc))

    # 5. Send the answer back to the frontend to finalize the connection
    return JSONResponse({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })