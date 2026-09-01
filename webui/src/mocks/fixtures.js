/**
 * Mock-data fixtures (mock-data seam).
 *
 * Deterministic sample data used by `MockApiClient` so every view can render
 * offline / in Vitest without a running backend.
 */

export const healthFixture = {
  status: 'ok',
  backend: 'mock',
  version: '0.1.0',
}

export const uploadDatasetFixture = {
  id: 'ds_001',
  name: 'voice_samples',
  status: 'idle',
  file_count: 3,
  files: [{ filename: 'sample_01.wav', duration_seconds: 12.5 }, { filename: 'sample_02.wav', duration_seconds: 8.3 }, { filename: 'sample_03.wav', duration_seconds: 15.1 }],
}

export const datasetsFixture = [
  {
    id: 'ds_001',
    name: 'voice_samples',
    status: 'idle',
    file_count: 3,
    files: [{ filename: 'sample_01.wav', duration_seconds: 12.5 }, { filename: 'sample_02.wav', duration_seconds: 8.3 }],
  },
  {
    id: 'ds_002',
    name: 'singing_voice',
    status: 'ready',
    file_count: 5,
    files: [{ filename: 'singing_01.wav', duration_seconds: 20.1 }, { filename: 'singing_02.wav', duration_seconds: 18.4 }],
  },
]

export const datasetFixture = {
  id: 'ds_001',
  name: 'voice_samples',
  status: 'ready',
  file_count: 3,
  files: [{ filename: 'sample_01.wav', duration_seconds: 12.5 }, { filename: 'sample_02.wav', duration_seconds: 8.3 }, { filename: 'sample_03.wav', duration_seconds: 15.1 }],
}

export const deleteDatasetFixture = { success: true }

export const validateConfigFixture = { valid: true, errors: [] }

export const startRunFixture = { run_id: 'run_abc123', status: 'starting' }

export const runsFixture = [
  { run_id: 'run_abc123', name: 'training_run_v1', status: 'completed', dataset: 'ds_001', epoch: 100, max_epochs: 100, loss: 0.12, created_at: '2024-01-15T10:30:00Z' },
  { run_id: 'run_def456', name: 'training_run_v2', status: 'running', dataset: 'ds_002', epoch: 45, max_epochs: 100, loss: 0.35, created_at: '2024-02-20T14:00:00Z' },
  { run_id: 'run_ghi789', name: 'training_run_v3', status: 'idle', dataset: 'ds_001', epoch: 0, max_epochs: 50, loss: 0.00, created_at: '2024-03-01T09:00:00Z' },
]

export const runFixture = {
  run_id: 'run_abc123',
  name: 'training_run_v1',
  status: 'completed',
  dataset: 'ds_001',
  epoch: 100,
  max_epochs: 100,
  loss: 0.12,
  created_at: '2024-01-15T10:30:00Z',
}

export const stopRunFixture = { success: true }

export const resumeRunFixture = { success: true }

export const deleteRunFixture = { success: true }

export const presetsFixture = [
  { name: 'vctk_default', is_builtin: true, params: { hidden_size: 128, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'optional' } },
  { name: 'singing_model', is_builtin: true, params: { hidden_size: 256, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'optional' } },
]

export const createPresetFixture = { name: 'custom_voice', is_builtin: false, params: { hidden_size: 128, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'optional' } }

export const updatePresetFixture = { success: true }

export const deletePresetFixture = { success: true }

export const createPresetFromRunFixture = { name: 'run_v1_preset', is_builtin: false, params: { hidden_size: 128, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'optional' } }

export const synthesizeFixture = { job_id: 'job_synth_001', status: 'queued' }

export const inferenceJobFixture = {
  job_id: 'job_synth_001',
  status: 'completed',
  audio_url: 'https://storage.example.com/audio/job_synth_001.wav',
  created_at: '2024-03-10T16:00:00Z',
}

export const inferenceArtifactsFixture = [
  { filename: 'job_synth_001.wav', url: 'https://storage.example.com/audio/job_synth_001.wav', size: 2560000 },
  { filename: 'job_synth_001_metadata.json', url: 'https://storage.example.com/audio/job_synth_001_metadata.json', size: 4096 },
]

export const modelsFixture = [
  { run_id: 'run_abc123', checkpoints: ['step-50.pt', 'step-100.pt'], created_at: '2024-01-15T10:30:00Z' },
  { run_id: 'run_def456', checkpoints: ['step-30.pt', 'step-45.pt'], created_at: '2024-02-20T14:00:00Z' },
]

