<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import WaveSurfer from 'wavesurfer.js'

const props = defineProps({
  originalUrl: { type: String, required: true },
  synthesizedUrl: { type: String, required: true }
})

const originalPlayer = ref(null)
const synthesizedPlayer = ref(null)
const originalWs = ref(null)
const synthesizedWs = ref(null)
const isSyncPlaying = ref(false)
const activeTrack = ref(null)

let syncInterval = null

onMounted(() => {
  initWaveSurfer('originalPlayer', props.originalUrl, 'original')
  initWaveSurfer('synthesizedPlayer', props.synthesizedUrl, 'synthesized')
})

onUnmounted(() => {
  if (originalWs.value) {
    originalWs.value.destroy()
    originalWs.value = null
  }
  if (synthesizedWs.value) {
    synthesizedWs.value.destroy()
    synthesizedWs.value = null
  }
  if (syncInterval) {
    clearInterval(syncInterval)
    syncInterval = null
  }
})

function initWaveSurfer(containerId, url, trackName) {
  const container = document.getElementById(containerId)
  if (!container) return

  const ws = WaveSurfer.create({
    container,
    waveColor: 'var(--text-secondary)',
    progressColor: 'var(--accent)',
    cursorColor: 'var(--accent)',
    barWidth: 2,
    height: 80,
    normalize: true
  })

  ws.load(url)

  ws.on('ready', () => {
    if (trackName === 'original') {
      originalWs.value = ws
      originalPlayer.value = container
    } else {
      synthesizedWs.value = ws
      synthesizedPlayer.value = container
    }
  })

  ws.on('play', () => {
    activeTrack.value = trackName
  })

  ws.on('pause', () => {
    if (activeTrack.value === trackName) {
      activeTrack.value = null
    }
  })

  ws.on('finish', () => {
    if (activeTrack.value === trackName) {
      activeTrack.value = null
    }
  })
}

function playOriginal() {
  if (originalWs.value) {
    originalWs.value.play()
  }
}

function pauseOriginal() {
  if (originalWs.value) {
    originalWs.value.pause()
  }
}

function playSynthesized() {
  if (synthesizedWs.value) {
    synthesizedWs.value.play()
  }
}

function pauseSynthesized() {
  if (synthesizedWs.value) {
    synthesizedWs.value.pause()
  }
}

function toggleSyncPlay() {
  if (isSyncPlaying.value) {
    stopSync()
  } else {
    startSync()
  }
}

function startSync() {
  isSyncPlaying.value = true
  if (originalWs.value) originalWs.value.play()
  if (synthesizedWs.value) synthesizedWs.value.play()
}

function stopSync() {
  isSyncPlaying.value = false
  if (originalWs.value) originalWs.value.pause()
  if (synthesizedWs.value) synthesizedWs.value.pause()
  activeTrack.value = null
}
</script>

<template>
  <div class="ab-player" data-testid="ab-player">
    <div
      class="ab-track"
      :class="{ active: activeTrack === 'original' }"
      data-testid="original-player"
    >
      <div class="ab-track-label">Original</div>
      <div ref="originalPlayer" class="waveform-container"></div>
      <div class="ab-controls">
        <button @click="playOriginal" :class="{ active: isSyncPlaying }">Play</button>
        <button @click="pauseOriginal">Pause</button>
      </div>
    </div>

    <div
      class="ab-track"
      :class="{ active: activeTrack === 'synthesized' }"
      data-testid="synthesized-player"
    >
      <div class="ab-track-label">Synthesized</div>
      <div ref="synthesizedPlayer" class="waveform-container"></div>
      <div class="ab-controls">
        <button @click="playSynthesized" :class="{ active: isSyncPlaying }">Play</button>
        <button @click="pauseSynthesized">Pause</button>
      </div>
    </div>

    <div class="ab-controls sync-controls">
      <button
        class="sync-play-btn"
        @click="toggleSyncPlay"
        :class="{ active: isSyncPlaying }"
        data-testid="sync-play-btn"
      >
        {{ isSyncPlaying ? 'Stop Sync' : 'Sync Play' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.ab-player { display: flex; gap: 1rem; margin: 1rem 0; }
.ab-track { flex: 1; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; }
.ab-track.active { border-color: var(--accent); }
.ab-track-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.5rem; }
.waveform-container { width: 100%; }
.ab-controls { display: flex; justify-content: center; gap: 0.5rem; margin-top: 1rem; }
.ab-controls button { padding: 0.375rem 1rem; background: var(--bg-tertiary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 4px; font-size: 0.8rem; cursor: pointer; }
.ab-controls button:hover { background: var(--accent); color: #000; }
.ab-controls button.active { background: var(--accent); color: #000; }
.sync-controls { margin-top: 0.5rem; }
.sync-play-btn { padding: 0.5rem 1.5rem; }
</style>
