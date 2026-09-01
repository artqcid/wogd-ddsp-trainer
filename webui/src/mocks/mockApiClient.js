import {
  healthFixture,
  uploadDatasetFixture,
  datasetsFixture,
  datasetFixture,
  deleteDatasetFixture,
  validateConfigFixture,
  startRunFixture,
  runsFixture,
  runFixture,
  stopRunFixture,
  resumeRunFixture,
  deleteRunFixture,
  presetsFixture,
  createPresetFixture,
  updatePresetFixture,
  deletePresetFixture,
  createPresetFromRunFixture,
  synthesizeFixture,
  inferenceJobFixture,
  inferenceArtifactsFixture,
  modelsFixture,
  downloadModelFixture,
  tensorboardFixture,
  settingsFixture,
  gpuHostInfoFixture,
  validatePresetFixture,
  morphFixture,
  voiceConvertFixture,
  tierFeasibilityFixture,
} from './fixtures.js'

/**
 * Mock implementation of the API-client abstraction.
 *
 * Returns deterministic fixtures instead of calling the backend. Used for
 * offline dev mode and Vitest rendering tests (mock-data seam).
 */
export class MockApiClient {
  async health() {
    return { ...healthFixture }
  }

  async uploadDataset() {
    return { ...uploadDatasetFixture }
  }

  async listDatasets() {
    return [...datasetsFixture]
  }

  async getDataset() {
    return { ...datasetFixture }
  }

  async deleteDataset() {
    return { ...deleteDatasetFixture }
  }

  async validateConfig() {
    return { ...validateConfigFixture }
  }

  async startRun() {
    return { ...startRunFixture }
  }

  async listRuns() {
    return [...runsFixture]
  }

  async getRun() {
    return { ...runFixture }
  }

  async stopRun() {
    return { ...stopRunFixture }
  }

  async resumeRun() {
    return { ...resumeRunFixture }
  }

  async deleteRun() {
    return { ...deleteRunFixture }
  }

  async listPresets() {
    return [...presetsFixture]
  }

  async createPreset() {
    return { ...createPresetFixture }
  }

  async updatePreset() {
    return { ...updatePresetFixture }
  }

  async deletePreset() {
    return { ...deletePresetFixture }
  }

  async createPresetFromRun() {
    return { ...createPresetFromRunFixture }
  }

  async synthesize() {
    return { ...synthesizeFixture }
  }

  async getInferenceJob() {
    return { ...inferenceJobFixture }
  }

  async getInferenceArtifacts() {
    return [...inferenceArtifactsFixture]
  }

  async listModels() {
    return [...modelsFixture]
  }

  async downloadModel() {
    return downloadModelFixture
  }

  async getTensorboard() {
    return { ...tensorboardFixture }
  }

  async getSettings() {
    return { ...settingsFixture }
  }

  async updateSettings(dataDir) {
    return {
      ...settingsFixture,
      data_dir: dataDir || settingsFixture.data_dir,
      data_is_default: !dataDir,
      datasets_dir: dataDir ? `${dataDir}/datasets` : settingsFixture.datasets_dir,
      runs_dir: dataDir ? `${dataDir}/runs` : settingsFixture.runs_dir,
      db_path: dataDir ? `${dataDir}/wogd-trainer.db` : settingsFixture.db_path,
    }
  }

  async getHostInfo() {
    return { ...gpuHostInfoFixture }
  }

  async getGPUInfo() {
    return this.getHostInfo()
  }

  async validatePreset(params, training_speed) {
    return validatePresetFixture(params, training_speed)
  }

  async injectIr() {
    return { status: 'ok' }
  }

  async extractIrUrl(runId) {
    return '/api/reverb/ir-extract/' + runId
  }

  async getFeatures() {
    const len = 100
    return {
      f0_hz: Array.from({ length: len }, () => Math.random() * 600 + 50),
      f0_confidence: Array.from({ length: len }, () => Math.random()),
      loudness_db: Array.from({ length: len }, () => Math.random() * 60 - 60),
    }
  }

  async morph(formData) {
    return { ...morphFixture }
  }

  async getGpuFeasibility(_params) {
    return { ...tierFeasibilityFixture }
  }

  async voiceConvert() {
    return { ...voiceConvertFixture }
  }
}
