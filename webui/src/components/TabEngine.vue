<template>
  <div class="tab-engine" data-testid="tab-engine">
    <div v-if="store.synthesisMode === 'midi_synth' || store.synthesisMode === 'both'" class="midi-hint" data-testid="midi-hint-engine">
      <p v-if="store.engineParams.engine === 'sinusoidal'">🎹 <strong>MIDI Synth:</strong> Produces glass, bell, marimba-like inharmonic timbres via MIDI.</p>
      <p v-else-if="store.engineParams.engine === 'combsub'">🎹 <strong>MIDI Synth:</strong> Resonant body character — plucked strings, oud, sitar textures.</p>
      <p v-else-if="store.engineParams.engine === 'newt'">🎹 <strong>MIDI Synth:</strong> Neural waveshaping — unique distorted synth character.</p>
      <p v-else>🎹 <strong>MIDI Synth:</strong> Clean harmonic timbres with MIDI note control.</p>
    </div>
    <div class="form-group">
      <label class="form-label">Engine</label>
      <select class="form-select" v-model="store.engineParams.engine" data-testid="engine-select">
        <option value="harmonic">Harmonic</option>
        <option value="sinusoidal">Sinusoidal</option>
        <option value="combsub">Comb-Subtractive</option>
        <option value="newt">NEWT</option>
      </select>
    </div>
    <div class="form-group" v-if="store.engineParams.engine === 'combsub' || store.engineParams.engine === 'sinusoidal'">
      <label class="form-label">Noise Color</label>
      <select class="form-select" v-model="store.engineParams.noise_color" data-testid="noise-color">
        <option value="white">White</option>
        <option value="pink">Pink</option>
        <option value="brown">Brown</option>
      </select>
    </div>
    <div class="form-group" v-if="store.engineParams.engine === 'newt'">
      <label class="form-label">NEWT Hidden Size</label>
      <input class="form-input" type="number" min="16" max="256" v-model.number="store.engineParams.newt_hidden_size" data-testid="newt-hidden" />
    </div>
    <div class="form-group" v-if="store.engineParams.engine === 'newt'">
      <label class="form-label">NEWT Layers</label>
      <input class="form-input" type="number" min="1" max="8" v-model.number="store.engineParams.newt_n_layers" data-testid="newt-layers" />
    </div>
  </div>
</template>

<script setup>
import { useModelConfigStore } from '../stores/modelConfig.js'

const store = useModelConfigStore()
</script>

<style scoped>
.tab-engine { display: flex; flex-direction: column; gap: var(--space-3); }
.midi-hint {
  padding: var(--space-3);
  background: var(--bg-tertiary);
  border: 1px solid var(--tier-hacks);
  border-radius: var(--radius-md);
  font-size: 0.8rem;
  margin-bottom: var(--space-3);
}
.midi-hint p { margin: 0; color: var(--text-secondary); }
.midi-hint strong { color: var(--text-primary); }
</style>
