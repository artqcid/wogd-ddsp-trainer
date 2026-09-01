<script setup>
import { inject, reactive, ref, computed } from 'vue'

const apiClient = inject('apiClient')

const variant = reactive({
  engine: 'harmonic',
  noise_color: 'white',
  noise_grain_jitter: 0,
  harmonic_ratios: null,
  waveform: 'sin',
  pd_k: 0,
  use_trainable_wavetable: false,
  fm_depth: 0,
  fm_ratio: 2,
  loss_band_mask: null,
  lfo_freq: 0,
  lfo_depth: 0,
  use_angular_cumsum: false,
  newt_n_hidden: 32,
  newt_n_layers: 4,
})

const bandMaskRows = ref([])
const nextBandRowId = ref(0)

function parseBandMask() {
  if (!variant.loss_band_mask) return []
  try {
    const parsed = JSON.parse(variant.loss_band_mask)
    if (Array.isArray(parsed)) {
      return parsed.map((row) => {
        const low = Number(row[0]) || 0
        const high = Number(row[1]) || 0
        return { id: crypto.randomUUID ? crypto.randomUUID() : String(nextBandRowId.value++), low, high }
      })
    }
  } catch {
    // malformed JSON, start fresh
  }
  return []
}

function syncBandMaskFromRows() {
  const pairs = bandMaskRows.value.map((row) => [row.low, row.high])
  variant.loss_band_mask = JSON.stringify(pairs)
}

function initBandMaskFromVariant() {
  bandMaskRows.value = parseBandMask()
}

function addBandRow(low = 0, high = 0) {
  bandMaskRows.value.push({
    id: crypto.randomUUID ? crypto.randomUUID() : String(nextBandRowId.value++),
    low,
    high,
  })
  syncBandMaskFromRows()
}

function removeBandRow(id) {
  bandMaskRows.value = bandMaskRows.value.filter((r) => r.id !== id)
  syncBandMaskFromRows()
}

function onBandLowChange(row, value) {
  row.low = Number(value) || 0
  syncBandMaskFromRows()
}

function onBandHighChange(row, value) {
  row.high = Number(value) || 0
  syncBandMaskFromRows()
}

const bandMaskPairs = computed(() => {
  return bandMaskRows.value.map((row) => [row.low, row.high])
})

initBandMaskFromVariant()
</script>

