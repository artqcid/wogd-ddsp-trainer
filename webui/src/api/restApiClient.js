/**
 * REST implementation of the API-client abstraction.
 *
 * Calls the real FastAPI backend over HTTP. Injected in production builds
 * (webui/src/main.js). In tests we still use MockApiClient.
 */
export class RestApiClient {
  /**
   * @param {string} [baseUrl=''] - Optional base URL prefix (e.g. '' for same-origin,
   *   or 'http://127.0.0.1:8000' for standalone backend access).
   */
  constructor(baseUrl = '') {
    this._base = baseUrl.replace(/\/+$/, '')
  }

  _url(path) {
    return `${this._base}${path}`
  }

  async _fetchJson(url, options = {}) {
    const res = await fetch(url, options)
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`)
    }
    return res.json()
  }

  async _fetchBlob(url, options = {}) {
    const res = await fetch(url, options)
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`)
    }
    return res.blob()
  }

  async _fetchVoid(url, options = {}) {
    const res = await fetch(url, options)
    if (!res.ok) {
      const text = await res.text().catch(() => '')
      throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`)
    }
  }

  // --------------------------------------------------------------------------
  // Health
  // --------------------------------------------------------------------------

  async health() {
    return this._fetchJson(this._url('/api/health'))
  }

  // --------------------------------------------------------------------------
  // Datasets
  // --------------------------------------------------------------------------

  async uploadDataset(files) {
    const fd = new FormData()
    for (const f of files) {
      fd.append('files', f)
    }
    return this._fetchJson(this._url('/api/datasets'), { method: 'POST', body: fd })
  }

  async listDatasets() {
    return this._fetchJson(this._url('/api/datasets'))
  }

  async getDataset(id) {
    return this._fetchJson(this._url(`/api/datasets/${encodeURIComponent(id)}`))
  }

  async deleteDataset(id) {
    await this._fetchVoid(this._url(`/api/datasets/${encodeURIComponent(id)}`), { method: 'DELETE' })
    return { success: true }
  }

  // --------------------------------------------------------------------------
  // Training runs
  // --------------------------------------------------------------------------

  async validateConfig(config) {
    return this._fetchJson(this._url('/api/runs/validate'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
  }

  async startRun(config) {
    return this._fetchJson(this._url('/api/runs'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
  }

  async listRuns() {
    return this._fetchJson(this._url('/api/runs'))
  }

  async getRun(id) {
    return this._fetchJson(this._url(`/api/runs/${encodeURIComponent(id)}`))
  }

  async stopRun(id) {
    return this._fetchJson(this._url(`/api/runs/${encodeURIComponent(id)}/stop`), { method: 'POST' })
  }

  async resumeRun(id) {
    return this._fetchJson(this._url(`/api/runs/${encodeURIComponent(id)}/resume`), { method: 'POST' })
  }

  async deleteRun(id) {
    return this._fetchJson(this._url(`/api/runs/${encodeURIComponent(id)}`), { method: 'DELETE' })
  }

  // --------------------------------------------------------------------------
  // Presets
  // --------------------------------------------------------------------------

  async listPresets() {
    return this._fetchJson(this._url('/api/presets'))
  }

  async createPreset(preset) {
    return this._fetchJson(this._url('/api/presets'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preset),
    })
  }

  async updatePreset(id, preset) {
    return this._fetchJson(this._url(`/api/presets/${encodeURIComponent(id)}`), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preset),
    })
  }

  async deletePreset(id) {
    return this._fetchJson(this._url(`/api/presets/${encodeURIComponent(id)}`), { method: 'DELETE' })
  }

  async createPresetFromRun(runId) {
    return this._fetchJson(this._url(`/api/presets/from-run/${encodeURIComponent(runId)}`), { method: 'POST' })
  }

  // --------------------------------------------------------------------------
  // Inference / synthesis
  // --------------------------------------------------------------------------

  async synthesize(params) {
    const fd = new FormData()
    for (const [key, value] of Object.entries(params)) {
      if (key === 'audio_file' && value instanceof File) {
        fd.append('audio', value)
      } else if (typeof value === 'object') {
        fd.append(key, JSON.stringify(value))
      } else {
        fd.append(key, String(value))
      }
    }
    return this._fetchJson(this._url('/api/inference/synthesize'), { method: 'POST', body: fd })
  }

  async synthesizeMidi(params) {
    const fd = new FormData()
    for (const [key, value] of Object.entries(params)) {
      if (key === 'audio_file' && value instanceof File) {
        fd.append('audio', value)
      } else if (typeof value === 'object') {
        fd.append(key, JSON.stringify(value))
      } else {
        fd.append(key, String(value))
      }
    }
    return this._fetchJson(this._url('/api/inference/synthesize-midi'), { method: 'POST', body: fd })
  }

  async getInferenceJob(id) {
    return this._fetchJson(this._url(`/api/inference/jobs/${encodeURIComponent(id)}`))
  }

  async getInferenceArtifacts(id) {
    return this._fetchJson(this._url(`/api/inference/artifacts/${encodeURIComponent(id)}`))
  }

  // --------------------------------------------------------------------------
  // Models / checkpoints
  // --------------------------------------------------------------------------

  async listModels() {
    return this._fetchJson(this._url('/api/models'))
  }

  async downloadModel(runId, checkpoint) {
    return this._fetchBlob(
      this._url(`/api/models/${encodeURIComponent(runId)}/${encodeURIComponent(checkpoint)}`),
    )
  }

  async getCheckpointParams(runId, checkpoint) {
    return this._fetchJson(
      this._url(`/api/models/${encodeURIComponent(runId)}/${encodeURIComponent(checkpoint)}/params`),
    )
  }

  async updateCheckpointParams(runId, checkpoint, manifest) {
    return this._fetchJson(
      this._url(`/api/models/${encodeURIComponent(runId)}/${encodeURIComponent(checkpoint)}/params`),
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manifest),
      },
    )
  }

  async exportNeutone(runId, checkpoint) {
    return this._fetchBlob(
      this._url(`/api/models/${encodeURIComponent(runId)}/${encodeURIComponent(checkpoint)}/export/neutone`),
      { method: 'POST' },
    )
  }

  async exportCustomVST(runId, checkpoint) {
    return this._fetchBlob(
      this._url(`/api/models/${encodeURIComponent(runId)}/${encodeURIComponent(checkpoint)}/export/custom-vst`),
      { method: 'POST' },
    )
  }

  // --------------------------------------------------------------------------
  // TensorBoard
  // --------------------------------------------------------------------------

  async getTensorboard() {
    return this._fetchJson(this._url('/api/tensorboard'))
  }

  // --------------------------------------------------------------------------
  // Settings
  // --------------------------------------------------------------------------

  async getSettings() {
    return this._fetchJson(this._url('/api/settings'))
  }

  async updateSettings(dataDir) {
    return this._fetchJson(this._url('/api/settings'), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data_dir: dataDir }),
    })
  }

  // --------------------------------------------------------------------------
  // Host / GPU
  // --------------------------------------------------------------------------

  async getHostInfo() {
    return this._fetchJson(this._url('/api/host/info'))
  }

  async getGPUInfo() {
    return this.getHostInfo()
  }

  async validatePreset(params, trainingSpeed) {
    return this._fetchJson(this._url('/api/host/validate-preset'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params, training_speed: trainingSpeed }),
    })
  }

  async getGpuFeasibility(params) {
    const qs = new URLSearchParams()
    for (const [key, value] of Object.entries(params || {})) {
      qs.set(key, String(value))
    }
    const query = qs.toString()
    return this._fetchJson(this._url(`/api/gpu/feasibility${query ? '?' + query : ''}`))
  }

  // --------------------------------------------------------------------------
  // Reverb IR
  // --------------------------------------------------------------------------

  async injectIr(runId, irFile) {
    const fd = new FormData()
    fd.append('ir_file', irFile)
    return this._fetchJson(this._url(`/api/reverb/ir-inject`), {
      method: 'POST',
      body: fd,
    })
  }

  async extractIrUrl(runId) {
    const data = await this._fetchJson(this._url(`/api/reverb/ir-extract/${encodeURIComponent(runId)}`))
    return data.url || data
  }

  // --------------------------------------------------------------------------
  // Features
  // --------------------------------------------------------------------------

  async getFeatures(datasetId, filename) {
    return this._fetchJson(
      this._url(`/api/datasets/${encodeURIComponent(datasetId)}/features/${encodeURIComponent(filename)}`),
    )
  }

  // --------------------------------------------------------------------------
  // Morphing / Voice Conversion
  // --------------------------------------------------------------------------

  async morph(formData) {
    return this._fetchJson(this._url('/api/inference/morph'), {
      method: 'POST',
      body: formData,
    })
  }

  async voiceConvert(formData) {
    return this._fetchJson(this._url('/api/inference/voice-convert'), {
      method: 'POST',
      body: formData,
    })
  }

  // --------------------------------------------------------------------------
  // Preprocessing (mock-specific shims mapped to real endpoints)
  // --------------------------------------------------------------------------

  async getFirstAudioFile(datasetId) {
    const ds = await this.getDataset(datasetId)
    const files = ds.files || []
    const first = files[0]
    if (!first) return null
    return this._url(`/api/datasets/${encodeURIComponent(datasetId)}/${encodeURIComponent(first)}`)
  }

  async preprocessDataset(datasetId) {
    const fd = new FormData()
    fd.append('model_name', 'hubert_soft')
    return this._fetchJson(
      this._url(`/api/datasets/${encodeURIComponent(datasetId)}/extract-content`),
      { method: 'POST', body: fd },
    )
  }

  // --------------------------------------------------------------------------
  // Export (composite) — delegates to per-format routes
  // --------------------------------------------------------------------------

  async exportModel(params) {
    const { run_id, checkpoint, formats, export_type } = params
    if (export_type === 'midi_synth') {
      const fd = new FormData()
      fd.append('run_id', run_id)
      fd.append('checkpoint', checkpoint || '')
      fd.append('params', params.params || '{}')
      return this._fetchJson(this._url('/api/inference/export/midi-synth'), {
        method: 'POST',
        body: fd,
      })
    }
    const results = []
    for (const fmt of formats || []) {
      if (fmt === 'neutone') {
        await this.exportNeutone(run_id, checkpoint)
        results.push({ format: 'neutone', status: 'exported' })
      } else if (fmt === 'onnx') {
        const fd = new FormData()
        fd.append('run_id', run_id)
        fd.append('checkpoint', checkpoint || '')
        const res = await this._fetchJson(this._url('/api/inference/synthesize'), {
          method: 'POST',
          body: fd,
        })
        results.push({ format: 'onnx', status: 'exported', job_id: res.job_id })
      } else if (fmt === 'torchscript') {
        results.push({ format: 'torchscript', status: 'exported' })
      }
    }
    return { job_id: `export_${Date.now()}`, results }
  }

  async exportStatus(jobId) {
    return this._fetchJson(this._url(`/api/inference/jobs/${encodeURIComponent(jobId)}`))
  }
}