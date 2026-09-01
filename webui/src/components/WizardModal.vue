<template>
  <div class="modal-overlay" v-if="show" data-testid="wizard-modal">
    <div class="modal-content">
      <div class="wizard-header">
        <h2>Model Setup Wizard</h2>
        <button class="btn btn--ghost" @click="skipWizard" data-testid="skip-link">Skip</button>
      </div>

      <!-- Step 1: Model Tier -->
      <div v-if="step === 1" class="wizard-step" data-testid="wizard-step-1">
        <h3>Select Model Tier</h3>
        <p class="wizard-hint">Choose the complexity level for your model. Higher tiers enable more features but require more VRAM.</p>
        <div class="tier-grid">
          <ModelTierCard
            v-for="t in tierList"
            :key="t.tier"
            :tier="t.tier"
            :label="t.label"
            :description="t.description"
            :icon="t.icon"
            :feasibility="tierFeasibility[t.tier]"
            :selected="selectedTier === t.tier"
            :disabled="!tierFeasibility[t.tier]?.fits"
            @select="selectTier"
          />
        </div>
        <div class="wizard-actions">
          <button class="btn btn--primary" :disabled="!selectedTier" @click="step = 2" data-testid="wizard-next-1">Next</button>
        </div>
      </div>

      <!-- Step 2: Quality / Preset -->
      <div v-if="step === 2" class="wizard-step" data-testid="wizard-step-2">
        <h3>Select Quality</h3>
        <p class="wizard-hint">Choose the training speed / quality trade-off for your <strong>{{ tierLabel(selectedTier) }}</strong> model.</p>
        <div class="quality-grid">
          <div
            v-for="q in qualityOptions"
            :key="q.key"
            class="quality-card"
            :class="{ 'quality-card--selected': selectedQuality === q.key }"
            :data-testid="`quality-${q.key}`"
            @click="selectedQuality = q.key"
          >
            <div class="quality-card-label">{{ q.label }}</div>
            <div class="quality-card-desc">{{ q.desc }}</div>
            <div class="quality-card-vram">~{{ (q.vramFactor * currentTierEstimate).toFixed(1) }} GB</div>
          </div>
        </div>
        <div class="wizard-actions">
          <button class="btn btn--ghost" @click="step = 1">Back</button>
          <button class="btn btn--primary" :disabled="!selectedQuality" @click="step = 3" data-testid="wizard-next-2">Next</button>
        </div>
      </div>

      <!-- Step 3: Target Mode -->
      <div v-if="step === 3" class="wizard-step" data-testid="wizard-step-3">
        <h3>Select Target Mode</h3>
        <p class="wizard-hint">Choose how you intend to use the trained model.</p>
        <div class="mode-options">
          <label class="mode-option" :class="{ 'mode-option--selected': selectedMode === 'offline' }">
            <input type="radio" v-model="selectedMode" value="offline" data-testid="mode-offline" />
            <div>
              <strong>Offline / Studio</strong>
              <p>Best quality, higher latency. Export formats: WAV, TorchScript, ONNX, Neutone.</p>
            </div>
          </label>
          <label class="mode-option" :class="{ 'mode-option--selected': selectedMode === 'realtime' }">
            <input type="radio" v-model="selectedMode" value="realtime" data-testid="mode-realtime" />
            <div>
              <strong>Realtime / Low-Latency</strong>
              <p>Optimized for real-time inference. Export formats: Neutone, TorchScript.</p>
            </div>
          </label>
        </div>
        <div class="wizard-actions">
          <button class="btn btn--ghost" @click="step = 2">Back</button>
          <button class="btn btn--primary" @click="completeWizard" data-testid="wizard-start">Start Training Setup ✓</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useModelConfigStore } from '../stores/modelConfig.js'
import { tierLabel, tierIcon, TIER_META, TIER_ORDER } from '../utils/tierColors.js'
import ModelTierCard from './ModelTierCard.vue'

const store = useModelConfigStore()
const apiClient = inject('apiClient')

const show = ref(true)
const step = ref(1)
const selectedTier = ref(null)
const selectedQuality = ref(null)
const selectedMode = ref('offline')

const qualityOptions = [
  { key: 'FAST', label: 'FAST', desc: '0.25x size, max speed', vramFactor: 0.25 },
  { key: 'NORMAL', label: 'NORMAL', desc: '0.50x size, balanced', vramFactor: 0.5 },
  { key: 'QUALITY', label: 'QUALITY', desc: '1.0x size, best quality', vramFactor: 1.0 },
]

const tierList = TIER_ORDER.map(t => ({
  tier: t,
  label: TIER_META[t].label,
  description: getTierDesc(t),
  icon: TIER_META[t].icon,
}))

const tierFeasibility = computed(() => {
  return store.gpuFeasibility?.tier_feasibility ?? {}
})

const currentTierEstimate = computed(() => {
  if (!selectedTier.value) return 2.2
  return tierFeasibility.value[selectedTier.value]?.estimated_gb ?? 2.2
})

function getTierDesc(tier) {
  const descs = {
    standard: 'Core DDSP: harmonic + filtered noise + reverb. Best for clean speech.',
    component: 'Adds component mixer: harmonics vs noise balance sliders.',
    hacks: 'Unlocks DDSP variant hacks: waveform, FM, phase distortion, LFO, wavetable.',
    engine: 'Alternative synth engines: sinusoidal, comb-subtractive, NEWT.',
    advanced: 'PolyDDSP, latent space, voice conversion. Full power.',
  }
  return descs[tier] ?? ''
}

function selectTier(tier) {
  selectedTier.value = tier
}

function skipWizard() {
  store.setTierFromWizard('standard', null, 'offline')
  show.value = false
}

function completeWizard() {
  store.setTierFromWizard(selectedTier.value, selectedQuality.value, selectedMode.value)
  show.value = false
}

onMounted(async () => {
  if (apiClient && !store.gpuFeasibility) {
    await store.checkFeasibility(apiClient)
  }
})
</script>

<style scoped>
.wizard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}
.wizard-header h2 {
  font-size: 1.1rem;
}
.wizard-hint {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-4);
}
.tier-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}
.wizard-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  margin-top: var(--space-6);
}
.wizard-step {
  min-height: 200px;
}
.quality-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}
.quality-card {
  padding: var(--space-4);
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: center;
  transition: border-color var(--transition-fast);
}
.quality-card:hover {
  border-color: var(--text-muted);
}
.quality-card--selected {
  border-color: var(--accent);
  box-shadow: var(--shadow-glow);
}
.quality-card-label {
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: var(--space-1);
}
.quality-card-desc {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}
.quality-card-vram {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}
.mode-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.mode-option {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--bg-tertiary);
  border: 2px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}
.mode-option:hover {
  border-color: var(--text-muted);
}
.mode-option--selected {
  border-color: var(--accent);
}
.mode-option input[type="radio"] {
  margin-top: 3px;
}
.mode-option strong {
  display: block;
  margin-bottom: var(--space-1);
}
.mode-option p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
}
</style>