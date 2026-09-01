<template>
  <div class="tab-hacks" data-testid="tab-hacks">
    <div class="form-group">
      <label class="form-label">Waveform</label>
      <select class="form-select" v-model="local.waveform" data-testid="waveform">
        <option value="sin">Sine</option>
        <option value="square">Square</option>
        <option value="saw">Saw</option>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">FM Depth</label>
      <input class="form-input" type="number" step="0.1" min="0" v-model.number="local.fm_depth" data-testid="fm-depth" />
    </div>
    <div class="form-group">
      <label class="form-label">FM Ratio</label>
      <input class="form-input" type="number" step="0.1" min="0.5" v-model.number="local.fm_ratio" data-testid="fm-ratio" />
    </div>
    <div class="form-group">
      <label class="form-label">Phase Distortion (pd_k)</label>
      <input class="form-input" type="number" step="0.05" min="0" max="1" v-model.number="local.pd_k" data-testid="pd-k" />
    </div>
    <div class="form-group">
      <label class="checkbox-label">
        <input type="checkbox" v-model="local.use_lfo" data-testid="use-lfo" /> LFO
      </label>
    </div>
    <div class="form-group" v-if="local.use_lfo">
      <label class="form-label">LFO Frequency</label>
      <input class="form-input" type="number" step="0.1" min="0" v-model.number="local.lfo_freq" data-testid="lfo-freq" />
    </div>
    <div class="form-group">
      <label class="checkbox-label">
        <input type="checkbox" v-model="local.use_trainable_wavetable" data-testid="trainable-wt" /> Trainable Wavetable
      </label>
    </div>
    <div class="form-group">
      <label class="checkbox-label">
        <input type="checkbox" v-model="local.use_angular_cumsum" data-testid="angular-cumsum" /> Angular Cumsum
      </label>
    </div>
    <RouterLink to="/experimental/synth-hacks" class="btn btn--ghost">Open Synth Hacks →</RouterLink>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { useModelConfigStore } from '../stores/modelConfig.js'

const store = useModelConfigStore()

const local = reactive({
  waveform: 'sin',
  fm_depth: 0,
  fm_ratio: 2,
  pd_k: 0,
  use_lfo: false,
  lfo_freq: 0,
  lfo_depth: 0,
  use_trainable_wavetable: false,
  use_angular_cumsum: false,
})

watch(local, (v) => { store.hacksVariant = { ...v } }, { deep: true })
</script>

<style scoped>
.tab-hacks { display: flex; flex-direction: column; gap: var(--space-3); }
.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  cursor: pointer;
}
</style>