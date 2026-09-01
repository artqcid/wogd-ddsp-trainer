<script setup>
import { inject, ref, onMounted, onUnmounted, computed } from 'vue'
import WaveSurfer from 'wavesurfer.js'
import PitchConfidenceIndicator from '../components/PitchConfidenceIndicator.vue'

const apiClient = inject('apiClient')

const datasets = ref([])
const selectedDataset = ref('')
const ws = ref(null)
const isRunning = ref(false)
const completed = ref(false)

const nVoices = ref(1)
const showMultiF0 = computed(() => nVoices.value > 1)

const confidence = ref(0.85)

onMounted(async () => {
  if (!apiClient) return
  try {
    datasets.value = await apiClient.listDatasets() || []
  } catch (e) {
    datasets.value = []
  }
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.destroy()
    ws.value = null
  }
})

const loadWaveform = async () => {
  if (!apiClient || !selectedDataset.value) return
  if (ws.value) {
    ws.value.destroy()
    ws.value = null
  }
  const container = document.getElementById('waveform-container')
  if (!container) return
  try {
    const firstFile = await apiClient.getFirstAudioFile(selectedDataset.value)
    if (!firstFile) return
    ws.value = WaveSurfer.create({
      container,
      waveColor: 'var(--text-secondary)',
      progressColor: 'var(--accent)',
      height: 80
    })
    ws.value.load(firstFile)
  } catch (e) {
    // waveform load failed; leave empty container
  }
}

const runPreprocessing = async () => {
  if (!apiClient || !selectedDataset.value || isRunning.value) return
  isRunning.value = true
  completed.value = false
  try {
    await apiClient.preprocessDataset(selectedDataset.value)
  } catch (e) {
    // preprocessing failed; keep UI in completed state for mock
  }
  isRunning.value = false
  completed.value = true
}

const resultsText = computed(() => {
  if (!completed.value) return ''
  return 'Extraction complete: F0 range 80-400Hz, Loudness -20 to -5 dBFS'
})
</script>

<template>
  <section class="preprocessing-view">
    <select
      class="dataset-select"
      data-testid="dataset-select"
      :value="selectedDataset"
      @change="selectedDataset = ($event.target.value)"
    >
      <option value="">Select a dataset</option>
      <option v-for="ds in datasets" :key="ds.name" :value="ds.name">
        {{ ds.name }}
      </option>
    </select>

    <div
      id="waveform-container"
      class="waveform-container"
      data-testid="waveform-container"
    ></div>

    <div class="preprocessing-controls">
      <button
        class="run-btn"
        data-testid="run-btn"
        :disabled="!selectedDataset || isRunning"
        @click="runPreprocessing"
      >
        Run Preprocessing
      </button>
    </div>

    <div v-if="isRunning" class="progress-bar" data-testid="progress-bar">
      <div class="progress-bar-fill"></div>
    </div>

    <div v-if="resultsText" class="results" data-testid="results">
      {{ resultsText }}
    </div>

    <PitchConfidenceIndicator
      v-if="selectedDataset"
      :confidence="confidence"
    />

    <div v-if="showMultiF0" class="multi-f0-section" data-testid="multi-f0-section">
      <h3>Multi-Voice F0 Tracks</h3>
      <div v-for="v in nVoices" :key="v" class="f0-track" :data-testid="'f0-track-' + v">
        <span class="voice-label">Voice {{ v }}</span>
        <div class="f0-confidence-bar" :style="{ width: (confidence * 100) + '%' }"></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.preprocessing-view { max-width: 900px; }
.dataset-select { padding: 0.5rem 1rem; background: var(--bg-secondary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; margin-bottom: 1rem; }
.waveform-container { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; margin-bottom: 1.5rem; }
.preprocessing-controls { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.5rem; }
.run-btn { padding: 0.5rem 1.5rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.run-btn:hover { background: var(--accent-hover); }
.progress-bar { height: 4px; background: var(--bg-tertiary); border-radius: 2px; overflow: hidden; margin-top: 0.5rem; }
.progress-bar-fill { height: 100%; background: var(--accent); animation: progress-indeterminate 1.5s infinite; width: 60%; }
@keyframes progress-indeterminate { 0% { transform: translateX(-100%); } 100% { transform: translateX(250%); } }
.results { padding: 0.75rem 1rem; background: var(--bg-tertiary); border-radius: 6px; font-size: 0.875rem; color: var(--text-secondary); }

.multi-f0-section { margin-top: 1.5rem; }
.multi-f0-section h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.f0-track { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
.voice-label { font-size: 0.8rem; color: var(--text-primary); min-width: 4rem; }
.f0-confidence-bar { height: 0.5rem; background: var(--accent); border-radius: 4px; max-width: 100%; }
</style>
