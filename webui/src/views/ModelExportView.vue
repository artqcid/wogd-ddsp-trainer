<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { inject } from 'vue'
import ModelParameterBuilder from '../components/ModelParameterBuilder.vue'

const apiClient = inject('apiClient')

const models = ref([])
const selectedModel = ref(null)
const manifest = ref(null)
const modelTier = ref('standard')
const formatOptions = [
  { id: 'neutone', label: 'Neutone', description: 'Plugin format for Neutone. Max 50ms inference time.' },
  { id: 'onnx', label: 'ONNX', description: 'Cross-platform format. Works with ONNX Runtime.' },
  { id: 'torchscript', label: 'TorchScript', description: 'PyTorch native format. Requires LibTorch.' },
]

const selectedFormats = ref([])
const isExporting = ref(false)
const exportJobId = ref(null)
const exportStatus = ref(null)
const statusPollId = ref(null)

const statusFetched = ref(false)

onMounted(async () => {
  if (!apiClient) return
  try {
    models.value = await apiClient.listModels()
  } catch (e) {
    models.value = []
  }
})

onBeforeUnmount(() => {
  if (statusPollId.value) {
    clearInterval(statusPollId.value)
  }
})

const loadManifest = async () => {
  if (!selectedModel.value || !apiClient) {
    manifest.value = null
    return
  }
  try {
    const checkpoint = selectedModel.value.checkpoints[0] || null
    manifest.value = await apiClient.getCheckpointParams(selectedModel.value.run_id, checkpoint)
  } catch (e) {
    manifest.value = null
  }
}

watch(selectedModel, () => {
  loadManifest()
})

const startExport = async () => {
  if (!selectedModel.value || selectedFormats.value.length === 0 || !apiClient) return
  isExporting.value = true
  exportJobId.value = null
  exportStatus.value = null
  statusFetched.value = false

  try {
    const checkpoint = selectedModel.value.checkpoints[0] || null
    const response = await apiClient.exportModel({
      run_id: selectedModel.value.run_id,
      checkpoint,
      formats: selectedFormats.value
    })
    exportJobId.value = response.job_id
    pollStatus()
  } catch (e) {
    exportStatus.value = { state: 'failed', error: String(e) }
    isExporting.value = false
  }
}

const pollStatus = () => {
  if (statusPollId.value) clearInterval(statusPollId.value)
  statusPollId.value = setInterval(async () => {
    if (!apiClient || !exportJobId.value) return
    try {
      const status = await apiClient.exportStatus(exportJobId.value)
      exportStatus.value = status
      statusFetched.value = true
      if (status.state === 'completed' || status.state === 'failed') {
        clearInterval(statusPollId.value)
        statusPollId.value = null
        isExporting.value = false
      }
    } catch (e) {
      exportStatus.value = { state: 'failed', error: String(e) }
      clearInterval(statusPollId.value)
      statusPollId.value = null
      isExporting.value = false
    }
  }, 3000)
}

const onManifestUpdate = (updatedManifest) => {
  manifest.value = updatedManifest
}

const toggleFormat = (format) => {
  const idx = selectedFormats.value.indexOf(format)
  if (idx >= 0) {
    selectedFormats.value.splice(idx, 1)
  } else {
    selectedFormats.value.push(format)
  }
}
</script>

<template>
  <section class="export-view">
    <header class="export-header">
      <h2>Model Export</h2>
      <p v-if="!apiClient" data-testid="api-status">API client missing</p>
    </header>

    <div v-if="models.length > 0">
      <label for="model-select" class="sr-only">Select model</label>
      <select id="model-select" v-model="selectedModel" class="model-select" data-testid="model-select">
        <option value="">Choose a model</option>
        <option
          v-for="model in models"
          :key="model.run_id"
          :value="model"
        >
          {{ model.run_id }} — {{ model.checkpoints.join(', ') }}
        </option>
      </select>
    </div>

    <ModelParameterBuilder
      v-if="manifest"
      :manifest="manifest"
      :modelTier="modelTier"
      :readonly="false"
      data-testid="export-param-builder"
      @update:manifest="onManifestUpdate"
    />

    <div v-else-if="models.length === 0 && !isExporting" class="empty-state">
      <p>No models available.</p>
    </div>

    <div class="format-selector">
      <div
        v-for="format in formatOptions"
        :key="format.id"
        class="format-card"
        :class="{ selected: selectedFormats.includes(format.id) }"
        @click="toggleFormat(format.id)"
        data-testid="format-card"
      >
        <h4>{{ format.label }}</h4>
        <p>{{ format.description }}</p>
      </div>
    </div>

    <button
      class="export-btn"
      :disabled="!selectedModel || selectedFormats.length === 0 || isExporting"
      @click="startExport"
      data-testid="export-btn"
    >
      <span v-if="isExporting">Exporting...</span>
      <span v-else>Export Model</span>
    </button>

    <div v-if="exportStatus && statusFetched" class="export-status" :class="exportStatus.state" data-testid="export-status">
      <span v-if="exportStatus.state === 'pending'">Pending</span>
      <span v-else-if="exportStatus.state === 'running'">Exporting...</span>
      <span v-else-if="exportStatus.state === 'completed'">Export completed</span>
      <span v-else-if="exportStatus.state === 'failed'">{{ exportStatus.error || 'Export failed' }}</span>
      <span v-else>{{ exportStatus.state }}</span>
    </div>

    <div v-if="exportStatus && exportStatus.state === 'completed' && exportStatus.downloads" class="download-links">
      <h3>Download Links</h3>
      <a
        v-for="link in exportStatus.downloads"
        :key="link.format"
        :href="link.downloadUrl"
        target="_blank"
        rel="noopener noreferrer"
        class="download-link"
        data-testid="download-link"
      >
        {{ link.format }} — {{ link.downloadUrl }}
      </a>
    </div>
  </section>
</template>

<style scoped>
.export-view { max-width: 900px; }
.export-header { margin-bottom: 1.5rem; }
.format-selector { display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.format-card { flex: 1; min-width: 200px; padding: 1rem; background: var(--bg-secondary); border: 2px solid var(--border); border-radius: 8px; cursor: pointer; transition: border-color 0.15s; }
.format-card:hover { border-color: var(--accent); }
.format-card.selected { border-color: var(--accent); background: var(--bg-tertiary); }
.format-card h4 { margin: 0 0 0.375rem; font-size: 0.9rem; }
.format-card p { margin: 0; font-size: 0.8rem; color: var(--text-secondary); }
.export-btn { padding: 0.5rem 1.5rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; margin-bottom: 1.5rem; }
.export-btn:hover { background: var(--accent-hover); }
.export-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.export-status { margin-top: 1rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.875rem; }
.export-status.completed { background: var(--success); color: #000; }
.export-status.failed { background: var(--error); color: #fff; }
.download-links { margin-top: 1rem; }
.download-links h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.download-link { display: block; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 0.5rem; color: var(--accent); text-decoration: none; font-size: 0.875rem; }
.download-link:hover { background: var(--bg-tertiary); }
.empty-state { color: var(--text-secondary); }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
</style>