export const downloadModelFixture = null // Blob returned by download endpoint

export const tensorboardFixture = { url: 'https://localhost:6006', running: true, port: 6006 }

export const settingsFixture = {
  install_dir: 'C:/Program Files/wogd-ddsp-trainer',
  data_dir: 'C:/Users/demo/AppData/Local/wogd-ddsp-trainer',
  db_path: 'C:/Users/demo/AppData/Local/wogd-ddsp-trainer/wogd-trainer.db',
  datasets_dir: 'C:/Users/demo/AppData/Local/wogd-ddsp-trainer/datasets',
  runs_dir: 'C:/Users/demo/AppData/Local/wogd-ddsp-trainer/runs',
  data_is_default: true,
}

export const gpuHostInfoFixture = {
  gpus: [
    { index: 0, name: 'NVIDIA GeForce RTX 3060', total_vram_gb: 12.0, available_vram_gb: 10.5 },
  ],
  tier: 'mid',
  bounds: {
    hidden_size_min: 256,
    hidden_size_max: 512,
    stft_scales_min: 3,
    stft_scales_max: 3,
    mixed_precision: 'required',
    gradient_checkpointing: 'optional',
  },
  presets: {
    FAST: { hidden_size: 256, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'enabled', vram_usage_target: '25%' },
    NORMAL: { hidden_size: 384, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'optional', vram_usage_target: '50%' },
    QUALITY: { hidden_size: 512, stft_scales: 3, mixed_precision: 'required', gradient_checkpointing: 'disabled', vram_usage_target: '75%' },
  },
}

export const reverbInjectionFixture = {
  status: 'ok',
  run_id: 'run_abc123',
}

export const variantFixture = {
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
}

const _SPEED_FACTORS = {
  FAST: { hidden: 0.50, scales: 'min', mp: 'required', ckpt: 'enabled' },
  NORMAL: { hidden: 0.75, scales: 'keep', mp: 'tier', ckpt: 'tier' },
  QUALITY: { hidden: 0.90, scales: 'keep', mp: 'tier', ckpt: 'disabled' },
}

export function validatePresetFixture(params, training_speed) {
  const speed = training_speed || 'NORMAL'
  const factor = _SPEED_FACTORS[speed] || _SPEED_FACTORS.NORMAL
  const bounds = { ...gpuHostInfoFixture.bounds }

  const speedApplied = { ...params }
  if (typeof speedApplied.hidden_size === 'number') {
    speedApplied.hidden_size = Math.round(speedApplied.hidden_size * factor.hidden)
  }
  if (factor.scales === 'min') {
    speedApplied.stft_scales = bounds.stft_scales_min
  }
  if (factor.mp === 'required') {
    speedApplied.mixed_precision = 'required'
  } else if (factor.mp === 'tier') {
    speedApplied.mixed_precision = bounds.mixed_precision
  }
  if (factor.ckpt === 'enabled') {
    speedApplied.gradient_checkpointing = 'enabled'
  } else if (factor.ckpt === 'disabled') {
    speedApplied.gradient_checkpointing = 'disabled'
  } else if (factor.ckpt === 'tier') {
    speedApplied.gradient_checkpointing = bounds.gradient_checkpointing
  }

  const clampedParams = { ...speedApplied }
  const clampedFields = []
  if (clampedParams.hidden_size < bounds.hidden_size_min) {
    clampedParams.hidden_size = bounds.hidden_size_min
    clampedFields.push('hidden_size')
  } else if (clampedParams.hidden_size > bounds.hidden_size_max) {
    clampedParams.hidden_size = bounds.hidden_size_max
    clampedFields.push('hidden_size')
  }
  if (clampedParams.stft_scales < bounds.stft_scales_min) {
    clampedParams.stft_scales = bounds.stft_scales_min
    clampedFields.push('stft_scales')
  } else if (clampedParams.stft_scales > bounds.stft_scales_max) {
    clampedParams.stft_scales = bounds.stft_scales_max
    clampedFields.push('stft_scales')
  }
  if (clampedParams.learning_rate === undefined) {
    clampedParams.learning_rate = 0.001
  }

  return {
    original_params: { ...params },
    speed_applied_params: speedApplied,
    clamped_params: clampedParams,
    clamped_fields: clampedFields,
    bounds,
    training_speed: speed,
    fits_gpu: clampedFields.length === 0,
  }
}