<template>
  <div class="synth-hacks-view">
    <h2>Experimental Synthesis Hacks</h2>

    <div class="card">
      <h3>Engine &amp; Noise</h3>
      <div class="row">
        <label class="label">Engine</label>
        <select v-model="variant.engine" class="select wide">
          <option value="harmonic">Harmonic (standard)</option>
          <option value="sinusoidal">Sinusoidal — free partials</option>
          <option value="combsub">CombSub — vocal formants</option>
          <option value="newt">NEWT — neural waveshaping</option>
        </select>
      </div>
      <div class="row" v-if="variant.engine === 'newt'">
        <label class="label">
          NEWT hidden units
          <span class="value-tag">{{ variant.newt_n_hidden }}</span>
        </label>
        <input type="range" min="8" max="128" step="1" v-model.number="variant.newt_n_hidden" class="slider" />
      </div>
      <div class="row" v-if="variant.engine === 'newt'">
        <label class="label">
          NEWT MLP depth
          <span class="value-tag">{{ variant.newt_n_layers }}</span>
        </label>
        <input type="range" min="2" max="8" step="1" v-model.number="variant.newt_n_layers" class="slider" />
      </div>
      </div>
      <div class="row">
        <label class="label">Noise colour</label>
        <select v-model="variant.noise_color" class="select wide">
          <option value="white">White</option>
          <option value="pink">Pink 1/f</option>
          <option value="brown">Brown 1/f²</option>
        </select>
      </div>
      <div class="row">
        <label class="label">
          Noise grain jitter
          <span class="value-tag">{{ variant.noise_grain_jitter.toFixed(1) }}</span>
        </label>
        <input
          type="range"
          min="0"
          max="5"
          step="0.1"
          v-model.number="variant.noise_grain_jitter"
          class="slider"
        />
      </div>
      <p v-if="variant.engine !== 'harmonic'" class="warning">
        ⚠ Engine-specific checkpoint — not compatible with standard runs.
      </p>
      <p v-if="variant.engine === 'newt'" class="warning">
        ⚠ NEWT checkpoints are not compatible with harmonic/combsub runs.
      </p>
    </div>

    <div class="card">
      <h3>Harmonic Oscillator Hacks</h3>
      <div class="row">
        <label class="label">Waveform</label>
        <select v-model="variant.waveform" class="select wide">
          <option value="sin">Sin</option>
          <option value="square">Square</option>
          <option value="saw">Saw</option>
        </select>
      </div>
      <div class="row">
        <label class="label">
          Phase distortion (k)
          <span class="value-tag">{{ variant.pd_k.toFixed(2) }}</span>
        </label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.01"
          v-model.number="variant.pd_k"
          class="slider"
        />
      </div>
      <div class="row two-col">
        <div class="field">
          <label class="label">
            FM depth
            <span class="value-tag">{{ variant.fm_depth.toFixed(2) }}</span>
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            v-model.number="variant.fm_depth"
            class="slider"
          />
        </div>
        <div class="field">
          <label class="label">FM ratio</label>
          <input
            type="number"
            min="1"
            max="8"
            step="0.1"
            v-model.number="variant.fm_ratio"
            class="input"
          />
        </div>
      </div>
      <div class="row">
        <label class="label">Inharmonic ratios</label>
        <textarea
          class="textarea"
          placeholder="e.g. 1.0, 1.414, 2.73"
          v-model="variant.harmonic_ratios"
          rows="3"
        ></textarea>
        <p class="hint">Optional, blank = None</p>
      </div>
      <div class="row">
        <label class="checkbox-label">
          <input type="checkbox" v-model="variant.use_trainable_wavetable" class="checkbox" />
          <span>Trainable wavetable</span>
          <span class="warning-inline">checkpoint incompatible with standard runs</span>
        </label>
      </div>
    </div>

    <div class="card">
      <h3>Loss Hacks</h3>
      <p class="hint">Band-mask editor — each row is a [low_hz, high_hz] passband. Empty = no mask.</p>
      <div class="band-mask">
        <div v-for="row in bandMaskRows" :key="row.id" class="band-row">
          <input
            type="number"
            class="input narrow"
            placeholder="low hz"
            :value="row.low"
            @input="onBandLowChange(row, $event.target.value)"
          />
          <span class="band-sep">→</span>
          <input
            type="number"
            class="input narrow"
            placeholder="high hz"
            :value="row.high"
            @input="onBandHighChange(row, $event.target.value)"
          />
          <button class="remove-btn" type="button" @click="removeBandRow(row.id)">X</button>
        </div>
      </div>
      <div class="band-actions">
        <button class="btn-secondary" type="button" @click="addBandRow(0, 0)">+ Add Band</button>
      </div>
    </div>

    <div class="card">
      <h3>Decoder Hacks</h3>
      <div class="row">
        <label class="label">
          LFO frequency
          <span class="value-tag">{{ variant.lfo_freq.toFixed(1) }} Hz</span>
        </label>
        <input
          type="range"
          min="0"
          max="20"
          step="0.1"
          v-model.number="variant.lfo_freq"
          class="slider"
        />
      </div>
      <div class="row">
        <label class="label">
          LFO depth
          <span class="value-tag">{{ variant.lfo_depth.toFixed(2) }}</span>
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          v-model.number="variant.lfo_depth"
          class="slider"
        />
      </div>
    </div>

    <div class="card">
      <h3>Quality</h3>
      <div class="row">
        <label class="checkbox-label">
          <input type="checkbox" v-model="variant.use_angular_cumsum" class="checkbox" />
          <span>Angular cumsum</span>
          <span class="hint-inline">reduces phase drift for &gt;6 s synthesis, ~10% slower</span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.synth-hacks-view {
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

.synth-hacks-view h2 {
  font-size: 1.5rem;
  margin: 0 0 1.5rem 0;
  color: var(--text);
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}

.card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
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

.row.two-col {
  flex-direction: row;
  gap: 1.2rem;
}

.row.two-col .field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
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
  width: 100%;
}

.select.wide {
  width: 100%;
}

.input {
  background: var(--bg-deep);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
  width: 100%;
}

.input.narrow {
  width: 100%;
}

.slider {
  width: 100%;
  accent-color: var(--accent);
}

.slider::-webkit-slider-thumb {
  accent-color: var(--accent);
}

.slider::-moz-range-thumb {
  accent-color: var(--accent);
}

.textarea {
  background: var(--bg-deep);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 8px;
  padding: 0.6rem 0.75rem;
  font-size: 0.9rem;
  font-family: inherit;
  width: 100%;
  resize: vertical;
}

.textarea::placeholder {
  color: var(--hint);
  opacity: 0.7;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox {
  accent-color: var(--accent);
  width: 1.1rem;
  height: 1.1rem;
}

.hint {
  font-size: 0.8rem;
  color: var(--hint);
  margin: 0.3rem 0 0 0;
}

.hint-inline {
  color: var(--hint);
  font-size: 0.82rem;
}

.warning-inline {
  color: var(--warning);
  font-size: 0.82rem;
}

.warning {
  margin: 0.8rem 0 0 0;
  padding: 0.6rem 0.8rem;
  background: rgba(245, 158, 11, 0.12);
  border-left: 3px solid var(--warning);
  color: var(--warning);
  border-radius: 4px;
  font-size: 0.88rem;
}

.band-mask {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.8rem;
}

.band-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.band-row .input {
  width: 45%;
}

.band-sep {
  color: var(--hint);
  font-size: 0.9rem;
}

.remove-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--warning);
  border-radius: 6px;
  padding: 0.3rem 0.6rem;
  cursor: pointer;
  font-size: 0.8rem;
  transition: background 0.15s;
}

.remove-btn:hover {
  background: rgba(245, 158, 11, 0.15);
}

.band-actions {
  margin-top: 0.3rem;
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--accent);
  color: var(--accent);
  border-radius: 8px;
  padding: 0.45rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.15s, color 0.15s;
}

.btn-secondary:hover {
  background: var(--accent);
  color: #fff;
}
</style>
