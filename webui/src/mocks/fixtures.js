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
  { name: 'vctk_default', type: 'autovc', parameters: { hidden_dim: 128, encoder_dim: 128, decoder_dim: 128, postnet_dim: 128 } },
  { name: 'singing_model', type: 'dsp-autoencoder', parameters: { hidden_dim: 256, encoder_dim: 256, decoder_dim: 256, postnet_dim: 256, sample_rate: 44100 } },
]

export const createPresetFixture = { name: 'custom_voice', type: 'autovc', parameters: { hidden_dim: 128, encoder_dim: 128, decoder_dim: 128, postnet_dim: 128 } }

export const updatePresetFixture = { success: true }

export const deletePresetFixture = { success: true }

export const createPresetFromRunFixture = { name: 'run_v1_preset', type: 'autovc', parameters: { hidden_dim: 128, encoder_dim: 128, decoder_dim: 128, postnet_dim: 128 } }

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
  { run_id: 'run_abc123', checkpoints: ['checkpoint_50.h5', 'checkpoint_100.h5'], created_at: '2024-01-15T10:30:00Z' },
  { run_id: 'run_def456', checkpoints: ['checkpoint_30.h5', 'checkpoint_45.h5'], created_at: '2024-02-20T14:00:00Z' },
]

export const downloadModelFixture = null // Blob returned by download endpoint

export const tensorboardFixture = { url: 'https://localhost:6006', running: true, port: 6006 }
