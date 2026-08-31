<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  nHarmonics: { type: Number, default: 60 },
  nFilterBanks: { type: Number, default: 32 },
  harmonicGain: { type: Number, default: 1.0 },
  noiseGain: { type: Number, default: 1.0 },
})

const emit = defineEmits(['update'])

const localHarmonics = ref(props.nHarmonics)
const localFilterBanks = ref(props.nFilterBanks)
const localHarmonicGain = ref(props.harmonicGain)
const localNoiseGain = ref(props.noiseGain)

const mixSummary = computed(() => {
  const h = localHarmonics.value
  const f = localFilterBanks.value
  const hg = localHarmonicGain.value
  const ng = localNoiseGain.value
  if (h === 0 && f === 0) return 'Silence'
  if (h === 0) return `Noise only (${f} banks, ${Math.round(ng * 100)}%)`
  if (f === 0) return `Harmonics only (${h} partials, ${Math.round(hg * 100)}%)`
  return `${h} harmonics @ ${Math.round(hg * 100)}% + ${f} filter banks @ ${Math.round(ng * 100)}%`
})

function emitUpdate() {
  emit('update', {
    n_harmonics: localHarmonics.value,
    n_filter_banks: localFilterBanks.value,
    harmonic_gain: localHarmonicGain.value,
    noise_gain: localNoiseGain.value,
  })
}
</script>

<template>
  <div class="component-mixer">
    <h3>Component Mixer</h3>
    <p class="mix-summary">{{ mixSummary }}</p>

    <div class="mixer-row">
      <label>Harmonics</label>
      <input type="range" min="0" max="120" v-model.number="localHarmonics" @input="emitUpdate" />
      <span class="mixer-value">{{ localHarmonics }}</span>
    </div>

    <div class="mixer-row">
      <label>Filter Banks</label>
      <input type="range" min="0" max="64" v-model.number="localFilterBanks" @input="emitUpdate" />
      <span class="mixer-value">{{ localFilterBanks }}</span>
    </div>

    <div class="mixer-row">
      <label>Harmonic Gain</label>
      <input type="range" min="0" max="1" step="0.05" v-model.number="localHarmonicGain" @input="emitUpdate" />
      <span class="mixer-value">{{ Math.round(localHarmonicGain * 100) }}%</span>
    </div>

    <div class="mixer-row">
      <label>Noise Gain</label>
      <input type="range" min="0" max="1" step="0.05" v-model.number="localNoiseGain" @input="emitUpdate" />
      <span class="mixer-value">{{ Math.round(localNoiseGain * 100) }}%</span>
    </div>

    <div class="mixer-actions">
      <button class="btn-small" @click="$emit('apply-config', { n_harmonics: localHarmonics, n_filter_banks: localFilterBanks })">Apply to Config</button>
    </div>
  </div>
</template>

<style scoped>
.component-mixer {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.component-mixer h3 {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-primary);
}
.mix-summary {
  margin: 0;
  font-size: 0.8rem;
  color: var(--accent);
  font-weight: 500;
}
.mixer-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.mixer-row label {
  width: 100px;
  font-size: 0.8rem;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.mixer-row input[type="range"] {
  flex: 1;
  accent-color: var(--accent);
}
.mixer-value {
  width: 50px;
  text-align: right;
  font-size: 0.8rem;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.mixer-actions {
  margin-top: 0.5rem;
}
.btn-small {
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  border: 1px solid var(--accent);
  border-radius: 4px;
  background: transparent;
  color: var(--accent);
  cursor: pointer;
}
.btn-small:hover {
  background: var(--accent);
  color: #fff;
}
</style>
