<script setup>
import { inject, ref } from 'vue'

const apiClient = inject('apiClient')
const models = ref([])
const selectedModel = ref('')
const pitchShift = ref(0)
const loudnessShift = ref(0)
const jobStatus = ref(null)
const resultUrl = ref(null)
const sourceFile = ref(null)
const isConverting = ref(false)

function onFileChange(e) {
  sourceFile.value = e.target.files[0] || null
}

async function convert() {
  if (!apiClient || !sourceFile.value || !selectedModel.value) return
  isConverting.value = true
  jobStatus.value = null
  resultUrl.value = null
  try {
    const formData = new FormData()
    formData.append('run_id', selectedModel.value)
    formData.append('source_audio', sourceFile.value)
    formData.append('pitch_shift', String(pitchShift.value))
    formData.append('loudness_shift', String(loudnessShift.value))
    const result = await apiClient.voiceConvert(formData)
    jobStatus.value = result.status
    // Poll for completion would go here in a full implementation
  } catch (e) {
    jobStatus.value = 'error: ' + (e.message || 'Unknown error')
  }
  isConverting.value = false
}
</script>

<template>
  <section class="vc-view">
    <div class="vc-header">
      <h2>Voice Conversion</h2>
      <p class="vc-subtitle">Replace the timbre of a source audio with a trained model's target voice.</p>
    </div>

    <div class="vc-section">
      <h3>Target Model</h3>
      <div class="form-group">
        <select v-model="selectedModel" data-testid="vc-model-select">
          <option value="">-- Select Model --</option>
          <option v-for="m in models" :key="m.run_id" :value="m.run_id">
            {{ m.run_id }}
          </option>
        </select>
      </div>
    </div>

    <div class="vc-section">
      <h3>Source Audio</h3>
      <input type="file" accept="audio/*" @change="onFileChange" data-testid="vc-source-audio" />
    </div>

    <div class="vc-section">
      <h3>Adjustments</h3>
      <div class="form-group">
        <label for="pitch-shift">Pitch Shift (semitones)</label>
        <input id="pitch-shift" type="number" min="-12" max="12" step="1" v-model.number="pitchShift" data-testid="vc-pitch-shift" />
      </div>
      <div class="form-group">
        <label for="loudness-shift">Loudness Shift (dB)</label>
        <input id="loudness-shift" type="number" min="-12" max="12" step="1" v-model.number="loudnessShift" data-testid="vc-loudness-shift" />
      </div>
    </div>

    <div class="vc-section">
      <button
        class="btn-primary"
        :disabled="!selectedModel || !sourceFile || isConverting"
        @click="convert"
        data-testid="vc-convert-btn"
      >
        {{ isConverting ? 'Converting...' : 'Convert' }}
      </button>
    </div>

    <div v-if="jobStatus" class="vc-job-status" data-testid="vc-job-status">
      Status: {{ jobStatus }}
    </div>

    <div class="vc-info-callout" data-testid="vc-info-callout">
      <p><strong>How it works:</strong> The target timbre comes from the trained model. The source content (speech/melody) comes from the uploaded audio.</p>
    </div>
  </section>
</template>

<style scoped>
.vc-view { max-width: 900px; }
.vc-header { margin-bottom: 1.5rem; }
.vc-subtitle { font-size: 0.875rem; color: var(--text-secondary); margin-top: 0.25rem; }
.vc-section { margin-bottom: 1.5rem; }
.vc-section h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group input, .form-group select { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; }
.btn-primary { padding: 0.5rem 1.5rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.vc-job-status { padding: 0.75rem 1rem; background: var(--bg-tertiary); border-radius: 6px; font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem; }
.vc-info-callout { padding: 1rem; background: var(--bg-tertiary); border-left: 3px solid var(--accent); border-radius: 6px; font-size: 0.875rem; color: var(--text-secondary); }
</style>
