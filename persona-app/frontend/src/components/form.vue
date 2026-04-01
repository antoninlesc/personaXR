<template>
  <div class="container">
    <div class="header">
      <h2>Persona & Journey Parser</h2>
      <input type="file" accept=".pptx" @change="onFile" class="file-input" />
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div v-if="data" class="content">
      <!-- Tabs Navigation -->
      <div class="tabs">
        <button 
          :class="{ active: currentTab === 'persona' }" 
          @click="currentTab = 'persona'">
          Persona (Slide 1)
        </button>
        <button 
          :class="{ active: currentTab === 'journey' }" 
          @click="currentTab = 'journey'">
          Journey Map (Slide 2)
        </button>
        <button 
          :class="{ active: currentTab === 'json' }" 
          @click="currentTab = 'json'">
          JSON Export
        </button>
      </div>

      <!-- TAB 1: PERSONA -->
      <div v-show="currentTab === 'persona'" class="tab-pane">
        
        <div class="row"><label>Nom</label><input type="text" v-model="data.persona.nom" /></div>
        <div class="row"><label>Occupation</label><input type="text" v-model="data.persona.metier" /></div>
        <div class="row"><label>Localisation</label><input type="text" v-model="data.persona.localisation" /></div>
      

        <div class="field-group">
           <label>Caractéristiques</label>
           <textarea v-model="data.persona.caracteristiques" rows="2"></textarea>
        </div>

        <div class="field-group">
           <label>Phrase clé</label>
           <input type="text" v-model="data.persona.phrase_cle" />
        </div>

        <div class="field-group">
           <label>Maturité digitale ({{ data.persona.maturite_digitale }}/5)</label>
           <div class="rating-group">
               <button 
                   v-for="n in 6" 
                   :key="'rating-' + (n - 1)"
                   class="rating-btn"
                   :class="{ active: data.persona.maturite_digitale === (n - 1) }"
                   @click="data.persona.maturite_digitale = (n - 1)"
                   type="button"
               >
                   {{ n - 1 }}
               </button>
           </div>
        </div>

        
        <div class="row">
            <label>Bio</label>
            <textarea v-model="data.persona.bio" rows="6"></textarea>
        </div>
        <div class="row">
            <label>Insights</label>
            <div v-for="(insight, index) in data.persona.insights" :key="index" class="insight-row">
                <input type="text" v-model="data.persona.insights[index]" />
                <button @click="removeInsight(Number (index))" class="btn-sm">🗑️</button>
            </div>
            <button @click="addInsight" class="btn-secondary">+ Ajouter</button>
        </div>
        <div class="row">
          <label>Inquiétudes & Frustrations</label>
          <textarea v-model="data.persona.inquietudes" rows="4"></textarea>
        </div>
        <div class="row">
          <label>Besoins</label>
          <textarea v-model="data.persona.besoins" rows="4"></textarea>
        </div>
        
      </div>

      <!-- TAB 2: JOURNEY MAP -->
      <div v-show="currentTab === 'journey'" class="tab-pane">
        <div class="journey-controls">
            <button @click="addStep" class="btn-primary">+ Ajouter une étape</button>
        </div>

        <div class="table-wrapper">
            <table class="journey-table">
                <thead>
                    <!-- LIGNE 1 : NOMS DES ÉTAPES -->
                    <tr>
                        <th class="row-header-cell sticky-col">Étapes</th>
                        <th v-for="(step, index) in data.journey.steps" :key="'head-'+index" >
                            <div class="header-content">
                                <textarea v-model="step.name" class="title-input" rows="2"></textarea>
                                <button @click="removeStep(index)" class="btn-remove">×</button>
                            </div>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <!-- LIGNE 2 : ACTIONS -->
                    <tr>
                        <td class="row-header-cell sticky-col">Actions</td>
                        <td v-for="(step, index) in data.journey.steps" :key="'act-'+index">
                            <div class="item-list">
                                <div v-for="(action, i) in step.actions" :key="i" class="item-box">
                                    <textarea v-model="action.description" ></textarea>
                                    <button @click="removeAction(step, i)" class="btn-x">×</button>
                                </div>
                                <button @click="addAction(step)" class="btn-add-item">+ Action</button>
                            </div>
                        </td>
                    </tr>

                    <!-- LIGNE 3 : CANAUX -->
                    <tr>
                        <td class="row-header-cell sticky-col">Canaux</td>
                        <td v-for="(step, index) in data.journey.steps" :key="'can-'+index">
                            <div class="icon-picker-list">
                                <div v-for="(canal, i) in step.channels" :key="i" class="icon-box">
                                    <select v-model="step.channels[i]" class="icon-select">
                                        <option
                                          v-for="option in canauxOptions" 
                                          :key="option.value" 
                                          :value="option.value"
                                          :disabled="step.channels.includes(option.value) && step.channels[i] !== option.value"
                                          >
                                            {{ option.label }}
                                            {{ (step.channels.includes(option.value) && step.channels[i] !== option.value) ? '(Déjà pris)' : '' }}
                                        </option>
                                    </select>
                                    <button @click="removeSimpleItem(step.channels, i)" class="btn-x">×</button>
                                </div>
                                <button v-if="step.channels.length != canauxOptions.length" @click="addSimpleItem(step.channels)" class="btn-add-item">+ Canal</button>
                            </div>
                        </td>
                    </tr>

                    <!-- LIGNE 4 : EMOTIONS -->
                    <tr class="emotion-row">
                        <td class="row-header-cell sticky-col">Émotions</td>
                        
                        <!-- UNE SEULE CELLULE QUI PREND TOUTE LA LARGEUR -->
                        <td :colspan="data.journey.steps.length" class="graph-cell-unified">
                            
                            <div class="emotion-graph-container">
                                <!-- UN SEUL GRAND SVG -->
                                <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                                    
                                    <!-- 1. GRILLE DE FOND (Globale) -->
                                    <line x1="0" y1="50" x2="100" y2="50" stroke="#999" stroke-width="0.5" vector-effect="non-scaling-stroke" />
                                    
                                    <!-- Lignes horizontales -->
                                    <g v-for="n in 6" :key="'grid-'+n">
                                        <line x1="0" :y1="mapEmotionToY(n)" x2="100" :y2="mapEmotionToY(n)" stroke="#eee" stroke-width="0.5" vector-effect="non-scaling-stroke" />
                                        <line x1="0" :y1="mapEmotionToY(-n)" x2="100" :y2="mapEmotionToY(-n)" stroke="#eee" stroke-width="0.5" vector-effect="non-scaling-stroke" />
                                    </g>

                                    <!-- 2. SÉPARATEURS D'ÉTAPES VERTICAUX -->
                                    <g v-for="(step, sIdx) in data.journey.steps" :key="'sep-'+sIdx">
                                        <!-- Ligne à la fin de chaque étape -->
                                        <line 
                                            :x1="getStepEndX(sIdx)" 
                                            y1="0" 
                                            :x2="getStepEndX(sIdx)" 
                                            y2="100" 
                                            stroke="#ccc" 
                                            stroke-width="1" 
                                            stroke-dasharray="4"
                                            vector-effect="non-scaling-stroke"
                                        />
                                    </g>

                                    <!-- 3. GUIDES D'ACTIONS (Petites lignes verticales pour chaque point) -->
                                    <g v-for="(point, pIdx) in getAllPoints()" :key="'guide-'+pIdx">
                                        <line 
                                            :x1="point.x" 
                                            y1="0" 
                                            :x2="point.x" 
                                            y2="100" 
                                            stroke="#f5f5f5" 
                                            stroke-width="1" 
                                            vector-effect="non-scaling-stroke"
                                        />
                                    </g>

                                    <!-- 4. LA COURBE UNIQUE (Path) -->
                                    <path 
                                        :d="getGlobalSmoothPath()" 
                                        fill="none" 
                                        stroke="#1976d2" 
                                        stroke-width="2"
                                        stroke-linejoin="round"
                                        stroke-linecap="round"
                                        vector-effect="non-scaling-stroke" 
                                    />
                                    <g v-for="(point, pIdx) in getAllPoints()" :key="'link-'+pIdx">
                                        <line 
                                            v-if="point.actionRef.emotion_text"
                                            :x1="point.x" 
                                            :y1="point.y" 
                                            :x2="getSvgLineCoords(point).x2" 
                                            :y2="getSvgLineCoords(point).y2" 
                                            stroke="#1976d2" 
                                            stroke-width="1"
                                            stroke-dasharray="2"
                                            opacity="0.6"
                                        />
                                    </g>
                                </svg>
                                <!-- 5. LES POINTS-->
                                <!-- en html parce que en svg les points sont itérés-->

                                <template v-for="(point, pIdx) in getAllPoints()" :key="'pt-group-'+pIdx">
                                    
                                    <!-- A. LE POINT CIBLE (HITBOX) -->
                                    <div
                                        class="graph-point"
                                        :class="{
                                            'pos': point.val > 0, 
                                            'neg': point.val < 0,
                                            'is-linked': !!point.actionRef.emotion_text,
                                            'hover-target': isDragging
                                        }"
                                        :style="{ left: point.x + '%', top: point.y + '%' }"
                                        :data-step-index="point.stepIndex"
                                        :data-action-index="point.actionIndex"
                                    ></div>

                                    <div 
                                        v-if="point.actionRef.emotion_text" 
                                        class="linked-label"
                                        :class="{ 'minimized': point.actionRef.isMinimized }"
                                        :style="{ 
                                            left: point.x + '%', 
                                            top: point.y + '%',
                                            transform: `translate(calc(-50% + ${point.actionRef.labelOffset?.x || 0}px), calc(-50% + ${point.actionRef.labelOffset?.y || -50}px))`
                                        }"
                                        @mousedown="startLabelDrag($event, point.actionRef)"
                                        @touchstart="startLabelDrag($event, point.actionRef)"
                                    >
                                        <div class="label-content">
                                            <div class="text-area">
                                                <span v-if="!point.actionRef.isMinimized">{{ point.actionRef.emotion_text }}</span>
                                                <span v-else class="minimized-text">...</span>
                                            </div>
                                            <div class="label-actions">
                                                <button class="btn-mini" @click.stop="point.actionRef.isMinimized = !point.actionRef.isMinimized">
                                                    {{ point.actionRef.isMinimized ? '+' : '-' }}
                                                </button>
                                                <button class="btn-detach" @click.stop="detachTextFromPoint(point.actionRef)">×</button>
                                            </div>
                                        </div>
                                    </div>

                                </template>

                                <!-- 6. LES SLIDERS (SUPERPOSÉS EN ABSOLU) -->
                                <!-- On itère sur tous les points globaux pour placer les sliders -->
                                <div 
                                    v-for="(point, pIdx) in getAllPoints()" 
                                    :key="'slider-'+pIdx"
                                    class="slider-wrapper"
                                    :class="{'slider-disabled': isDragging}"
                                    :style="{ left: point.x + '%', transform: 'translateX(-50%)' }"
                                >
                                    <input 
                                        type="range" 
                                        v-model.number="point.actionRef.emotion" 
                                        min="-6" 
                                        max="6" 
                                        step="1" 
                                        class="vertical-range"
                                        :disabled="isDragging"
                                    >
                                     <div class="value-bubble" :style="{ top: point.y + '%' }">
                                        {{ point.val }}
                                    </div>
                                </div>
                            </div>
                        </td>
                    </tr>

                    <!-- LIGNE 5 : CHALLENGES -->
                    <tr>
                        <td class="row-header-cell sticky-col">Challenges</td>
                        <td v-for="(step, index) in data.journey.steps" :key="'chall-'+index">
                            <div class="item-list">
                                <div v-for="(chal, i) in step.challenges" :key="i" class="item-box error-box">
                                    <textarea v-model="step.challenges[i]" rows="3"></textarea>
                                    <button @click="removeSimpleItem(step.challenges, i)" class="btn-x">×</button>
                                </div>
                                <button @click="addSimpleItem(step.challenges)" class="btn-add-item red">+ Challenge</button>
                            </div>                        
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
      </div>
        <div 
          v-if="data.journey.emotion_gen && data.journey.emotion_gen.length > 0 && currentTab === 'journey'"
          class="floating-panel"
          :style="{ top: panelPos.y + 'px', left: panelPos.x + 'px' }"
          ref="panelRef"
      >
        <!-- Barre de titre (Zone pour déplacer le panneau) -->
        <div 
            class="panel-header"
            @mousedown="startPanelDrag"
            @touchstart="startPanelDrag"
        >
            <span>Émotions à placer ({{ data.journey.emotion_gen.length }})</span>
            <button class="minimize-btn" @click="isPanelMinimized = !isPanelMinimized">
                {{ isPanelMinimized ? 'Show' : '_' }}
            </button>
        </div>

        <!-- Corps du panneau (Liste des items) -->
        <div v-show="!isPanelMinimized" class="panel-body">
            <div 
                v-for="(text, idx) in data.journey.emotion_gen" 
                :key="'gen-'+idx" 
                class="draggable-tag"
                @mousedown.stop.prevent="startDrag($event, text, idx)"
                @touchstart.stop.prevent="startDrag($event, text, idx)"
            >
                {{ text }}
            </div>
            <div v-if="data.journey.emotion_gen.length === 0" class="empty-msg">
                Tout est placé !
            </div>
        </div>
      </div>
      <div 
        v-if="isDragging && dragItem" 
        class="drag-ghost"
        :style="{ left: ghostPos.left + 'px', top: ghostPos.top + 'px' }"
      >
        <!-- On coupe le texte s'il est trop long pour le fantôme -->
        {{ dragItem.text.length > 30 ? dragItem.text.substring(0, 30) + '...' : dragItem.text }}
      </div>
        <!-- TAB 3: JSON OUTPUT -->
        <div v-show="currentTab === 'json'" class="tab-pane modal-overlay">
            <div class="export-header box-card">
                <div class="export-info">
                    <h3>Exportation du projet</h3>
                    <p>Voici le résultat généré à partir de vos modifications.</p>
                </div>
                <div class="export-actions">
                    <button @click="generateJSON" class="btn-secondary">Actualiser</button>
                    <button @click="copyToClipboard" class="btn-secondary">Copier</button>
                    <button @click="downloadJSON" class="btn-primary">Télécharger .json</button>
                </div>
            </div>

            <div class="json-preview-wrapper box-card">
                <pre class="json-code">{{ jsonOutput }}</pre>
            </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { parsePptx } from "../api/api.js"; // Assurez-vous que cette fonction existe
