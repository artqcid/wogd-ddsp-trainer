<script setup>
import { inject, ref } from 'vue'

const apiClient = inject('apiClient')

const models = ref([])
const selectedModel = ref('')
const latentDim = ref(32)
const zValues = ref([])
const audioUrl = ref(null)
const loading = ref(false)

async function loadModels() {
  const data = await apiClient.listModels()
  models.value = data || []
}
loadModels()

function initZ() {
  zValues.value = Array.from({ length: latentDim.value }, () => 0)
}

function onModelChange() {
  initZ()
}

async function renderLatent() {
  if (!selectedModel.value) return
  loading.value = true
  try {
    const params = {
      run_id_a: selectedModel.value,
      run_id_b: selectedModel.value,
      alpha: 1.0,
      pitch_shift: 0,
      loudness_shift: 0,
    }
    const result = await apiClient.morph(params)
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 1000))
      try {
        const job = await apiClient.getInferenceJob(result.job_id)
        if (job.status === 'completed') {
          audioUrl.value = job.artifact_url
          break
        }
        if (job.status === 'failed') break
      } catch {
        break
      }
    }
  } finally {
    loading.value = false
  }
}

function dimensionGroups() {
  const groups = []
  for (let i = 0; i < zValues.value.length; i += 8) {
    groups.push(zValues.value.slice(i, i + 8))
  }
  return groups
}
</script>

<template>
  <div class="latent-explore-view">
    <h2>Latent Space Exploration</h2>
    <p class="hint">Manually steer individual latent dimensions and render the result.</p>

    <div class="card">
      <div class="row">
        <label class="label">Model</label>
        <select v-model="selectedModel" class="select wide" @change="onModelChange">
          <option value="" disabled>Select model...</option>
          <option v-for="m in models" :key="m.run_id" :value="m.run_id">{{ m.run_id }}</option>
        </select>
      </div>
    </div>

    <div v-if="selectedModel" class="card">
      <h3>Latent Steering</h3>
      <p class="hint">Adjust each latent dimension (range -3 to +3).</p>
      <div v-for="(group, gi) in dimensionGroups()" :key="gi" class="dim-group">
        <div v-for="(val, vi) in group" :key="gi * 8 + vi" class="dim-row">
          <label class="label">{{ 'z[' + (gi * 8 + vi) + ']' }}</label>
          <input type="range" min="-3" max="3" step="0.1" v-model.number="zValues[gi * 8 + vi]" class="slider" />
          <span class="value-tag dim-val">{{ zValues[gi * 8 + vi].toFixed(1) }}</span>
        </div>
      </div>
      <button class="btn-primary" @click="renderLatent" :disabled="loading">
        {{ loading ? 'Rendering...' : 'Render' }}
      </button>
    </div>

    <div v-if="audioUrl" class="card">
      <h3>Result</h3>
      <audio controls :src="audioUrl" style="width: 100%"></audio>
    </div>
  </div>
</template>

<style scoped>
.latent-explore-view {
  --bg-deep: #0f0f1a;
  --bg-card: #1a1a2e;
  --border: #2d2d4a;
  --text: #e2e8f0;
  --accent: #6366F1;
  --hint: #94a3b8;

  padding: 1.5rem;
  background: var(--bg-deep);
  color: var(--text);
  min-height: 100%;
}

.latent-explore-view h2 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem 0;
  color: var(--text);
}

.hint {
  font-size: 0.85rem;
  color: var(--hint);
  margin: 0 0 1.5rem 0;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}

.card h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  color: var(--accent);
}

.row {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 0.9rem;
}

.label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: var(--hint);
  min-width: 5rem;
}

.value-tag {
  color: var(--accent);
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.select {
  background: var(--bg-deep);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
}

.select.wide {
  width: 100%;
}

.slider {
  flex: 1;
  accent-color: var(--accent);
}

.dim-group {
  margin-bottom: 1rem;
}

.dim-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
}

.dim-val {
  width: 3rem;
  text-align: right;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: opacity 0.15s;
  margin-top: 0.5rem;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
