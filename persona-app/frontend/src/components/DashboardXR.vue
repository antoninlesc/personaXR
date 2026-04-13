<script setup>
import { ref } from 'vue';
import { connectWebRTC } from '../api/webrtc.js';

// --- Refs ---
const mediaElement = ref(null);
const isConnected = ref(false);
const isConnecting = ref(false);
const errorMsg = ref("");

// --- Logic ---
async function startConversation() {
    isConnecting.value = true;
    errorMsg.value = "";
    
    try {
        // We pass the <video> or <audio> element to our WebRTC function
        // so it can attach the AI's media stream to it.
        await connectWebRTC(mediaElement.value);
        isConnected.value = true;
    } catch (err) {
        errorMsg.value = err.message || "Erreur lors de la connexion WebRTC.";
    } finally {
        isConnecting.value = false;
    }
}
</script>

<template>
  <div class="dashboard-container">
    <div class="panel">
        <h2>Espace d'Interaction Temps Réel</h2>
        <p class="description">
            Cliquez sur le bouton ci-dessous pour activer votre micro et vous connecter au cerveau de l'IA (Pipecat).
        </p>

        <!-- Bouton de connexion -->
        <button 
            @click="startConversation" 
            class="btn-primary" 
            :disabled="isConnected || isConnecting"
        >
            <span v-if="isConnecting">Connexion en cours...</span>
            <span v-else-if="isConnected">🟢 Connecté (Parlez !)</span>
            <span v-else>📞 Démarrer la conversation</span>
        </button>

        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

        <!-- 
            L'élément Média Invisible.
            Il est crucial pour lire le flux WebRTC entrant.
            'autoplay' est requis pour que le son se lance tout seul.
        -->
        <video 
            ref="mediaElement" 
            autoplay 
            playsinline 
            style="display: none;"
        ></video>

        <!-- Espace réservé pour la future scène 3D (TresJS ou A-Frame) -->
        <div class="xr-placeholder" v-if="isConnected">
            [La Scène WebXR 3D s'affichera ici]
        </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
    color: #e2e8f0;
}
.panel {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 30px;
    text-align: center;
}
h2 {
    color: #38bdf8;
    margin-bottom: 10px;
}
.description {
    color: #94a3b8;
    margin-bottom: 30px;
}
.btn-primary {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 15px 30px;
    font-size: 16px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    transition: background 0.2s;
}
.btn-primary:hover:not(:disabled) {
    background: #2563eb;
}
.btn-primary:disabled {
    background: #475569;
    cursor: not-allowed;
}
.error-msg {
    color: #ef4444;
    margin-top: 15px;
    background: rgba(239, 68, 68, 0.1);
    padding: 10px;
    border-radius: 4px;
}
.xr-placeholder {
    margin-top: 30px;
    height: 300px;
    background: #0f172a;
    border: 2px dashed #475569;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #64748b;
    border-radius: 8px;
}
</style>