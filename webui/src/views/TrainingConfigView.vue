<script setup>
import { inject, ref, onMounted, computed } from 'vue'
import PresetSaveDialog from '../components/PresetSaveDialog.vue'

const apiClient = inject('apiClient')

const presets = ref([])
const selectedPreset = ref(null)
const learningRate = ref(0.001)
const batchSize = ref(32)
const epochs = ref(100)
const targetMode = ref('offline')
const showDialog = ref(false)
const validationResult = ref(null)
const isClamping = ref(false)
const clampMessages = ref([])

const presetOptions = computed(() => {
  const builtin = presets.value.filter(p => p.type === 'builtin' || p.type === 'autovc' || p.type === 'dsp-autoencoder')
  const custom = presets.value.filter(p => p.type === 'custom')
  return { builtin, custom }
})

const gpuBounds = {
  hiddenDim: 256,
  encoderDim: 256,
  decoderDim: 256,
  postnetDim: 256,
  sampleRate: 48000,
  nHarmonics: 64,
  nTrees: 100
}

function applyPreset(preset) {
  selectedPreset.value = preset
  if (preset?.parameters) {
    learningRate.value = preset.parameters.learning_rate ?? 0.001
    batchSize.value = preset.parameters.batch_size ?? 32
    epochs.value = preset.parameters.epochs ?? 100

    const dims = ['hidden_dim', 'encoder_dim', 'decoder_dim', 'postnet_dim']
    const clamped = []
    dims.forEach(dim => {
      const val = preset.parameters[dim]
      if (val !== undefined && val > gpuBounds[dim]) {
        clamped.push({ dim, original: val, clamped: gpuBounds[dim] })
      }
    })

    if (preset.type === 'custom' && clamped.length > 0) {
      isClamping.value = true
      clampMessages.value = clamped.map(c =>
        `${c.dim.replace('_', ' ')} clamped from ${c.original} to ${c.clamped}`
      )
    } else {
      isClamping.value = false
      clampMessages.value = []
    }
  } else {
    isClamping.value = false
    clampMessages.value = []
  }
}

onMounted(async () => {
  if (!apiClient) return
  try {
    presets.value = await apiClient.listPresets()
  } catch (e) {
    console.error('Failed to load presets:', e)
  }
})

async function handleStartTraining() {
  if (!apiClient) return
  validationResult.value = null
  const config = {
    learning_rate: learningRate.value,
    batch_size: batchSize.value,
    epochs: epochs.value,
    target_mode: targetMode.value,
    preset: selectedPreset.value?.name || null,
    parameters: {
      hidden_dim: selectedPreset.value?.parameters?.hidden_dim ?? 128,
      encoder_dim: selectedPreset.value?.parameters?.encoder_dim ?? 128,
      decoder_dim: selectedPreset.value?.parameters?.decoder_dim ?? 128,
      postnet_dim: selectedPreset.value?.parameters?.postnet_dim ?? 128,
      sample_rate: selectedPreset.value?.parameters?.sample_rate ?? 44100,
      n_harmonics: selectedPreset.value?.parameters?.n_harmonics ?? 32,
      n_trees: selectedPreset.value?.parameters?.n_trees ?? 50
    }
  }
  try {
    const validation = await apiClient.validateConfig(config)
    if (validation.valid) {
      const run = await apiClient.startRun(config)
      validationResult.value = {
        ok: true,
        message: `Training started: ${run.run_id} (${run.status})`
      }
    } else {
      validationResult.value = {
        ok: false,
        message: validation.errors.join('; ')
      }
    }
  } catch (e) {
    validationResult.value = {
      ok: false,
      message: e.message || 'Validation failed'
    }
  }
}
</script>

