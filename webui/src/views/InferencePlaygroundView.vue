<script setup>
import { inject, ref, onMounted, onUnmounted, watch, computed } from 'vue'
import ABComparisonPlayer from '../components/ABComparisonPlayer.vue'

const apiClient = inject('apiClient')

const models = ref([])
const selectedModelId = ref('')
const selectedModel = ref(null)
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

const paramManifest = ref(null)
const paramValues = ref({})

const paramGroups = computed(() => {
  if (!paramManifest.value) return []
  const groups = {}
  for (const param of paramManifest.value.params) {
    const groupName = param.group || ''
    if (!groups[groupName]) {
      groups[groupName] = []
    }
    groups[groupName].push(param)
  }
  const sortedGroups = Object.entries(groups).sort(([a], [b]) => {
    if (a === '') return -1
    if (b === '') return 1
    return a.localeCompare(b)
  })
  return sortedGroups.map(([name, params]) => ({ name, params }))
})

async function loadParamManifest() {
  if (!apiClient || !selectedModel.value) {
    paramManifest.value = null
    paramValues.value = {}
    return
  }
  try {
    const checkpoint = selectedModel.value.checkpoints[0] || 'step-100.pt'
    const manifest = await apiClient.getCheckpointParams(selectedModel.value.run_id, checkpoint)
    paramManifest.value = manifest
    if (manifest) {
      paramValues.value = {}
      for (const param of manifest.params) {
        paramValues.value[param.slot] = param.default_value
      }
    }
  } catch (err) {
    console.error('Failed to load param manifest:', err)
    paramManifest.value = null
    paramValues.value = {}
  }
}

onMounted(async () => {
  if (!apiClient) return
  try {
    models.value = await apiClient.listModels()
  } catch (err) {
    console.error('Failed to load models:', err)
  }
})

watch(selectedModelId, async (newId) => {
  selectedModel.value = models.value.find(m => m.run_id === newId) || null
  await loadParamManifest()
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
    const paramsJson = {}
    for (const [slot, value] of Object.entries(paramValues.value)) {
      paramsJson[slot] = value
    }

    const result = await apiClient.synthesize({
      model_id: selectedModelId.value,
      audio_file: audioFile.value,
      enhance: enhanceOutput.value,
      params: paramsJson
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

function onSliderInput(slot, event) {
  paramValues.value[slot] = parseFloat(event.target.value)
}

function resetToDefaults() {
  if (!paramManifest.value) return
  paramValues.value = {}
  for (const param of paramManifest.value.params) {
    paramValues.value[param.slot] = param.default_value
  }
}

function formatValue(value, param) {
  if (param.param_type === 'continuous') {
    return Number(value).toFixed(2)
  }
  return String(value)
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
            {{ m.run_id }} — {{ m.checkpoints?.join(', ') || m.checkpoint }}
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

    <div v-if="paramManifest" class="param-sliders-section" data-testid="param-sliders-section">
      <h3>Parameters</h3>
      <button
        class="reset-btn"
        @click="resetToDefaults"
        data-testid="param-slider-reset"
      >
        Reset to defaults
      </button>

      <div
        v-for="group in paramGroups"
        :key="group.name"
        class="param-slider-group"
        :data-testid="`param-slider-group-${group.name}`"
      >
        <details v-if="group.params.length > 8">
          <summary>
            <h5>{{ group.name || 'Other' }} ({{ group.params.length }})</h5>
          </summary>
          <div class="param-sliders">
            <div
              v-for="param in group.params"
              :key="param.slot"
              class="param-slider-item"
            >
              <label :for="'param-' + param.slot">
                {{ param.name }}
                <span v-if="param.unit_hint" class="param-unit">({{ param.unit_hint }})</span>
              </label>
              <input
                :id="'param-' + param.slot"
                type="range"
                :min="param.min_value"
                :max="param.max_value"
                :step="param.param_type === 'continuous' ? 0.01 : 1"
                :value="paramValues[param.slot]"
                @input="onSliderInput(param.slot, $event)"
                :data-testid="`param-slider-${param.slot}`"
                class="param-slider"
              />
              <span class="param-value" :data-testid="`param-slider-value-${param.slot}`">
                {{ formatValue(paramValues[param.slot], param) }}
              </span>
            </div>
          </div>
        </details>
        <div v-else class="param-sliders">
          <div
            v-for="param in group.params"
            :key="param.slot"
            class="param-slider-item"
          >
            <label :for="'param-' + param.slot">
              {{ param.name }}
              <span v-if="param.unit_hint" class="param-unit">({{ param.unit_hint }})</span>
            </label>
            <input
              :id="'param-' + param.slot"
              type="range"
              :min="param.min_value"
              :max="param.max_value"
              :step="param.param_type === 'continuous' ? 0.01 : 1"
              :value="paramValues[param.slot]"
              @input="onSliderInput(param.slot, $event)"
              :data-testid="`param-slider-${param.slot}`"
              class="param-slider"
            />
            <span class="param-value" :data-testid="`param-slider-value-${param.slot}`">
              {{ formatValue(paramValues[param.slot], param) }}
            </span>
          </div>
        </div>
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
.param-sliders-section {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
}
.param-sliders-section h3 {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
}
.reset-btn {
  margin-bottom: 1rem;
  padding: 0.375rem 0.75rem;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
}
.reset-btn:hover {
  background: var(--border);
}
.param-slider-group {
  margin-bottom: 1rem;
}
.param-slider-group details {
  margin-bottom: 0.5rem;
}
.param-slider-group summary {
  cursor: pointer;
  padding: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 4px;
  list-style: none;
}
.param-slider-group summary h5 {
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}
.param-slider-group summary::-webkit-details-marker {
  display: none;
}
.param-sliders {
  padding: 0.75rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 4px;
  margin-top: 0.5rem;
}
.param-slider-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin-bottom: 0.75rem;
}
.param-slider-item:last-child {
  margin-bottom: 0;
}
.param-slider-item label {
  font-size: 0.8rem;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.param-unit {
  font-weight: 400;
  color: var(--text-secondary);
  font-size: 0.75rem;
}
.param-slider {
  width: 100%;
  margin: 0.25rem 0;
}
.param-value {
  font-size: 0.75rem;
  font-family: monospace;
  color: var(--text-secondary);
  text-align: right;
}
</style>
