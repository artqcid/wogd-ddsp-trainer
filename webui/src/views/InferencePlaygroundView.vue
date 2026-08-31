<script setup>
import { inject, ref, onMounted, onUnmounted, watch } from 'vue'
import ABComparisonPlayer from '../components/ABComparisonPlayer.vue'

const apiClient = inject('apiClient')

const models = ref([])
const selectedModelId = ref('')
const audioFile = ref(null)
const audioFileName = ref('')
const enhanceOutput = ref(false)
const isSynthesizing = ref(false)
const jobId = ref(null)
const jobStatus = ref(null)
const jobResult = ref(null)
const artifacts = ref([])
const pollInterval = ref(null)

const sourceAudioUrl = ref(null)

onMounted(async () => {
  if (!apiClient) return
  try {
    models.value = await apiClient.listModels()
  } catch (err) {
    console.error('Failed to load models:', err)
  }
})

onUnmounted(() => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
})

function onFileChange(event) {
  const file = event.target.files?.[0] || null
  audioFile.value = file
}

watch(audioFile, (file) => {
  audioFileName.value = file ? file.name : ''
  sourceAudioUrl.value = file ? URL.createObjectURL(file) : null
})

async function handleSynthesize() {
  if (!apiClient || !selectedModelId.value || !audioFile.value) return
  isSynthesizing.value = true
  jobStatus.value = null
  jobResult.value = null
  artifacts.value = []

  try {
    const result = await apiClient.synthesize({
      model_id: selectedModelId.value,
      audio_file: audioFile.value,
      enhance: enhanceOutput.value
    })
    jobId.value = result.job_id
    jobStatus.value = result.status
    if (result.status === 'completed') {
      jobResult.value = result
      await loadArtifacts()
    } else {
      startPolling()
    }
  } catch (err) {
    console.error('Synthesis failed:', err)
    jobStatus.value = 'failed'
  } finally {
    isSynthesizing.value = false
  }
}

function startPolling() {
  if (pollInterval.value) clearInterval(pollInterval.value)
  pollInterval.value = setInterval(async () => {
    if (!apiClient || !jobId.value) return
    try {
      const status = await apiClient.getInferenceJob(jobId.value)
      jobStatus.value = status.status
      if (status.status === 'completed') {
        jobResult.value = status
        clearInterval(pollInterval.value)
        pollInterval.value = null
        await loadArtifacts()
      } else if (status.status === 'failed') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
      }
    } catch (err) {
      console.error('Polling error:', err)
    }
  }, 3000)
}

async function loadArtifacts() {
  if (!apiClient || !jobId.value) return
  try {
    artifacts.value = await apiClient.getInferenceArtifacts(jobId.value)
  } catch (err) {
    console.error('Failed to load artifacts:', err)
  }
}
</script>

<template>
  <section class="inference-view">
    <header class="inference-header">
      <h2>Inference Playground</h2>
      <p class="view-description">Run timbre transfer and compare audio A/B.</p>
    </header>

    <div class="form-row">
      <div class="form-group">
        <label for="model-select">Model</label>
        <select id="model-select" v-model="selectedModelId" data-testid="model-select">
          <option value="">Select a model</option>
          <option v-for="m in models" :key="m.run_id" :value="m.run_id">
            {{ m.run_id }} — {{ m.checkpoint }}
          </option>
        </select>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group">
        <label for="audio-input">Source Audio</label>
        <input
          id="audio-input"
          type="file"
          accept="audio/*"
          @change="onFileChange"
          data-testid="audio-input"
        />
        <span v-if="audioFileName" class="selected-filename">{{ audioFileName }}</span>
      </div>
    </div>

    <div class="form-row">
      <div class="form-group checkbox-group">
        <label>
          <input type="checkbox" v-model="enhanceOutput" data-testid="enhance-toggle" />
          Enable output enhancement
        </label>
        <span class="enhance-hint">Improve perceived quality via pre-trained vocoder</span>
      </div>
    </div>

    <button
      class="synthesize-btn"
      @click="handleSynthesize"
      :disabled="!selectedModelId || !audioFile || isSynthesizing"
      data-testid="synthesize-btn"
    >
      {{ isSynthesizing ? 'Synthesizing...' : 'Synthesize' }}
    </button>

    <div v-if="jobId" class="job-status" :class="jobStatus" data-testid="job-status">
      <span class="job-label">Job:</span>
      <span class="job-id">{{ jobId }}</span>
      <span class="job-status-badge">{{ jobStatus }}</span>
    </div>

    <ABComparisonPlayer
      v-if="jobStatus === 'completed' && sourceAudioUrl && jobResult?.audio_url"
      :original-url="sourceAudioUrl"
      :synthesized-url="jobResult.audio_url"
      data-testid="ab-player"
    />

    <div v-if="artifacts.length" class="artifacts-list">
      <h3>Artifacts</h3>
      <div v-for="artifact in artifacts" :key="artifact.name" class="artifact-item" data-testid="artifact-item">
        <span>{{ artifact.name }}</span>
        <a :href="artifact.url" :download="artifact.name" target="_blank">Download</a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.inference-view { max-width: 900px; }
.inference-header { margin-bottom: 1.5rem; }
.view-description { color: var(--text-secondary); margin-bottom: 0.5rem; }
.form-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
.form-row .form-group { flex: 1; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group select, .form-group input { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; }
.selected-filename { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem; }
.synthesize-btn { padding: 0.5rem 1.5rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.synthesize-btn:hover { background: var(--accent-hover); }
.synthesize-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.job-status { margin-top: 1rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.875rem; display: flex; gap: 0.5rem; align-items: center; }
.job-status.completed { background: var(--success); color: #000; }
.job-status.failed { background: var(--error); color: #fff; }
.job-status.running { background: var(--accent); color: #000; }
.job-label { color: var(--text-secondary); }
.job-id { font-family: monospace; }
.job-status-badge { padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; background: rgba(0,0,0,0.15); }
.job-status.completed .job-status-badge { background: rgba(0,0,0,0.1); }
.job-status.failed .job-status-badge { background: rgba(255,255,255,0.2); }
.artifacts-list { margin-top: 1.5rem; }
.artifacts-list h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.artifact-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 0.5rem; font-size: 0.875rem; }
.artifact-item a { color: var(--accent); text-decoration: none; }
.artifact-item a:hover { text-decoration: underline; }
.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}
.enhance-hint {
  font-size: 0.85em;
  opacity: 0.7;
  margin-left: 1.5rem;
}
</style>
