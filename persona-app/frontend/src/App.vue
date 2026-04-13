<script setup>
import { ref } from 'vue';
import Form from './components/Form.vue';
import DashboardXR from './components/DashboardXR.vue';
// Navigation state: 'form' or 'xr'
const currentView = ref('form');
</script>

<template>
  <div id="app-root">
    <!-- Navbar -->
    <nav class="top-nav">
      <button 
        :class="{ active: currentView === 'form' }" 
        @click="currentView = 'form'"
      >
        1. Form & Parsing
      </button>
      <button 
        :class="{ active: currentView === 'xr' }" 
        @click="currentView = 'xr'"
      >
        2. Dashboard WebXR
      </button>
    </nav>

    <!-- Main Content -->
    <main>
      <Form v-if="currentView === 'form'" />
      <DashboardXR v-else-if="currentView === 'xr'" />
    </main>
  </div>
</template>

<style scoped>
#app-root {
  min-height: 100vh;
  background-color: #0f172a; /* Reprend la couleur de fond de ton form.css */
}

.top-nav {
  display: flex;
  background-color: #1e293b;
  padding: 0 20px;
  border-bottom: 2px solid #334155;
}

.top-nav button {
  background: none;
  border: none;
  color: #94a3b8;
  padding: 15px 20px;
  font-size: 16px;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  font-family: inherit;
}

.top-nav button:hover {
  color: #e2e8f0;
}

.top-nav button.active {
  color: #3b82f6;
  font-weight: bold;
  border-bottom-color: #3b82f6;
}

main {
  height: calc(100vh - 54px);
  overflow-y: auto;
}
</style>