<template>
  <section class="config-view">
    <div class="config-header">
      <h2>Training Config</h2>
      <button
        class="btn-secondary"
        data-testid="save-preset-btn"
        @click="showDialog = true"
      >
        Save as Preset
      </button>
    </div>

    <div class="config-section">
      <h3>Preset</h3>
      <div class="form-group">
        <select
          data-testid="preset-select"
          :value="selectedPreset?.name || ''"
          @change="(e) => {
            const name = e.target.value
            const preset = presets.find(p => p.name === name)
            if (preset) applyPreset(preset)
          }"
        >
          <option value="">-- Select Preset --</option>
          <optgroup label="Built-in Presets">
            <option
              v-for="preset in presetOptions.builtin"
              :key="preset.name"
              :value="preset.name"
            >
              {{ preset.name }} ({{ preset.type }})
            </option>
          </optgroup>
          <optgroup label="Custom Presets" v-if="presetOptions.custom.length">
            <option
              v-for="preset in presetOptions.custom"
              :key="preset.name"
              :value="preset.name"
            >
              {{ preset.name }} (custom)
            </option>
          </optgroup>
        </select>
      </div>
    </div>

    <div class="config-section">
      <h3>ML Parameters</h3>
      <div class="form-group">
        <label for="learning-rate">Learning Rate</label>
        <input
          id="learning-rate"
          type="number"
          step="0.0001"
          data-testid="learning-rate"
          v-model.number="learningRate"
        />
      </div>
      <div class="form-group">
        <label for="batch-size">Batch Size</label>
        <input
          id="batch-size"
          type="number"
          data-testid="batch-size"
          v-model.number="batchSize"
        />
      </div>
      <div class="form-group">
        <label for="epochs">Epochs</label>
        <input
          id="epochs"
          type="number"
          data-testid="epochs"
          v-model.number="epochs"
        />
      </div>
    </div>

    <div class="config-section">
      <h3>Target Mode</h3>
      <div class="radio-group" data-testid="target-mode">
        <label>
          <input
            type="radio"
            value="offline"
            v-model="targetMode"
          />
          Offline
        </label>
        <label>
          <input
            type="radio"
            value="realtime"
            v-model="targetMode"
          />
          Realtime
        </label>
      </div>
    </div>

    <div class="config-section">
      <h3>GPU Requirements</h3>
      <div class="gpu-info" data-testid="gpu-info">
        <div>Suggested GPU: NVIDIA RTX 3060+ (12GB VRAM)</div>
        <div>Estimated training time: ~2 hours for 100 epochs</div>
      </div>
    </div>

    <div class="config-section" v-if="isClamping && clampMessages.length">
      <h3>Constraint Warnings</h3>
      <div v-for="(msg, idx) in clampMessages" :key="idx">
        <span class="clamp-warning" data-testid="clamp-warning">{{ msg }}</span>
      </div>
    </div>

    <div class="btn-row">
      <button
        class="btn-primary"
        data-testid="start-training-btn"
        @click="handleStartTraining"
      >
        Start Training
      </button>
    </div>

    <div
      v-if="validationResult"
      class="validation-result"
      :class="validationResult.ok ? 'ok' : 'err'"
      data-testid="validation-result"
    >
      {{ validationResult.message }}
    </div>

    <PresetSaveDialog
      :show="showDialog"
      :currentConfig="{
        learning_rate: learningRate,
        batch_size: batchSize,
        epochs: epochs,
        target_mode: targetMode,
        parameters: {
          hidden_dim: selectedPreset?.parameters?.hidden_dim ?? 128,
          encoder_dim: selectedPreset?.parameters?.encoder_dim ?? 128,
          decoder_dim: selectedPreset?.parameters?.decoder_dim ?? 128,
          postnet_dim: selectedPreset?.parameters?.postnet_dim ?? 128,
          sample_rate: selectedPreset?.parameters?.sample_rate ?? 44100,
          n_harmonics: selectedPreset?.parameters?.n_harmonics ?? 32,
          n_trees: selectedPreset?.parameters?.n_trees ?? 50
        }
      }"
      @close="showDialog = false"
      @save="(payload) => {
        showDialog = false
        if (apiClient) {
          apiClient.createPreset(payload).then(() => {
            apiClient.listPresets().then(newPresets => {
              presets.value = newPresets
              if (payload.name) {
                const newPreset = newPresets.find(p => p.name === payload.name)
                if (newPreset) applyPreset(newPreset)
              }
            })
          })
        }
      }"
    />
  </section>
</template>

<style scoped>
.config-view { max-width: 900px; }
.config-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.config-section { margin-bottom: 1.5rem; }
.config-section h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group input, .form-group select { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: var(--accent); }
.radio-group { display: flex; gap: 1.5rem; }
.radio-group label { display: flex; align-items: center; gap: 0.375rem; font-size: 0.875rem; color: var(--text-primary); cursor: pointer; }
.gpu-info { padding: 0.75rem 1rem; background: var(--bg-tertiary); border-radius: 6px; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }
.clamp-warning { display: inline-block; padding: 0.125rem 0.5rem; background: var(--warning); color: #000; border-radius: 4px; font-size: 0.75rem; margin-top: 0.25rem; }
.btn-row { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.btn-primary { padding: 0.5rem 1.5rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { padding: 0.5rem 1.5rem; background: transparent; color: var(--text-primary); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; }
.btn-secondary:hover { background: var(--bg-tertiary); }
.validation-result { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.875rem; }
.validation-result.ok { background: var(--success); color: #000; }
.validation-result.err { background: var(--error); color: #fff; }
</style>