import "../assets/form.css";


interface Action {
    id: string; // Unique ID pour Vue (:key)
    description: string;
    emotion: number;
    emotion_text: string | null;
    labelOffset: { x: number, y: number };
    isMinimized: boolean;
}

interface Step {
    id: string;
    name: string;
    order: number;
    channels: string[]; // Canaux au niveau de l'étape
    challenges: string[]; 
    actions: Action[]; // Tableau d'objets !
}

interface ProjectData {
    persona: {
        nom: string;
        metier: string;
        localisation: string;
        phrase_cle: string;
        bio: string;
        maturite_digitale: number;
        caracteristiques: string[];
        insights: string[];
        besoins: string[];
        inquietudes: string[];
    };
    journey: {
        steps: Step[];
        emotion_gen: string[];
    }
}


const canauxOptions = [
  { value: "desktop", label: "Desktop" },
  { value: "mobile", label: "Mobile" },
  { value: "tablet", label: "Tablette" }
];
const data = ref<ProjectData | null>(null);
const error = ref("");
const currentTab = ref("persona");
watch(currentTab, (newTab) => {
    if (newTab === 'json') {
        generateJSON();
    }
});
const panelPos = ref({ x: window.innerWidth - 320, y: 100 });
const isPanelDragging = ref(false);
const panelOffset = ref({ x: 0, y: 0 });
const isPanelMinimized = ref(false);

