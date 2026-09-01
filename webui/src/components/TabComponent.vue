<template>
  <div class="tab-component" data-testid="tab-component">
    <div class="form-group">
      <label class="form-label">Number of Harmonics ({{ store.componentParams.n_harmonics }})</label>
      <input class="form-input" type="range" :min="bounds.n_harmonics_min ?? 20" :max="bounds.n_harmonics_max ?? 120" v-model.number="store.componentParams.n_harmonics" data-testid="n-harmonics" />
    </div>
    <div class="form-group">
      <label class="form-label">Number of Filter Banks ({{ store.componentParams.n_filter_banks }})</label>
      <input class="form-input" type="range" :min="bounds.n_filter_banks_min ?? 16" :max="bounds.n_filter_banks_max ?? 64" v-model.number="store.componentParams.n_filter_banks" data-testid="n-filter-banks" />
    </div>
    <RouterLink to="/experimental/mixer" class="btn btn--ghost">Open Component Mixer →</RouterLink>
  </div>
</template>

<script setup>
import { useModelConfigStore } from '../stores/modelConfig.js'

const store = useModelConfigStore()

const bounds = {
  n_harmonics_min: 20, n_harmonics_max: 120,
  n_filter_banks_min: 16, n_filter_banks_max: 64,
}
</script>

<style scoped>
.tab-component { display: flex; flex-direction: column; gap: var(--space-3); }
</style>