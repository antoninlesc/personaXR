<script setup>
import { ref, onUpdated, nextTick } from 'vue';
import { connectWebRTC } from '../api/webrtc.js';


const mediaElement = ref(null);
const chatLogRef = ref(null); // Reference to the log window for auto-scrolling
const isConnected = ref(false);
const isConnecting = ref(false);
const errorMsg = ref("");

// State for the avatar and emotion placeholder
const currentEmotion = ref("NEUTRAL"); // Default emotion

// State for chat and metrics
const chatHistory = ref([]);
const latencyMetrics = ref({
    ttfs: { label: "1. STT (Whisper BASE model TTFS)", value: 0 }, // Time to First Sound (STT Delay)
    ttfb: { label: "2. LLM (Llama 3 TTFB)", value: 0 }  // Time to First Byte (LLM Delay)
});

// This function is called every time Python sends a message via the Data Channel
function handlePipecatMessage(rawData) {
    
    // Sécurité Anti-Double-Stringify
    let data = rawData;
    if (typeof rawData === "string") {
        try { data = JSON.parse(rawData); } catch(e) {}
    }

    if (data.type === "transcription") {
        // User speech transcribed
        chatHistory.value.push({ role: "user", text: data.text, timestamp: new Date().toLocaleTimeString() });
        scrollToBottom();
    } 
    else if (data.type === "llm_response") {
        // AI generated a response (Streamed chunk by chunk)
        let chunk = data.text;
        
        // Filtrage des tokens système de Llama 3 qui fuitent dans le stream
        chunk = chunk.replace(/<\|.*?\|>/g, '');
        if (chunk.trim() === "assistant" && chatHistory.value.length > 0 && chatHistory.value[chatHistory.value.length-1].role === "user") {
            return; // Ignore le mot "assistant" isolé au tout début de la réponse
        }

        let lastMsg = chatHistory.value[chatHistory.value.length - 1];
        
        // Si le dernier message est de l'IA, on concatène pour faire un effet "Machine à écrire"
        if (lastMsg && lastMsg.role === "assistant") {
            lastMsg.text += chunk;
        } else {
            // Sinon on crée une nouvelle bulle (seulement si le texte n'est pas vide)
            if (chunk.trim() !== "") {
                chatHistory.value.push({ role: "assistant", text: chunk, timestamp: new Date().toLocaleTimeString() });
            }
        }
        scrollToBottom();
    }
    else if (data.type === "emotion") {
        // Emotion tag received from the backend
        console.log("Avatar emotion updated to:", data.value);
        currentEmotion.value = data.value; // Log pour vérifier l'émotion reçue
    }

    else if (data.type === "metrics") {
        // Detailed latency data received dynamically
        if (data.data) {
            // Standard metrics
            if (data.data.ttfs) latencyMetrics.value.ttfs.value = Math.round(data.data.ttfs * 1000);
            if (data.data.ttfb) latencyMetrics.value.ttfb.value = Math.round(data.data.ttfb * 1000);
            
            // Add all other raw metrics dynamically for deep debugging
            for (const [key, val] of Object.entries(data.data)) {
                if (key !== 'ttfs' && key !== 'ttfb' && typeof val === 'number') {
                    if (!latencyMetrics.value[key]) {
                        // Créer une nouvelle ligne de métrique si elle n'existe pas
                        latencyMetrics.value[key] = { label: "🔍 " + key.toUpperCase(), value: 0 };
                    }
                    latencyMetrics.value[key].value = Math.round(val * 1000);
                }
            }
        }
    }
}

async function startConversation() {
    isConnecting.value = true;
    errorMsg.value = "";
    
    try {
        // We pass the media element AND our callback function to the WebRTC API
        await connectWebRTC(mediaElement.value, handlePipecatMessage);
        isConnected.value = true;
        chatHistory.value.push({ role: "system", text: "Connexion établie. Vous pouvez parler." });
    } catch (err) {
        errorMsg.value = err.message || "Erreur lors de la connexion WebRTC.";
    } finally {
        isConnecting.value = false;
    }
}

