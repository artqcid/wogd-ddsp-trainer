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
const trainingSpeed = ref('NORMAL')
const decoderType = ref('gru')
const useReverb = ref(true)
const nHarmonics = ref(60)
const nFilterBanks = ref(32)
const gpuInfo = ref(null)
const showVramWarning = ref(false)
const vramAdjustmentParams = ref(null)
const nVoices = ref(1)

const presetOptions = computed(() => {
  const builtin = presets.value.filter(p => p.is_builtin === true)
  const custom = presets.value.filter(p => p.is_builtin !== true)
  return { builtin, custom }
})

const currentParams = computed(() => {
  const p = selectedPreset.value?.params || {}
  return {
    learning_rate: learningRate.value,
    batch_size: batchSize.value,
    epochs: epochs.value,
    n_harmonics: p.n_harmonics ?? nHarmonics.value,
    n_filter_banks: p.n_filter_banks ?? nFilterBanks.value,
    hidden_size: p.hidden_size ?? 256,
    stft_scales: 3,
    mixed_precision: p.mixed_precision ?? 'required',
    gradient_checkpointing: p.gradient_checkpointing ?? 'optional',
    decoder_type: p.decoder_type ?? 'gru',
    use_reverb: p.use_reverb ?? true,
    n_voices: nVoices.value,
  }
})

const gpuDisplay = computed(() => {
  if (!gpuInfo.value?.gpus?.length) return null
  const gpu = gpuInfo.value.gpus[0]
  return {
    name: gpu.name,
    totalVram: gpu.total_vram_gb.toFixed(1),
    availableVram: gpu.available_vram_gb.toFixed(1),
    tier: gpuInfo.value.tier,
  }
})

function applyPreset(preset) {
  selectedPreset.value = preset
  isClamping.value = false
  clampMessages.value = []
  if (preset?.params) {
    learningRate.value = preset.params.learning_rate ?? 0.001
    batchSize.value = preset.params.batch_size ?? 32
    epochs.value = preset.params.epochs ?? 100
    nHarmonics.value = preset.params.n_harmonics ?? 60
    nFilterBanks.value = preset.params.n_filter_banks ?? 32
  }
  validateCurrentConfig()
}

async function validateCurrentConfig() {
  if (!apiClient) return
  try {
    const result = await apiClient.validatePreset(currentParams.value, trainingSpeed.value)
    if (!result.fits_gpu) {
      showVramWarning.value = true
      vramAdjustmentParams.value = result.clamped_params
    } else {
      showVramWarning.value = false
      vramAdjustmentParams.value = null
    }
  } catch {
    showVramWarning.value = false
  }
}

function onSpeedChange(speed) {
  trainingSpeed.value = speed
  validateCurrentConfig()
}

function acceptVramAdjustment() {
  if (!vramAdjustmentParams.value || !selectedPreset.value) return
  showVramWarning.value = false
  const adj = vramAdjustmentParams.value
  if (adj.hidden_size !== undefined) {
    selectedPreset.value = {
      ...selectedPreset.value,
      params: {
        ...selectedPreset.value.params,
        hidden_size: adj.hidden_size,
      }
    }
  }
  if (adj.n_harmonics !== undefined) {
    selectedPreset.value = {
      ...selectedPreset.value,
      params: {
        ...selectedPreset.value.params,
        n_harmonics: adj.n_harmonics,
      }
    }
  }
  if (adj.n_filter_banks !== undefined) {
    selectedPreset.value = {
      ...selectedPreset.value,
      params: {
        ...selectedPreset.value.params,
        n_filter_banks: adj.n_filter_banks,
      }
    }
  }
  vramAdjustmentParams.value = null
}

function dismissVramWarning() {
  showVramWarning.value = false
  vramAdjustmentParams.value = null
}

