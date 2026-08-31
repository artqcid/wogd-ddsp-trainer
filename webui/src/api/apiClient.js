/**
 * API-client abstraction (mock-data seam).
 *
 * The web UI must never import backend code directly. All data access flows
 * through an object implementing the methods declared here. In development and
 * tests we inject `MockApiClient` from `../mocks/mockApiClient.js`; against a
 * running backend we inject a REST implementation.
 */

const healthKey = 'ApiClient.health'

export class ApiClient {
  /** @returns {Promise<{status: string, backend: string, version: string}>} */
  async health() {
    throw new Error(`${healthKey} not implemented`)
  }

  /** @returns {Promise<{id: string, name: string, status: string, file_count: number, files: Array}>} */
  async uploadDataset(file) {
    throw new Error('ApiClient.uploadDataset not implemented')
  }

  /** @returns {Promise<Array<{id: string, name: string, status: string, file_count: number, files: Array}>>} */
  async listDatasets() {
    throw new Error('ApiClient.listDatasets not implemented')
  }

  /** @returns {Promise<{id: string, name: string, status: string, file_count: number, files: Array}>} */
  async getDataset(id) {
    throw new Error('ApiClient.getDataset not implemented')
  }

  /** @returns {Promise<{success: boolean}>} */
  async deleteDataset(id) {
    throw new Error('ApiClient.deleteDataset not implemented')
  }

  /** @returns {Promise<{valid: boolean, errors: Array<string>}>} */
  async validateConfig(config) {
    throw new Error('ApiClient.validateConfig not implemented')
  }

  /** @returns {Promise<{run_id: string, status: string}>} */
  async startRun(config) {
    throw new Error('ApiClient.startRun not implemented')
  }

  /** @returns {Promise<Array<{run_id: string, name: string, status: string, dataset: string, epoch: number, max_epochs: number, ...}>>} */
  async listRuns() {
    throw new Error('ApiClient.listRuns not implemented')
  }

  /** @returns {Promise<{run_id: string, name: string, status: string, dataset: string, epoch: number, max_epochs: number, loss: number, created_at: string}>} */
  async getRun(id) {
    throw new Error('ApiClient.getRun not implemented')
  }

  /** @returns {Promise<{success: boolean}>} */
  async stopRun(id) {
    throw new Error('ApiClient.stopRun not implemented')
  }

  /** @returns {Promise<{success: boolean}>} */
  async resumeRun(id) {
    throw new Error('ApiClient.resumeRun not implemented')
  }

  /** @returns {Promise<{success: boolean}>} */
  async deleteRun(id) {
    throw new Error('ApiClient.deleteRun not implemented')
  }

  /** @returns {Promise<Array<{name: string, type: string, parameters: object}>>} */
  async listPresets() {
    throw new Error('ApiClient.listPresets not implemented')
  }

  /** @returns {Promise<{name: string, type: string, parameters: object}>} */
  async createPreset(preset) {
    throw new Error('ApiClient.createPreset not implemented')
  }

  /** @returns {Promise<{success: boolean}>} */
  async updatePreset(id, preset) {
    throw new Error('ApiClient.updatePreset not implemented')
  }

  /** @returns {Promise<{success: boolean}>} */
  async deletePreset(id) {
    throw new Error('ApiClient.deletePreset not implemented')
  }

  /** @returns {Promise<{name: string, type: string, parameters: object}>} */
  async createPresetFromRun(runId) {
    throw new Error('ApiClient.createPresetFromRun not implemented')
  }

  /** @returns {Promise<{job_id: string, status: string}>} */
  async synthesize(params) {
    throw new Error('ApiClient.synthesize not implemented')
  }

  /** @returns {Promise<{job_id: string, status: string, audio_url: string, created_at: string}>} */
  async getInferenceJob(id) {
    throw new Error('ApiClient.getInferenceJob not implemented')
  }

  /** @returns {Promise<Array<{filename: string, url: string, size: number}>>} */
  async getInferenceArtifacts(id) {
    throw new Error('ApiClient.getInferenceArtifacts not implemented')
  }

  /** @returns {Promise<Array<{run_id: string, checkpoints: Array<string>, created_at: string}>>} */
  async listModels() {
    throw new Error('ApiClient.listModels not implemented')
  }

  /** @returns {Promise<Blob>} */
  async downloadModel(runId, checkpoint) {
    throw new Error('ApiClient.downloadModel not implemented')
  }

  /** @returns {Promise<{url: string, running: boolean, port: number}>} */
  async getTensorboard() {
    throw new Error('ApiClient.getTensorboard not implemented')
  }

  /** @returns {Promise<{install_dir: string, data_dir: string, db_path: string, datasets_dir: string, runs_dir: string, data_is_default: boolean}>} */
  async getSettings() {
    throw new Error('ApiClient.getSettings not implemented')
  }

  /**
   * @param {string|null} dataDir Absolute new data directory, or null to reset to default.
   * @returns {Promise<{install_dir: string, data_dir: string, db_path: string, datasets_dir: string, runs_dir: string, data_is_default: boolean}>}
   */
  async updateSettings(dataDir) {
    throw new Error('ApiClient.updateSettings not implemented')
  }

  /** @returns {Promise<{gpus: Array<{index: number, name: string, total_vram_gb: number, available_vram_gb: number}>, tier: string, bounds: object, presets: object}>} */
  async getHostInfo() {
    throw new Error('ApiClient.getHostInfo not implemented')
  }

  /** @returns {Promise<{gpus: Array, tier: string, bounds: object, presets: object}>} */
  async getGPUInfo() {
    return this.getHostInfo()
  }

  /**
   * @param {object} params Training parameters (hidden_size, stft_scales, etc.)
   * @param {"FAST"|"NORMAL"|"QUALITY"} training_speed
   * @returns {Promise<{original_params: object, speed_applied_params: object, clamped_params: object, clamped_fields: Array<string>, bounds: object, training_speed: string, fits_gpu: boolean}>}
   */
  async validatePreset(params, training_speed) {
    throw new Error('ApiClient.validatePreset not implemented')
  }
}
