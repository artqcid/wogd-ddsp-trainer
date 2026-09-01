<template>
  <div class="tab-advanced" data-testid="tab-advanced">
    <div v-if="store.synthesisMode === 'midi_synth' || store.synthesisMode === 'both'" class="midi-hint" data-testid="midi-hint-advanced">
      <p v-if="store.advancedParams.use_latent">🎹 <strong>MIDI Synth:</strong> Latent Z sliders morph the timbre in real time while playing MIDI. Unique expressive instrument.</p>
      <p v-else-if="store.advancedParams.n_voices > 1">🎹 <strong>MIDI Synth:</strong> Each MIDI note routes to one PolyDDSP voice (up to N). Enables polyphonic chords.</p>
      <p v-else-if="store.advancedParams.use_content_encoder">🎹 <strong>MIDI Synth:</strong> Hybrid mode: MIDI drives pitch, a reference audio sample sets the source timbre.</p>
      <p v-else>🎹 <strong>MIDI Synth:</strong> Full MIDI control with advanced model features.</p>
    </div>
    <div class="adv-section">
      <h4 class="adv-section-title">VAE / Latent Space</h4>
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="store.advancedParams.use_latent" data-testid="use-latent" />
          Use Latent (VAE)
        </label>
      </div>
      <div class="form-group" v-if="store.advancedParams.use_latent">
        <label class="form-label">Latent Dim</label>
        <input class="form-input" type="number" min="8" max="128" v-model.number="store.advancedParams.latent_dim" data-testid="latent-dim" />
      </div>
      <div class="form-group" v-if="store.advancedParams.use_latent">
        <label class="form-label">KL Beta</label>
        <input class="form-input" type="number" step="0.1" min="0" max="10" v-model.number="store.advancedParams.kl_beta" data-testid="kl-beta" />
      </div>
    </div>

    <div class="adv-section">
      <h4 class="adv-section-title">Polyphony</h4>
      <div class="form-group">
        <label class="form-label">Number of Voices</label>
        <input class="form-input" type="number" min="1" max="4" v-model.number="store.advancedParams.n_voices" data-testid="n-voices" />
        <p v-if="store.advancedParams.n_voices > 2" class="hint-warning">N voices × ~2.2 GB. Ensure sufficient VRAM.</p>
      </div>
    </div>

    <div class="adv-section">
      <h4 class="adv-section-title">Voice Conversion</h4>
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="store.advancedParams.use_content_encoder" data-testid="use-content-encoder" />
          Use Content Encoder
        </label>
      </div>
      <div class="form-group" v-if="store.advancedParams.use_content_encoder">
        <label class="form-label">Encoder</label>
        <select class="form-select" v-model="store.advancedParams.content_encoder_name" data-testid="content-encoder">
          <option value="hubert-soft">HuBERT-Soft</option>
          <option value="contentvec">ContentVec</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useModelConfigStore } from '../stores/modelConfig.js'

const store = useModelConfigStore()
</script>

<style scoped>
.tab-advanced { display: flex; flex-direction: column; gap: var(--space-4); }
.adv-section {
  padding: var(--space-3);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}
.adv-section-title {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--tier-advanced);
  margin-bottom: var(--space-3);
}
.form-group { margin-bottom: var(--space-2); }
.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  cursor: pointer;
}
.hint-warning { font-size: 0.75rem; color: var(--warning); margin-top: var(--space-1); }
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