onMounted(async () => {
  if (!apiClient) return
  try {
    presets.value = await apiClient.listPresets()
  } catch (e) {
    console.error('Failed to load presets:', e)
  }
  try {
    gpuInfo.value = await apiClient.getHostInfo()
  } catch (e) {
    console.error('Failed to load GPU info:', e)
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
    training_speed: trainingSpeed.value,
    preset: selectedPreset.value?.name || null,
    parameters: {
      hidden_size: selectedPreset.value?.params?.hidden_size ?? 256,
      stft_scales: selectedPreset.value?.params?.stft_scales ?? 3,
      mixed_precision: selectedPreset.value?.params?.mixed_precision ?? 'required',
      gradient_checkpointing: selectedPreset.value?.params?.gradient_checkpointing ?? 'optional',
      decoder_type: selectedPreset.value?.params?.decoder_type ?? 'gru',
      use_reverb: selectedPreset.value?.params?.use_reverb ?? true,
      n_harmonics: selectedPreset.value?.params?.n_harmonics ?? nHarmonics.value,
      n_filter_banks: selectedPreset.value?.params?.n_filter_banks ?? nFilterBanks.value,
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
              {{ preset.name }}
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
      <h3>Decoder</h3>
      <div class="form-group">
        <label for="decoder-type">Decoder Type</label>
        <select id="decoder-type" v-model="decoderType" data-testid="decoder-type">
          <option value="gru">GRU</option>
          <option value="rnn">RNN</option>
        </select>
      </div>
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="useReverb" data-testid="use-reverb" />
          Enable Reverb
        </label>
      </div>
      <div class="form-group">
        <label for="n-harmonics">Number of Harmonics</label>
        <input
          id="n-harmonics"
          type="number"
          min="20"
          max="120"
          data-testid="n-harmonics"
          v-model.number="nHarmonics"
        />
      </div>
      <div class="form-group">
        <label for="n-filter-banks">Number of Filter Banks</label>
        <input
          id="n-filter-banks"
          type="number"
          min="16"
          max="64"
          data-testid="n-filter-banks"
          v-model.number="nFilterBanks"
        />
      </div>
    </div>

    <div class="config-section">
      <h3>Training Speed</h3>
      <div class="radio-group" data-testid="training-speed">
        <label>
          <input
            type="radio"
            value="FAST"
            :checked="trainingSpeed === 'FAST'"
            data-testid="speed-FAST"
            @change="onSpeedChange('FAST')"
          />
          FAST (0.5x hidden_size, max speed)
        </label>
        <label>
          <input
            type="radio"
            value="NORMAL"
            :checked="trainingSpeed === 'NORMAL'"
            data-testid="speed-NORMAL"
            @change="onSpeedChange('NORMAL')"
          />
          NORMAL (0.75x, default)
        </label>
        <label>
          <input
            type="radio"
            value="QUALITY"
            :checked="trainingSpeed === 'QUALITY'"
            data-testid="speed-QUALITY"
            @change="onSpeedChange('QUALITY')"
          />
          QUALITY (0.9x, best quality)
        </label>
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
      <h3>GPU</h3>
      <div class="gpu-info" data-testid="gpu-info">
        <template v-if="gpuDisplay">
          <div>{{ gpuDisplay.name }} ({{ gpuDisplay.totalVram }}GB VRAM, {{ gpuDisplay.availableVram }}GB available)</div>
          <div>Tier: {{ gpuDisplay.tier }}</div>
        </template>
        <div v-else>No GPU detected</div>
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

    <div v-if="showVramWarning" class="popup-overlay" data-testid="vram-popup">
      <div class="popup-box">
        <h4>VRAM-Warnung</h4>
        <p>Die gewählte Konfiguration überschreitet den verfügbaren VRAM. Möchten Sie die empfohlenen Anpassungen übernehmen?</p>
        <div class="popup-actions">
          <button class="btn-primary" @click="acceptVramAdjustment">Anpassungen annehmen</button>
          <button class="btn-secondary" @click="dismissVramWarning">Abbrechen</button>
      <div class="config-section">
        <h3>Polyphony</h3>
        <div class="form-group">
          <label for="n-voices">Number of Voices</label>
          <input
            id="n-voices"
            type="number"
            min="1"
            max="4"
            data-testid="n-voices"
            v-model.number="nVoices"
          />
          <p v-if="nVoices > 2" class="hint-warning">N voices × ~500 MB. Reduce hidden_size if VRAM is tight.</p>
        </div>
      </div>
    </div>
      </div>
    </div>

    <PresetSaveDialog
      :show="showDialog"
      :currentConfig="{
        learning_rate: learningRate,
        batch_size: batchSize,
        epochs: epochs,
        target_mode: targetMode,
        training_speed: trainingSpeed,
      parameters: {
        hidden_size: selectedPreset?.params?.hidden_size ?? 256,
        stft_scales: selectedPreset?.params?.stft_scales ?? 3,
        mixed_precision: selectedPreset?.params?.mixed_precision ?? 'required',
        gradient_checkpointing: selectedPreset?.params?.gradient_checkpointing ?? 'optional',
        decoder_type: selectedPreset?.params?.decoder_type ?? 'gru',
        use_reverb: selectedPreset?.params?.use_reverb ?? true,
         n_harmonics: selectedPreset?.params?.n_harmonics ?? nHarmonics,
         n_filter_banks: selectedPreset?.params?.n_filter_banks ?? nFilterBanks,
         n_voices: nVoices,
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

.popup-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.popup-box {
  background: var(--bg-primary); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.5rem; max-width: 480px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.popup-box h4 { margin: 0 0 0.75rem; font-size: 1rem; color: var(--text-primary); }
.popup-box p { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5; margin: 0 0 1.25rem; }
.popup-actions { display: flex; gap: 0.75rem; justify-content: flex-end; }
.checkbox-label { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.hint-warning { font-size: 0.75rem; color: var(--warning); margin-top: 0.25rem; }
</style>