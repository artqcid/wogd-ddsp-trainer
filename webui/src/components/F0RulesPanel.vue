<script setup>
import { ref } from 'vue'

const emit = defineEmits(['apply'])

const selectedRule = ref('quantize')
const scaleType = ref('chromatic')
const baseFreq = ref(220)
const noiseStd = ref(50)
const noiseProb = ref(0.1)
const pivotFreq = ref(440)

function apply() {
  emit('apply', {
    rule: selectedRule.value,
    params: {
      scale: scaleType.value,
      base_freq: baseFreq.value,
      noise_std: noiseStd.value,
      probability: noiseProb.value,
      pivot_freq: pivotFreq.value,
    }
  })
}
</script>

<template>
  <div class="rules-panel">
    <h3>F0 Transformation Rules</h3>
    <div class="form-group">
      <label for="rule-select">Rule</label>
      <select id="rule-select" v-model="selectedRule" data-testid="rule-select">
        <option value="quantize">Quantize to Scale</option>
        <option value="noise">Inject Noise</option>
        <option value="invert">Invert Pitch</option>
      </select>
    </div>

    <template v-if="selectedRule === 'quantize'">
      <div class="form-group">
        <label for="scale-type">Scale</label>
        <select id="scale-type" v-model="scaleType">
          <option value="chromatic">Chromatic</option>
          <option value="major">Major</option>
          <option value="minor">Minor</option>
          <option value="pentatonic">Pentatonic</option>
        </select>
      </div>
      <div class="form-group">
        <label for="base-freq">Base Freq (Hz)</label>
        <input id="base-freq" type="number" v-model.number="baseFreq" min="20" max="2000" />
      </div>
    </template>

    <template v-if="selectedRule === 'noise'">
      <div class="form-group">
        <label for="noise-std">Noise Std (Hz)</label>
        <input id="noise-std" type="number" v-model.number="noiseStd" min="1" max="500" />
      </div>
      <div class="form-group">
        <label for="noise-prob">Probability</label>
        <input id="noise-prob" type="number" v-model.number="noiseProb" min="0" max="1" step="0.05" />
      </div>
    </template>

    <template v-if="selectedRule === 'invert'">
      <div class="form-group">
        <label for="pivot-freq">Pivot Freq (Hz)</label>
        <input id="pivot-freq" type="number" v-model.number="pivotFreq" min="20" max="2000" />
      </div>
    </template>

    <button class="btn-primary" @click="apply" data-testid="apply-rule">
      Apply Rule
    </button>
  </div>
</template>

<style scoped>
.rules-panel {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.rules-panel h3 {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-primary);
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.form-group label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
.form-group select,
.form-group input {
  padding: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-size: 0.85rem;
}
.btn-primary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
}
.btn-primary:hover {
  background: var(--accent-hover);
}
</style>