const isDragging = ref(false);
const dragItem = ref<any>(null); 
const ghostPos = ref({ top: 0, left: 0 });

const jsonOutput = ref("");

const draggingLabel = ref<{ 
    action: Action, 
    startX: number, 
    startY: number, 
    startOffsetX: number, 
    startOffsetY: number 
} | null>(null);

function generateJSON() {
    if (!data.value) return;

    // 1. Construction du Persona
    const personaData = {
        name: data.value.persona.nom,
        job: data.value.persona.metier,
        bio: data.value.persona.bio,
        quote: data.value.persona.phrase_cle,
        digital_maturity: data.value.persona.maturite_digitale,
        insights: data.value.persona.insights,
        expectations: data.value.persona.besoins,
        frustrations: data.value.persona.inquietudes
    };

    // 2. Construction de la Journey
    const journeyData = data.value.journey.steps.map((step, index) => {
        return {
            step_order: index + 1,
            step_name: step.name,
            channels: step.channels,     // Canaux globaux de l'étape
            pain_points: step.challenges, // Challenges globaux
            
            // Liste des actions (propres)
            actions: step.actions.map((act, actIdx) => ({
                order: actIdx + 1,
                description: act.description,
                emotion_score: act.emotion,       // La note (-6 à +6)
                emotion_text: act.emotion_text    // Le texte droppé (null si aucun)
            }))
        };
    });

    // 3. Assemblage final
    const finalObj = {
        meta: {
            generated_at: new Date().toISOString(),
            app_version: "1.0"
        },
        persona: personaData,
        journey: journeyData
    };

    // 4. Formatage et Affichage
    jsonOutput.value = JSON.stringify(finalObj, null, 2); // 2 espaces d'indentation
}

