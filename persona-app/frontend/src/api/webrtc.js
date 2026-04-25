import { API } from "./config";

export async function connectWebRTC(mediaElementRef, onMessageReceived) {
    // Create a new RTCPeerConnection
    const pc = new RTCPeerConnection({
        iceServers: [],
    });

    const dataChannel = pc.createDataChannel("pipecat");
    dataChannel.addEventListener("message", (event) => {
        try {
            const data = JSON.parse(event.data);
            if (onMessageReceived) onMessageReceived(data);
        } catch (err) {
            console.error("ERROR parsing message from data channel:", err);
        }
    });
    // Request microphone access and add the audio track to the connection
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        stream.getTracks().forEach((track) => {
            pc.addTrack(track, stream);
            console.log("Added AUDIO track to RTCPeerConnection");
        });
    } catch (err) {
        console.error("ERROR accessing microphone:", err);
        throw new Error("Microphone access denied");
    }

    // Listenning for incoming tracks (audio from the bot)
    pc.addEventListener("track", (event) => {
        if (event.track.kind === "audio" || event.track.kind === "video") {
            console.log(`Received ${event.track.kind} track from bot, attaching to media element`);
            if (mediaElementRef.srcObject !== event.streams[0]) {
                mediaElementRef.srcObject = event.streams[0];
            }
        }
    });

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    
    await new Promise((resolve) => {
        if (pc.iceGatheringState === 'complete') {
            resolve();
        } else {
            const checkState = () => {
                if (pc.iceGatheringState === 'complete') {
                    pc.removeEventListener('icegatheringstatechange', checkState);
                    resolve();
                }
            };
            pc.addEventListener('icegatheringstatechange', checkState);
        }
    });

    const response = await fetch(`${API}/webrtc/connect`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ sdp: offer.sdp, type: offer.type })
    });

    if (!response.ok) {
        const txt = await response.text();
        console.error("WebRTC connection failed:", txt);
        throw new Error(txt || "WebRTC connection failed");
    }

    const answer = await response.json();
    await pc.setRemoteDescription(answer);
    console.log("WebRTC connection established successfully");

    return pc;
}