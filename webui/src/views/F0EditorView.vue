<script setup>
import { ref, inject, onMounted } from 'vue'
import F0Editor from '../components/F0Editor.vue'
import F0RulesPanel from '../components/F0RulesPanel.vue'
import { logger } from '../utils/logger.js'

const apiClient = inject('apiClient')
const datasets = ref([])
const selectedDataset = ref(null)
const selectedFile = ref(null)
const f0Data = ref([])
const statusMessage = ref('')

onMounted(async () => {
  if (!apiClient) return
  try {
    datasets.value = await apiClient.listDatasets()
  } catch (e) {
    logger.error('Failed to load datasets:', e)
  }
})

async function loadF0() {
  if (!apiClient || !selectedDataset.value || !selectedFile.value) return
  statusMessage.value = 'Loading F0...'
  try {
    const features = await apiClient.getFeatures(selectedDataset.value, selectedFile.value)
    f0Data.value = features.f0_hz
    statusMessage.value = ''
  } catch (e) {
    statusMessage.value = `Failed to load F0: ${e}`
  }
}

function onF0Update(newData) {
  f0Data.value = newData
}

function onApplyRule(ruleConfig) {
  statusMessage.value = `Rule '${ruleConfig.rule}' applied (simulated)`
}
</script>

<template>
  <section class="f0-editor-view">
    <header class="view-header">
      <h2>F0 Editor</h2>
      <p class="view-description">Override F0 curves per file or apply global transformations.</p>
    </header>

    <div class="form-row">
      <div class="form-group">
        <label for="dataset-select">Dataset</label>
        <select id="dataset-select" v-model="selectedDataset" @change="selectedFile = null; f0Data = []">
          <option value="">Select a dataset</option>
          <option v-for="d in datasets" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      <div v-if="selectedDataset" class="form-group">
        <label for="file-select">File</label>
        <select id="file-select" v-model="selectedFile" @change="loadF0">
          <option value="">Select a file</option>
          <option v-for="f in fileList" :key="f" :value="f">{{ f }}</option>
        </select>
      </div>
    </div>

    <div v-if="statusMessage" class="status-msg">{{ statusMessage }}</div>

    <div v-if="f0Data.length" class="editor-layout">
      <div class="editor-main">
        <F0Editor :f0-data="f0Data" @update="onF0Update" />
      </div>
      <div class="editor-sidebar">
        <F0RulesPanel @apply="onApplyRule" />
      </div>
    </div>
  </section>
</template>

<script>
import { computed } from 'vue'
export default {
  computed: {
    fileList() {
      const ds = this.datasets.find(d => d.id === this.selectedDataset)
      return ds ? ds.files : []
    }
  }
}
</script>

<style scoped>
.f0-editor-view {
  max-width: 960px;
}
.view-header {
  margin-bottom: 1rem;
}
.view-header h2 {
  margin: 0;
  color: var(--text-primary);
}
.view-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0.25rem 0 0 0;
}
.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
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
.form-group select {
  padding: 0.4rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  min-width: 200px;
}
.status-msg {
  color: var(--text-secondary);
  font-style: italic;
  margin-bottom: 1rem;
}
.editor-layout {
  display: flex;
  gap: 1rem;
}
.editor-main {
  flex: 1;
}
.editor-sidebar {
  width: 280px;
  flex-shrink: 0;
}
</style>
