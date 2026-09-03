<script setup>
import { inject, ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'

const apiClient = inject('apiClient')

const runs = ref([])
const selectedRunId = ref(null)
const tensorboard = ref({})
const presetResult = ref(null)

let pollInterval = null

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

function startPolling() {
  stopPolling()
  pollInterval = setInterval(async () => {
    if (apiClient) {
      try {
        const current = await apiClient.listRuns()
        runs.value = current
        const anyRunning = current.some(r => r.status === 'running')
        if (!anyRunning) {
          stopPolling()
        }
      } catch {
        stopPolling()
      }
    } else {
      stopPolling()
    }
  }, 5000)
}

async function loadRuns() {
  if (!apiClient) return
  try {
    const current = await apiClient.listRuns()
    runs.value = current
    const anyRunning = current.some(r => r.status === 'running')
    if (anyRunning) {
      startPolling()
    }
  } catch {
    runs.value = []
  }
}

async function loadTensorboard() {
  if (!apiClient) return
  try {
    const tb = await apiClient.getTensorboard()
    tensorboard.value = tb
  } catch {
    tensorboard.value = {}
  }
}

function selectRun(id) {
  selectedRunId.value = selectedRunId.value === id ? null : id
}

async function handleStop(id) {
  if (!apiClient) return
  try {
    await apiClient.stopRun(id)
    await loadRuns()
  } catch {
    await loadRuns()
  }
}

async function handleResume(id) {
  if (!apiClient) return
  try {
    await apiClient.resumeRun(id)
    await loadRuns()
  } catch {
    await loadRuns()
  }
}

async function handleDelete(id) {
  if (!apiClient) return
  if (!window.confirm('Delete this training run? This action cannot be undone.')) return
  try {
    await apiClient.deleteRun(id)
    selectedRunId.value = null
    await loadRuns()
  } catch {
    await loadRuns()
  }
}

async function handleSavePreset(id) {
  if (!apiClient) return
  presetResult.value = null
  try {
    await apiClient.createPresetFromRun(id)
    presetResult.value = { type: 'ok', message: 'Preset saved successfully.' }
  } catch {
    presetResult.value = { type: 'err', message: 'Failed to save preset.' }
  }
}

onMounted(() => {
  loadRuns()
  loadTensorboard()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <section class="dashboard-view">
    <header class="dashboard-header">
      <h2>Training Dashboard</h2>
    </header>

    <div class="tensorboard-section">
      <h3>TensorBoard</h3>
      <div v-if="tensorboard.running && tensorboard.url">
        <iframe
          class="tensorboard-iframe"
          data-testid="tensorboard-iframe"
          :src="tensorboard.url"
          title="TensorBoard"
        />
      </div>
      <div v-else class="tensorboard-fallback" data-testid="tensorboard-fallback">
        <p>TensorBoard not running</p>
        <a v-if="tensorboard.url" :href="tensorboard.url" target="_blank" rel="noopener noreferrer">
          Open TensorBoard in new tab
        </a>
      </div>
    </div>

    <div v-if="runs.length === 0" class="empty-state" data-testid="empty-state">
      <p>No training runs yet. Start one from the
        <RouterLink to="/model">Training Config</RouterLink> page.
      </p>
    </div>

    <div v-else class="runs-list">
      <div
        v-for="run in runs"
        :key="run.run_id"
        class="run-card"
        :data-testid="'run-card'"
        @click="selectRun(run.run_id)"
      >
        <div class="run-card-header">
          <span class="run-card-name" data-testid="run-name">{{ run.name }}</span>
          <span class="badge" :class="'badge ' + run.status" data-testid="run-status">{{ run.status }}</span>
        </div>
        <div class="run-card-meta">
          <span>Dataset: {{ run.dataset_id || '—' }}</span>
          <span>Step: {{ run.latest_step ?? '—' }} / {{ run.config?.max_steps ?? '—' }}</span>
          <span>Error: {{ run.error || '—' }}</span>
        </div>
        <div
          v-if="selectedRunId === run.run_id"
          class="run-detail"
          data-testid="run-detail"
        >
          <div class="run-detail-meta">
            <div>
              <strong>Created:</strong> {{ run.created_at }}
            </div>
            <div>
              <strong>Dataset:</strong> {{ run.dataset_id || '—' }}
            </div>
            <div>
              <strong>Steps:</strong> {{ run.latest_step ?? '—' }} / {{ run.config?.max_steps ?? '—' }}
            </div>
            <div class="epoch-bar" data-testid="epoch-bar">
              <div
                class="epoch-bar-fill"
                :style="{
                  width: run.config?.max_steps ? ((run.latest_step / run.config.max_steps) * 100) + '%' : '0%'
                }"
              />
            </div>
          </div>
          <div class="run-controls">
            <button
              v-if="run.status === 'running'"
              class="stop"
              data-testid="stop-btn"
              @click.stop="handleStop(run.run_id)"
            >
              Stop
            </button>
            <button
              v-if="run.status === 'stopped' || run.status === 'failed'"
              class="resume"
              data-testid="resume-btn"
              @click.stop="handleResume(run.run_id)"
            >
              Resume
            </button>
            <button
              class="delete"
              data-testid="delete-btn"
              @click.stop="handleDelete(run.run_id)"
            >
              Delete
            </button>
            <button
              class="preset"
              data-testid="save-preset-btn"
              @click.stop="handleSavePreset(run.run_id)"
            >
              Save as Preset
            </button>
            <span
              v-if="presetResult"
              class="preset-result"
              :class="presetResult.type"
              data-testid="preset-result"
            >
              {{ presetResult.message }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.dashboard-view { max-width: 1100px; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.runs-list { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 2rem; }
.run-card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; cursor: pointer; transition: border-color 0.15s; }
.run-card:hover { border-color: var(--accent); }
.run-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.run-card-name { font-weight: 600; font-size: 0.9rem; }
.run-card-meta { display: flex; gap: 1.5rem; font-size: 0.8rem; color: var(--text-secondary); }
.run-detail { margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border); }
.run-detail-meta { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.75rem; line-height: 1.6; }
.run-controls { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.run-controls button { padding: 0.375rem 1rem; border-radius: 4px; font-size: 0.8rem; cursor: pointer; border: 1px solid var(--border); background: transparent; color: var(--text-primary); }
.run-controls button:hover { background: var(--bg-tertiary); }
.run-controls .stop { border-color: var(--error); color: var(--error); }
.run-controls .stop:hover { background: var(--error); color: #000; }
.run-controls .delete { border-color: var(--error); color: var(--error); }
.run-controls .preset { border-color: var(--accent); color: var(--accent); }
.preset-result { margin-top: 0.5rem; font-size: 0.8rem; padding: 0.375rem 0.75rem; border-radius: 4px; }
.preset-result.ok { background: var(--success); color: #000; }
.preset-result.err { background: var(--error); color: #fff; }
.badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
.badge.idle { background: var(--warning); color: #000; }
.badge.stopped { background: var(--warning); color: #000; }
.badge.running { background: var(--accent); color: #000; }
.badge.completed { background: var(--success); color: #000; }
.badge.failed { background: var(--error); color: #fff; }
.epoch-bar { height: 4px; background: var(--bg-tertiary); border-radius: 2px; margin-top: 0.5rem; overflow: hidden; }
.epoch-bar-fill { height: 100%; background: var(--accent); transition: width 0.3s; }
.tensorboard-section { margin-top: 2rem; }
.tensorboard-section h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
.tensorboard-iframe { width: 100%; height: 500px; border: 1px solid var(--border); border-radius: 8px; }
.tensorboard-fallback { padding: 2rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; text-align: center; color: var(--text-secondary); }
.tensorboard-fallback a { display: inline-block; margin-top: 0.75rem; padding: 0.5rem 1rem; background: var(--accent); color: #000; text-decoration: none; border-radius: 6px; font-weight: 600; }
.empty-state { text-align: center; padding: 3rem; color: var(--text-secondary); }
.empty-state a { color: var(--accent); }
</style>
