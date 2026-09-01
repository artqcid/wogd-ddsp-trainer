<script setup>
import { inject, ref } from 'vue'

const apiClient = inject('apiClient')

const models = ref([])
const selectedA = ref('')
const selectedB = ref('')
const alpha = ref(0.5)
const sourceFile = ref(null)
const jobId = ref(null)
const jobStatus = ref(null)
const audioUrl = ref(null)
const loading = ref(false)

async function loadModels() {
  const data = await apiClient.listModels()
  models.value = data || []
}
loadModels()

async function renderBlend() {
  if (!selectedA.value || !selectedB.value) return
  loading.value = true
  jobStatus.value = 'submitting'
  try {
    const formData = new FormData()
    formData.append('run_id_a', selectedA.value)
    formData.append('run_id_b', selectedB.value)
    formData.append('alpha', String(alpha.value))
    if (sourceFile.value) {
      formData.append('audio', sourceFile.value)
    }
    const result = await apiClient.morph(formData)
    jobId.value = result.job_id
    jobStatus.value = 'pending'
    await pollJob(result.job_id)
  } catch (err) {
    jobStatus.value = 'error'
  } finally {
    loading.value = false
  }
}

async function pollJob(id) {
  for (let i = 0; i < 30; i++) {
    await new Promise(r => setTimeout(r, 1000))
    try {
      const job = await apiClient.getInferenceJob(id)
      if (job.status === 'completed') {
        jobStatus.value = 'completed'
        audioUrl.value = job.artifact_url
        return
      }
      if (job.status === 'failed') {
        jobStatus.value = 'failed'
        return
      }
    } catch {
      jobStatus.value = 'error'
      return
    }
  }
  jobStatus.value = 'timeout'
}
</script>

<template>
  <div class="morphing-view">
    <h2>Checkpoint Morphing</h2>
    <p class="hint">Blend two latent-trained models by interpolating their latent vectors.</p>

    <div class="card">
      <div class="row">
        <label class="label">Model A</label>
        <select v-model="selectedA" class="select wide">
          <option value="" disabled>Select model...</option>
          <option v-for="m in models" :key="m.run_id" :value="m.run_id">{{ m.run_id }}</option>
        </select>
      </div>
      <div class="row">
        <label class="label">Model B</label>
        <select v-model="selectedB" class="select wide">
          <option value="" disabled>Select model...</option>
          <option v-for="m in models" :key="m.run_id" :value="m.run_id">{{ m.run_id }}</option>
        </select>
      </div>
      <div class="row">
        <label class="label">
          Alpha (blend ratio)
          <span class="value-tag">{{ alpha.toFixed(2) }}</span>
        </label>
        <input type="range" min="0" max="1" step="0.01" v-model.number="alpha" class="slider" />
      </div>
      <div class="row">
        <label class="label">Source audio (optional)</label>
        <input type="file" accept="audio/*" @change="e => sourceFile = e.target.files[0]" class="file-input" />
      </div>
      <div class="row">
        <button class="btn-primary" @click="renderBlend" :disabled="loading || !selectedA || !selectedB">
          {{ loading ? 'Rendering...' : 'Render Blend' }}
        </button>
      </div>
    </div>

    <div v-if="jobStatus" class="card">
      <h3>Status: {{ jobStatus }}</h3>
      <div v-if="audioUrl" class="audio-player">
        <audio controls :src="audioUrl" style="width: 100%"></audio>
      </div>
    </div>

    <div class="card warning-card" v-if="selectedA || selectedB">
      <p class="warning">Both models must be trained with Latent Space enabled for morphing to work.</p>
    </div>
  </div>
</template>

<style scoped>
.morphing-view {
  --bg-deep: #0f0f1a;
  --bg-card: #1a1a2e;
  --border: #2d2d4a;
  --text: #e2e8f0;
  --accent: #6366F1;
  --hint: #94a3b8;
  --warning: #f59e0b;

  padding: 1.5rem;
  background: var(--bg-deep);
  color: var(--text);
  min-height: 100%;
}

.morphing-view h2 {
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

.row:last-child {
  margin-bottom: 0;
}

.label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: var(--hint);
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
  width: 100%;
  accent-color: var(--accent);
}

.file-input {
  background: var(--bg-deep);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 8px;
  padding: 0.5rem;
  font-size: 0.85rem;
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
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.audio-player {
  margin-top: 0.5rem;
}

.warning {
  margin: 0;
  padding: 0.6rem 0.8rem;
  background: rgba(245, 158, 11, 0.12);
  border-left: 3px solid var(--warning);
  color: var(--warning);
  border-radius: 4px;
  font-size: 0.88rem;
}
</style>
