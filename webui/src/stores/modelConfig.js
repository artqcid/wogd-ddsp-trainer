import { defineStore } from 'pinia'

export const useModelConfigStore = defineStore('modelConfig', {
  state: () => ({
    activeTier: null,
    wizardCompleted: false,
    gpuFeasibility: null,
    selectedPreset: null,
    targetMode: 'offline',
    synthesisMode: 'audio_fx', // 'audio_fx' | 'midi_synth' | 'both'
    coreParams: {
      learning_rate: 0.001,
      batch_size: 1,
      epochs: 100,
      decoder_type: 'gru',
      use_reverb: true,
    },
    componentParams: { n_harmonics: 60, n_filter_banks: 32 },
    hacksVariant: {},
    engineParams: { engine: 'harmonic', noise_color: 'white', newt_hidden_size: 64, newt_n_layers: 4 },
    advancedParams: {
      use_latent: false, latent_dim: 32, kl_beta: 1.0,
      n_voices: 1,
      use_content_encoder: false, content_encoder_name: 'hubert-soft',
    },
  }),
  getters: {
    isFeasible: (state) => state.gpuFeasibility?.fits ?? true,
    currentTierFeasibility: (state) =>
      state.gpuFeasibility?.tier_feasibility ?? {},
    wizardRequired: (state) => !state.wizardCompleted,
  },
  actions: {
    setTierFromWizard(tier, preset, targetMode, synthesisMode = 'audio_fx') {
      this.activeTier = tier
      this.wizardCompleted = true
      this.selectedPreset = preset
      this.targetMode = targetMode
      this.synthesisMode = synthesisMode
    },
    setSynthesisMode(mode) {
      this.synthesisMode = mode
    },
    async checkFeasibility(apiClient) {
      const p = this.advancedParams
      this.gpuFeasibility = await apiClient.getGpuFeasibility({
        model_tier: this.activeTier ?? 'standard',
        n_voices: p.n_voices,
        use_latent: p.use_latent,
        use_content_encoder: p.use_content_encoder,
      })
    },
    resetToWizard() {
      this.activeTier = null
      this.wizardCompleted = false
      this.synthesisMode = 'audio_fx'
    },
    buildFullConfig() {
      const config = {
        ...this.coreParams,
        model_tier: this.activeTier ?? 'standard',
        target_mode: this.targetMode,
        ...this.componentParams,
      }
      if (this.activeTier === 'hacks' || this.activeTier === 'engine' || this.activeTier === 'advanced') {
        config.variant = { ...this.hacksVariant }
      }
      if (this.activeTier === 'engine' || this.activeTier === 'advanced') {
        config.engine = this.engineParams.engine
        config.noise_color = this.engineParams.noise_color
        if (this.engineParams.engine === 'newt') {
          config.newt_hidden_size = this.engineParams.newt_hidden_size
          config.newt_n_layers = this.engineParams.newt_n_layers
        }
      }
      if (this.activeTier === 'advanced') {
        Object.assign(config, this.advancedParams)
      }
      config.synthesis_mode = this.synthesisMode
      return config
    },
  },
})