function downloadJSON() {
    // Création d'un fichier virtuel pour le téléchargement
    const blob = new Blob([jsonOutput.value], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `persona_export_${new Date().getTime()}.json`;
    link.click();
    URL.revokeObjectURL(url);
}

function copyToClipboard() {
    navigator.clipboard.writeText(jsonOutput.value);
    alert("JSON copié dans le presse-papier !");
}

function startLabelDrag(event: MouseEvent | TouchEvent, action: Action) {
    // Ne pas draguer si on clique sur les boutons (+, -, x)
    if ((event.target as HTMLElement).tagName === 'BUTTON') return;
    
    event.stopPropagation();
    event.preventDefault(); // Empêche la sélection de texte

    // Initialise l'offset s'il n'existe pas encore
    if (!action.labelOffset) {
        action.labelOffset = { x: 0, y: -50 };
    }

    const clientX = (event as any).touches ? (event as any).touches[0].clientX : (event as MouseEvent).clientX;
    const clientY = (event as any).touches ? (event as any).touches[0].clientY : (event as MouseEvent).clientY;

    // Enregistre l'état de départ
    draggingLabel.value = {
        action,
        startX: clientX,
        startY: clientY,
        startOffsetX: action.labelOffset.x,
        startOffsetY: action.labelOffset.y
    };

    window.addEventListener('mousemove', onLabelMove);
    window.addEventListener('touchmove', onLabelMove, { passive: false });
    window.addEventListener('mouseup', endLabelDrag);
    window.addEventListener('touchend', endLabelDrag);
}

function onLabelMove(event: MouseEvent | TouchEvent) {
    if (!draggingLabel.value) return;
    event.preventDefault();

    const clientX = (event as any).touches ? (event as any).touches[0].clientX : (event as MouseEvent).clientX;
    const clientY = (event as any).touches ? (event as any).touches[0].clientY : (event as MouseEvent).clientY;

    // Calcule la distance parcourue par la souris
    const deltaX = clientX - draggingLabel.value.startX;
    const deltaY = clientY - draggingLabel.value.startY;

    // Applique le déplacement au label
    draggingLabel.value.action.labelOffset.x = draggingLabel.value.startOffsetX + deltaX;
    draggingLabel.value.action.labelOffset.y = draggingLabel.value.startOffsetY + deltaY;
}

function endLabelDrag() {
    draggingLabel.value = null;
    window.removeEventListener('mousemove', onLabelMove);
    window.removeEventListener('touchmove', onLabelMove);
    window.removeEventListener('mouseup', endLabelDrag);
    window.removeEventListener('touchend', endLabelDrag);
}

// Fonction pour que la ligne SVG suive le label
function getSvgLineCoords(point: any) {
    const action = point.actionRef;
    if (!action.labelOffset) action.labelOffset = { x: 0, y: -50 };
    
    // Le SVG est en % (0 à 100), le label est en pixels.
    // On convertit approximativement (1px = 0.1% en X, 1px = 0.3% en Y)
    return {
        x2: point.x + (action.labelOffset.x * 0.1),
        y2: point.y + (action.labelOffset.y * 0.3)
    };
}

function onDragEnd(event: MouseEvent | TouchEvent) {
    if (!isDragging.value) return;

    // 1. Coordonnées de la souris / du doigt
    const evt = (event as any).changedTouches ? (event as any).changedTouches[0] : event;
    const clientX = evt.clientX;
    const clientY = evt.clientY;

    // 2. Masquer fantôme (Standard)
    const ghostEl = document.querySelector('.drag-ghost') as HTMLElement;
    if (ghostEl) ghostEl.style.display = 'none';

    // 3. ESSAI 1 : Hit Test Standard
    let elementBelow = document.elementFromPoint(clientX, clientY);
    let pointElement = elementBelow?.closest('.graph-point');

    // 4. ESSAI 2 : RECHERCHE GÉOMÉTRIQUE (Si le Hit Test a échoué)
    // C'est ce qui va sauver votre Drag & Drop
    if (!pointElement) {
        const points = document.querySelectorAll('.graph-point');
        let minDistance = 40; // Tolérance de 40px autour du point (assez large)
        let closestArg = null;

        points.forEach((el) => {
            const rect = el.getBoundingClientRect();
            // Centre du point
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;

            // Distance Pythagore
            const dist = Math.sqrt(
                Math.pow(clientX - centerX, 2) + Math.pow(clientY - centerY, 2)
            );

            if (dist < minDistance) {
                minDistance = dist;
                closestArg = el;
            }
        });

        if (closestArg) {
            console.log("Point trouvé par proximité (Distance:", minDistance.toFixed(1), "px)");
            pointElement = closestArg;
        }
    }

    // 5. Appliquer Drop
    if (pointElement) {
        // Lecture sécurisée des attributs
        const sIdxStr = pointElement.getAttribute('data-step-index');
        const aIdxStr = pointElement.getAttribute('data-action-index');

        if (sIdxStr !== null && aIdxStr !== null) {
            applyDrop(parseInt(sIdxStr, 10), parseInt(aIdxStr, 10));
        }
    } else {
        console.warn("Drop manqué : Aucun point trouvé sous la souris");
    }

    // 6. Reset & Nettoyage
    // IMPORTANT : On retire la classe après le calcul
    document.body.classList.remove('dragging-mode');
    
    if (ghostEl) ghostEl.style.display = 'block'; // Reset display pour le prochain drag

    isDragging.value = false;
    dragItem.value = null;
    
    document.removeEventListener('mousemove', onDragMove);
    document.removeEventListener('touchmove', onDragMove);
    document.removeEventListener('mouseup', onDragEnd);
    document.removeEventListener('touchend', onDragEnd);
}

// --- EFFECTUER L'ATTACHEMENT ---
function applyDrop(stepIndex: number, actionIndex: number) {
    console.log("Applying drop to step", stepIndex, "action", actionIndex);
    const step = data.value.journey.steps[stepIndex];
    if (!step) return;
    const action = step.actions[actionIndex];
    if (!action) return;
    
    if (action.emotion_text){
        data.value.journey.emotion_gen.push(action.emotion_text);
    }
    action.emotion_text = dragItem.value.text;

    if (typeof dragItem.value.index === 'number') {
        // Retirer de la liste globale
        data.value.journey.emotion_gen.splice(dragItem.value.index, 1);
    }
}

// --- HELPERS ---

function detachTextFromPoint(actionRef: Action) {
    if (actionRef.emotion_text && data.value) {
        data.value.journey.emotion_gen.push(actionRef.emotion_text);
        actionRef.emotion_text = null;
    }
}

function startDrag(event: MouseEvent | TouchEvent, text: string, index: number) {
    event.stopPropagation();
    
    // Ajouter la classe au body pour changer le CSS
    document.body.classList.add('dragging-mode');

    // Gestion events souris/touch unifiée
    const evt = (event as any).touches ? (event as any).touches[0] : event;
    const clientX = evt.clientX;
    const clientY = evt.clientY;

    if (event.type === 'mousedown') event.preventDefault(); // Empêche sélection texte

    isDragging.value = true;
    dragItem.value = { text, index };
    
    updateGhostPos(clientX, clientY);

    document.addEventListener('mousemove', onDragMove, { passive: false });
    document.addEventListener('touchmove', onDragMove, { passive: false });
    document.addEventListener('mouseup', onDragEnd);
    document.addEventListener('touchend', onDragEnd);
}

function onDragMove(event: MouseEvent | TouchEvent) {
    if (!isDragging.value) return;
    // Important : Empêcher le scroll de la page ou du panneau pendant le drag
    event.preventDefault(); 
    
    const clientX = (event as TouchEvent).touches ? (event as TouchEvent).touches[0].clientX : (event as MouseEvent).clientX;
    const clientY = (event as TouchEvent).touches ? (event as TouchEvent).touches[0].clientY : (event as MouseEvent).clientY;

    updateGhostPos(clientX, clientY);
}

function updateGhostPos(x: number, y: number) {
    // On centre visuellement le fantôme ou on le décale un peu pour voir ce qu'il y a dessous
    // Position FIXED requiert des coordonnées viewport (clientX/Y)
    ghostPos.value = { 
        left: x + 15, // Décalage pour ne pas être pile sous la souris (et permettre le elementFromPoint)
        top: y + 15 
    };
}

function startPanelDrag(e: MouseEvent | TouchEvent) {
    // On ignore si on clique sur le bouton réduire
    if ((e.target as HTMLElement).tagName === 'BUTTON') return;
    
    e.preventDefault();
    isPanelDragging.value = true;
    
    const clientX = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientX : (e as MouseEvent).clientX;
    const clientY = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientY : (e as MouseEvent).clientY;

    // Calculer l'offset pour que le panneau ne saute pas sous la souris
    panelOffset.value = {
        x: clientX - panelPos.value.x,
        y: clientY - panelPos.value.y
    };

    window.addEventListener('mousemove', onPanelMove);
    window.addEventListener('touchmove', onPanelMove, { passive: false });
    window.addEventListener('mouseup', endPanelDrag);
    window.addEventListener('touchend', endPanelDrag);
}

function onPanelMove(e: MouseEvent | TouchEvent) {
    if (!isPanelDragging.value) return;
    e.preventDefault();

    const clientX = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientX : (e as MouseEvent).clientX;
    const clientY = (e as TouchEvent).touches ? (e as TouchEvent).touches[0].clientY : (e as MouseEvent).clientY;

    // Nouvelle position
    let newX = clientX - panelOffset.value.x;
    let newY = clientY - panelOffset.value.y;

    // (Optionnel) Garder dans l'écran
    newX = Math.max(0, Math.min(window.innerWidth - 300, newX));
    newY = Math.max(0, Math.min(window.innerHeight - 50, newY));

    panelPos.value = { x: newX, y: newY };
}

function endPanelDrag() {
    isPanelDragging.value = false;
    window.removeEventListener('mousemove', onPanelMove);
    window.removeEventListener('touchmove', onPanelMove);
    window.removeEventListener('mouseup', endPanelDrag);
    window.removeEventListener('touchend', endPanelDrag);
}

function getAllPoints() {
    if (!data.value?.journey?.steps) return [];
    
    const steps = data.value.journey.steps;
    const totalSteps = steps.length;
    if (totalSteps === 0) return [];
    
    const allPoints: any[] = [];
    const stepWidth = 100 / totalSteps;

    steps.forEach((step: any, sIdx: number) => {
        const actionCount = step.actions.length;
        
        step.actions.forEach((action: Action, aIdx: number) => {
            // Uniquement si l'action correspondante existe
            if (aIdx < actionCount) {
                const localRatio = (aIdx + 1) / (actionCount + 1);
                const globalX = (sIdx * stepWidth) + (stepWidth * localRatio);
                
                allPoints.push({
                    x: globalX,
                    y: mapEmotionToY(action.emotion),
                    val: action.emotion,
                    stepRef: step,
                    actionRef: action,
                    stepIndex: sIdx,
                    actionIndex: aIdx
                });
            }
        });
    });
    
    return allPoints;
}
// Génère le <path> SVG qui relie TOUS les points de gauche à droite
function getGlobalSmoothPath() {
    const points = getAllPoints();
    if (points.length < 2) return "";
    // M = start
    let d = `M ${points[0].x} ${points[0].y}`;
    // Courbe spline catmull-rom simplifiée (Bezier cubique)
    for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[i];
        const p1 = points[i + 1];
        // Control points
        const cp1x = p0.x + (p1.x - p0.x) / 2;
        const cp1y = p0.y;
        const cp2x = p0.x + (p1.x - p0.x) / 2;
        const cp2y = p1.y;
        d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p1.x} ${p1.y}`;
    }
    return d;
}

function getStepEndX(stepIndex: number) {
    const steps = data.value?.journey.steps;
    if (steps.length === 0) return 0;
    const stepWidth = 100 / steps.length;
    return (stepIndex + 1) * stepWidth;
}

async function onFile(e: Event) {
  error.value = "";
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  try {
    const responseByAPI = await parsePptx(file);
    
    if (responseByAPI){
        console.log("Données brutes reçues de l'API:", responseByAPI);
        data.value = transformRawData(responseByAPI);
        console.log("Données transformées pour l'UI:", data.value);
    }
    


  } catch (err: any) {
    error.value = "Erreur parsing: " + err.message;
  }
}

function mapEmotionToY(score: number) {
    const minVal = -6; 
    const maxVal = 6;
    const percent = (score - minVal) / (maxVal - minVal);
    return 90 - (percent * 80);
}

// Logic Persona
function addInsight() { data.value?.persona.insights.push(""); }
function removeInsight(idx: number) { data.value?.persona.insights.splice(idx, 1); }

// Logic Journey
function addStep() {
    if (!data.value) return;
    data.value.journey.steps.push({
        id: generateId(),
        name: "Nouvelle étape",
        order: data.value.journey.steps.length + 1,
        actions: [],
        channels: [],
        challenges: []        
    });
}
function removeStep(idx: number) {
    data.value?.journey.steps.splice(idx, 1);
}

function addSimpleItem(list: string[]) { list.push(""); }
function removeSimpleItem(list: string[], idx: number) { list.splice(idx, 1); }

function addAction(step: Step){
    step.actions.push({
        id: generateId(),
        description: "",
        emotion: 0,
        emotion_text: null,
        labelOffset: { x: 0, y: -50 },
        isMinimized: false
    });
}
function removeAction(step: Step, idx: number){
    const action = step.actions[idx];
    if (action.emotion_text) {
        data.value.journey.emotion_gen.push(action.emotion_text);
    }
    step.actions.splice(idx, 1);
}

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2, 5);

// Fonction de transformation : Raw Data -> Clean Data
function transformRawData(rawData: any): ProjectData {
    
    // 1. Nettoyage Persona (Valeurs par défaut)
    const cleanPersona = {
        nom: rawData.persona?.nom || "Nouveau Persona",
        metier: rawData.persona?.metier || "",
        localisation: rawData.persona?.localisation || "",
        phrase_cle: rawData.persona?.phrase_cle || "",
        bio: rawData.persona?.bio || "",
        maturite_digitale: rawData.persona?.maturite_digitale,
        caracteristiques: rawData.persona?.caracteristiques || [],
        insights: rawData.persona?.insights || [],
        besoins: rawData.persona?.besoins || [],
        inquietudes: rawData.persona?.inquietudes || [],
    };

    // 2. Nettoyage Journey (Conversion en Objets)
    const cleanSteps: Step[] = (rawData.journey?.steps || []).map((rawStep: any, index: number) => {
        
        // On transforme les tableaux parallèles (actions/emotions) en liste d'objets Action
        const actionsList: Action[] = [];
        
        // On suppose que rawStep.actions est la source de vérité pour le nombre d'actions
        const rawActions = rawStep.actions || [];
        
        rawActions.forEach((desc: string, actIdx: number) => {
            actionsList.push({
                id: generateId(), // ID unique vital
                description: desc || "",
                // Si rawStep.emotions existe, on prend la valeur, sinon 0
                emotion: 0,
                // Si rawStep.emotion_texts existe, on prend le texte, sinon null
                emotion_text: null,
                labelOffset: { x: 0, y: -50 },
                isMinimized: false
            });
        });

        return {
            id: generateId(),
            name: rawStep.name || `Étape ${index + 1}`,
            order: index + 1,
            // Canaux : On prend le tableau brut s'il existe, sinon vide
            channels: Array.isArray(rawStep.channels) ? rawStep.channels : [], 
            challenges: Array.isArray(rawStep.challenges) ? rawStep.challenges : [],
            actions: actionsList
        };
    });

    return {
        persona: cleanPersona,
        journey: {
            steps: cleanSteps,
            emotion_gen: rawData.journey?.emotion_gen || []
        }
    };
}
</script>
