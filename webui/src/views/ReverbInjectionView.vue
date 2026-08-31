<script setup>
import { inject, ref, onMounted } from 'vue'

const apiClient = inject('apiClient')

const models = ref([])
const selectedRunId = ref('')
const irFile = ref(null)
const irFileName = ref('')
const isInjecting = ref(false)
const injectStatus = ref('')
const extractUrl = ref('')
const isExtracting = ref(false)

onMounted(async () => {
  if (!apiClient) return
  try {
    models.value = await apiClient.listModels()
  } catch (err) {
    console.error('Failed to load models:', err)
  }
})

function onIrFileChange(event) {
  const file = event.target.files?.[0] || null
  irFile.value = file
  irFileName.value = file ? file.name : ''
}

async function handleInject() {
  if (!apiClient || !selectedRunId.value || !irFile.value) return
  isInjecting.value = true
  injectStatus.value = ''

  try {
    const result = await apiClient.injectIr(selectedRunId.value, irFile.value)
    injectStatus.value = result.status === 'ok' ? 'IR injected successfully' : 'Injection failed'
  } catch (err) {
    console.error('Inject IR failed:', err)
    injectStatus.value = `Error: ${err.message}`
  } finally {
    isInjecting.value = false
  }
}

async function handleExtract() {
  if (!apiClient || !selectedRunId.value) return
  isExtracting.value = true

  try {
    extractUrl.value = await apiClient.extractIrUrl(selectedRunId.value)
  } catch (err) {
    console.error('Extract IR failed:', err)
  } finally {
    isExtracting.value = false
  }
}
</script>

<template>
  <section class="reverb-view">
    <header class="reverb-header">
      <h2>Reverb IR Injection</h2>
      <p class="view-description">Inject a custom impulse response into a model's reverb or extract its current IR.</p>
    </header>

    <div class="form-row">
      <div class="form-group">
        <label for="run-select">Model / Run</label>
        <select id="run-select" v-model="selectedRunId" data-testid="run-select">
          <option value="">Select a model</option>
          <option v-for="m in models" :key="m.run_id" :value="m.run_id">
            {{ m.run_id }} — {{ m.checkpoint }}
          </option>
        </select>
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">Inject IR</h3>
      <p class="section-description">Upload a .wav impulse response to replace the model's reverb kernel.</p>

      <div class="form-row">
        <div class="form-group">
          <label for="ir-input">IR File (.wav)</label>
          <input
            id="ir-input"
            type="file"
            accept=".wav,audio/wav,audio/x-wav,audio/mpeg,audio/mp3,audio/flac"
            @change="onIrFileChange"
            data-testid="ir-input"
          />
          <span v-if="irFileName" class="selected-filename">{{ irFileName }}</span>
        </div>
      </div>

      <button
        class="action-btn primary"
        @click="handleInject"
        :disabled="!selectedRunId || !irFile || isInjecting"
        data-testid="inject-btn"
      >
        {{ isInjecting ? 'Injecting...' : 'Inject' }}
      </button>

      <div v-if="injectStatus" class="status-message" :class="{ success: injectStatus.includes('successfully') }" data-testid="inject-status">
        {{ injectStatus }}
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">Extract IR</h3>
      <p class="section-description">Download the model's current reverb kernel as a .wav file.</p>

      <button
        class="action-btn"
        @click="handleExtract"
        :disabled="!selectedRunId || isExtracting"
        data-testid="extract-btn"
      >
        {{ isExtracting ? 'Extracting...' : 'Download IR' }}
      </button>

      <div v-if="extractUrl && !isExtracting" class="download-link" data-testid="extract-link">
        <a :href="extractUrl" download="reverb_ir.wav" class="download-url">Download IR — {{ selectedRunId }}</a>
      </div>

      <div v-if="injectStatus && !injectStatus.includes('successfully')" class="status-message error" data-testid="extract-status">
        {{ injectStatus }}
      </div>
    </div>
  </section>
</template>

<style scoped>
.reverb-view { max-width: 700px; }
.reverb-header { margin-bottom: 1.5rem; }
.view-description { color: var(--text-secondary); margin-bottom: 0.5rem; font-size: 0.875rem; }
.section { margin-top: 2rem; padding: 1rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; }
.section-title { margin: 0 0 0.25rem; font-size: 1rem; color: var(--text-primary); }
.section-description { margin: 0 0 1rem; color: var(--text-secondary); font-size: 0.85rem; }
.form-row { display: flex; gap: 1rem; margin-bottom: 1rem; }
.form-row .form-group { flex: 1; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group select,
.form-group input { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-tertiary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; }
.form-group select:focus,
.form-group input:focus { outline: none; border-color: var(--accent); }
.selected-filename { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem; }
.action-btn {
  padding: 0.5rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
}
.action-btn.primary { background: var(--accent); color: #000; }
.action-btn.primary:hover:not(:disabled) { background: var(--accent-hover); }
.action-btn:not(.primary) { background: var(--bg-tertiary); color: var(--text-primary); border: 1px solid var(--border); }
.action-btn:not(.primary):hover:not(:disabled) { background: var(--bg-primary); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.status-message {
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
.status-message.success { background: var(--success); color: #000; }
.status-message.error { background: var(--error); color: #fff; }
.download-link { margin-top: 0.75rem; }
.download-url { color: var(--accent); text-decoration: none; font-size: 0.875rem; }
.download-url:hover { text-decoration: underline; }
</style>
