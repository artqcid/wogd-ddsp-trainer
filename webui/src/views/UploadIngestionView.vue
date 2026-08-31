<script setup>
import { inject, ref, nextTick, onBeforeUnmount, onMounted } from 'vue'
import WaveSurfer from 'wavesurfer.js'

const apiClient = inject('apiClient')

const ACCEPTED_EXTS = new Set(['wav', 'flac', 'ogg', 'mp3', 'm4a', 'mp4', 'aiff', 'aif'])

const files = ref([])
const isUploading = ref(false)
const uploadSuccess = ref(null)

const dropZone = ref(null)
const hintsExpanded = ref(false)

const waveformEls = ref({})

const uploadedWaveSurfers = ref({})

const isAccepted = (file) => {
  const ext = file.name.split('.').pop().toLowerCase()
  return ACCEPTED_EXTS.has(ext)
}

const classifyFile = (file) => {
  if (isAccepted(file)) return { status: 'ok', label: 'Accepted' }
  return { status: 'warn', label: `Type not supported` }
}

const handleDragOver = (e) => {
  e.preventDefault()
  if (dropZone.value) dropZone.value.classList.add('dragover')
}

const handleDragLeave = (e) => {
  e.preventDefault()
  if (dropZone.value) dropZone.value.classList.remove('dragover')
}

const handleDrop = async (e) => {
  e.preventDefault()
  if (dropZone.value) dropZone.value.classList.remove('dragover')

  const droppedFiles = Array.from(e.dataTransfer.files || [])
  for (const file of droppedFiles) {
    if (file.type.startsWith('audio/') || isAccepted(file)) {
      const entry = {
        file,
        ...classifyFile(file),
        id: crypto.randomUUID(),
      }
      files.value.push(entry)
    }
  }
}

const addFilesFromInput = (inputEvent) => {
  const selectedFiles = Array.from(inputEvent.target.files || [])
  for (const file of selectedFiles) {
    if (file.type.startsWith('audio/') || isAccepted(file)) {
      const entry = {
        file,
        ...classifyFile(file),
        id: crypto.randomUUID(),
      }
      files.value.push(entry)
    }
  }
  if (inputEvent.target) inputEvent.target.value = ''
}

const renderWaveform = async (fileItem) => {
  if (uploadedWaveSurfers.value[fileItem.id]) return
  const el = waveformEls.value[fileItem.id]
  if (!el) return

  const ws = WaveSurfer.create({
    container: el,
    height: 40,
    waveColor: '#8b949e',
    progressColor: '#58a6ff',
    cursorColor: '#58a6ff',
    barWidth: 2,
    barGap: 1,
  })

  uploadedWaveSurfers.value[fileItem.id] = ws

  ws.loadBlob(fileItem.file)

  ws.on('ready', () => {
    // waveform ready
  })
}

const removeWaveform = (id) => {
  const ws = uploadedWaveSurfers.value[id]
  if (ws) {
    ws.destroy()
    delete uploadedWaveSurfers.value[id]
  }
  if (waveformEls.value[id]) {
    delete waveformEls.value[id]
  }
}

const uploadFiles = async () => {
  const accepted = files.value.filter((f) => f.status === 'ok')
  if (accepted.length === 0) return
  isUploading.value = true
  try {
    await apiClient.uploadDataset(accepted.map((f) => f.file))
    uploadSuccess.value = `Uploaded: ${accepted.map((f) => f.file.name).join(', ')}`
  } finally {
    isUploading.value = false
  }
}

onBeforeUnmount(() => {
  for (const id of Object.keys(uploadedWaveSurfers.value)) {
    const ws = uploadedWaveSurfers.value[id]
    if (ws) ws.destroy()
  }
  uploadedWaveSurfers.value = {}
})
</script>

<template>
  <section class="upload-view">
    <h2>Upload & Ingestion</h2>
    <div
      ref="dropZone"
      class="drop-zone"
      data-testid="drop-zone"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <div class="drop-zone-icon">📁</div>
      <div class="drop-zone-text">
        Drag & drop audio files here, or click to browse
      </div>
      <div class="drop-zone-hint">
        Supported: WAV, FLAC, OGG, MP3, M4A, MP4, AIFF, AIF
      </div>
      <input
        type="file"
        multiple
        accept="audio/*,.wav,.flac,.ogg,.mp3,.m4a,.mp4,.aiff,.aif"
        style="display:none"
        @change="addFilesFromInput"
      />
    </div>

    <div class="file-list">
      <div
        v-for="fileItem in files"
        :key="fileItem.id"
        class="file-item"
        data-testid="file-item"
      >
        <span class="file-icon">🎵</span>
        <span class="file-name">{{ fileItem.file.name }}</span>
        <span class="file-status" :class="fileItem.status">{{ fileItem.label }}</span>
        <div
          v-if="fileItem.status === 'ok'"
          class="waveform-preview"
          :ref="(el) => { if (el) waveformEls[fileItem.id] = el }"
        ></div>
      </div>
    </div>

    <button
      class="upload-btn"
      data-testid="upload-btn"
      :disabled="isUploading || files.filter(f => f.status === 'ok').length === 0"
      @click="uploadFiles"
    >
      {{ isUploading ? 'Uploading...' : 'Upload' }}
    </button>

    <div v-if="uploadSuccess" class="upload-success" data-testid="upload-success">
      {{ uploadSuccess }}
    </div>

    <button class="hints-toggle" data-testid="hints-toggle" @click="hintsExpanded = !hintsExpanded">
      {{ hintsExpanded ? 'Hide DDSP requirements' : 'Show DDSP requirements' }}
    </button>
    <div v-if="hintsExpanded" class="hints-box">
      DDSP requires 2-5 minute mono audio at 16kHz+ sample rate. Files are resampled automatically.
    </div>
  </section>
</template>

<style scoped>
.upload-view { max-width: 800px; }
.drop-zone { border: 2px dashed var(--border); border-radius: 8px; padding: 3rem 2rem; text-align: center; cursor: pointer; transition: border-color 0.2s; }
.drop-zone.dragover { border-color: var(--accent); }
.drop-zone-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.drop-zone-text { color: var(--text-secondary); font-size: 0.875rem; }
.drop-zone-hint { color: var(--text-secondary); font-size: 0.75rem; margin-top: 0.25rem; }
.file-list { margin-top: 1rem; }
.file-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0.75rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 0.5rem; }
.file-icon { font-size: 1.1rem; }
.file-name { flex: 1; font-size: 0.875rem; word-break: break-word; }
.file-status { font-size: 0.75rem; padding: 0.125rem 0.5rem; border-radius: 4px; }
.file-status.ok { background: var(--success); color: #000; }
.file-status.warn { background: var(--warning); color: #000; }
.waveform-preview { height: 40px; margin-top: 0.25rem; }
.upload-btn { margin-top: 1rem; padding: 0.5rem 1.5rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.upload-btn:hover { background: var(--accent-hover); }
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.upload-success { margin-top: 0.75rem; padding: 0.5rem 0.75rem; background: var(--success); color: #000; border-radius: 6px; font-size: 0.875rem; }
.hints-toggle { margin-top: 1.5rem; color: var(--text-secondary); font-size: 0.8rem; cursor: pointer; border: none; background: none; }
.hints-box { margin-top: 0.5rem; padding: 0.75rem; background: var(--bg-tertiary); border-radius: 6px; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }
</style>
