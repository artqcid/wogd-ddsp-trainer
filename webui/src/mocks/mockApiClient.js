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
}