// Helper to keep the chat window scrolled to the latest message
async function scrollToBottom() {
    await nextTick();
    if (chatLogRef.value) {
        chatLogRef.value.scrollTop = chatLogRef.value.scrollHeight;
    }
}
</script>

<template>
  <div class="dashboard-container">
    
    <!-- Left Column: 3D Scene -->
    <div class="scene-panel">
        <!-- <h2>Real Time Avatar</h2> -->
        <div class="placeholder emotion-container">
            <div class="emotion-avatar" :class:="currentEmotion.toLowerCase()">
                <span class="emotion-text">{{ currentEmotion }}</span>
            </div>
        </div>
    </div>
    
    <!-- Right Column: Controls, Chat Log & Metrics -->
    <div class="control-panel panel">
        <h2>Real Time Interaction</h2>
        
        <button 
            @click="startConversation" 
            class="btn-primary" 
            :disabled="isConnected || isConnecting"
        >
            <span v-if="isConnecting">Connexion en cours...</span>
            <span v-else-if="isConnected">Connecté</span>
            <span v-else>Démarrer la conversation</span>
        </button>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <!-- Hidden audio player for WebRTC stream -->
        <video ref="mediaElement" autoplay playsinline style="display: none;"></video>

        <hr class="divider" />

        <!-- Chat Log Terminal -->
        <div class="chat-log" ref="chatLogRef">
            <div 
                v-for="(msg, idx) in chatHistory" 
                :key="idx" 
                :class="['log-entry', `log-${msg.role}`]"
            >
                <span class="log-time">[{{ msg.timestamp }}]</span>
                <span class="log-role">{{ msg.role === 'user' ? 'Vous' : (msg.role === 'assistant' ? 'IA' : 'Sys') }}:</span>
                <span class="log-text">{{ msg.text }}</span>
            </div>
        </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
    display: flex;
    gap: 20px;
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
    color: #e2e8f0;
    height: 85vh; /* Keep it constrained to viewport */
}

.scene-panel {
    flex: 1.5;
    background: #0f172a;
    border-radius: 8px;
    border: 1px solid #334155;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.scene-panel .placeholder {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    border: 2px dashed #334155;
    margin: 20px;
    border-radius: 8px;
}

.control-panel {
    flex: 1;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    flex-direction: column;
}

h2 { color: #38bdf8; margin-bottom: 15px; font-size: 1.2rem; text-align: center; }

.btn-primary {
    background: #3b82f6; color: white; border: none; padding: 12px; font-size: 16px; 
    border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; transition: 0.2s;
}
.btn-primary:disabled { background: #059669; cursor: default; } /* Green when connected */

.divider { border-color: #334155; margin: 20px 0; border-bottom: 0; }

/* Metrics */
.metrics-box {
    background: #0f172a; padding: 15px; border-radius: 6px; margin-bottom: 15px;
    border: 1px solid #1e293b;
}
.metrics-title { font-size: 0.85rem; color: #38bdf8; margin-top: 0; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
.metric { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.metric:last-child { margin-bottom: 0; }
.metric-label { font-size: 0.9rem; color: #94a3b8; }
.metric-value { font-family: monospace; font-weight: bold; font-size: 1.1rem; }
.metric-value.good { color: #10b981; }
.metric-value.bad { color: #ef4444; }

/* Chat Log */
.chat-log {
    flex: 1;
    background: #0b1120;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 10px;
    overflow-y: auto;
    font-family: 'Consolas', monospace;
    font-size: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.log-entry { line-height: 1.4; padding: 4px; border-radius: 4px; }
.log-time { color: #64748b; margin-right: 8px; }
.log-role { font-weight: bold; margin-right: 8px; }

.log-user .log-role { color: #38bdf8; }
.log-user .log-text { color: #e2e8f0; }

.log-assistant { background: rgba(52, 211, 153, 0.05); }
.log-assistant .log-role { color: #10b981; }
.log-assistant .log-text { color: #a7f3d0; }

.log-system .log-role { color: #f59e0b; }
.log-system .log-text { color: #fcd34d; font-style: italic; }
</style>