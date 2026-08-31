<script setup>
import { inject, onMounted, ref } from 'vue'

const apiClient = inject('apiClient')

const settings = ref(null)
const loading = ref(true)
const error = ref(null)
const saving = ref(false)
const saveMessage = ref(null)
const newDataDir = ref('')
const dirty = ref(false)

onMounted(async () => {
  try {
    settings.value = await apiClient.getSettings()
    newDataDir.value = settings.value.data_dir
  } catch (e) {
    error.value = e.message || 'Failed to load settings'
  } finally {
    loading.value = false
  }
})

function isAbsolutePath(p) {
  if (!p) return false
  return /^([a-zA-Z]:[\\/]|\/)/.test(p)
}

async function saveDataDir() {
  saving.value = true
  saveMessage.value = null
  try {
    if (newDataDir.value === settings.value.data_dir) {
      saveMessage.value = { kind: 'info', text: 'Data directory unchanged.' }
      return
    }
    if (!isAbsolutePath(newDataDir.value)) {
      saveMessage.value = { kind: 'error', text: 'Data directory must be an absolute path.' }
      return
    }
    settings.value = await apiClient.updateSettings(newDataDir.value)
    dirty.value = false
    saveMessage.value = {
      kind: 'ok',
      text: 'Data directory updated. Uploaded samples now go to the new datasets folder.',
    }
  } catch (e) {
    saveMessage.value = { kind: 'error', text: e.message || 'Failed to update data directory' }
  } finally {
    saving.value = false
  }
}

async function resetDataDir() {
  saving.value = true
  saveMessage.value = null
  try {
    settings.value = await apiClient.updateSettings(null)
    newDataDir.value = settings.value.data_dir
    dirty.value = false
    saveMessage.value = { kind: 'ok', text: 'Data directory reset to default.' }
  } catch (e) {
    saveMessage.value = { kind: 'error', text: e.message || 'Failed to reset data directory' }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="settings-view">
    <h2>Settings</h2>
    <div v-if="loading" class="loading" data-testid="settings-loading">Loading...</div>
    <div v-else-if="error" class="error-box" data-testid="settings-error">{{ error }}</div>
    <div v-else-if="settings" class="settings-body">
      <div class="settings-card">
        <h3>Installation</h3>
        <p class="muted">Where the application is installed. This is fixed at install time and read-only at runtime.</p>
        <dl class="path-list">
          <div class="path-row">
            <dt>Install directory</dt>
            <dd data-testid="install-dir">{{ settings.install_dir }}</dd>
          </div>
        </dl>
      </div>

      <div class="settings-card">
        <h3>Data directory (Sammelwurzel)</h3>
        <p class="muted">
          Central folder holding datasets, runs and the database. Only this directory can be changed
          live. Uploaded input samples (drag &amp; drop) are copied into the <em>datasets</em> folder by default.
        </p>
        <dl class="path-list">
          <div class="path-row">
            <dt>Data directory</dt>
            <dd data-testid="data-dir">{{ settings.data_dir }}</dd>
          </div>
          <div class="path-row">
            <dt>Datasets</dt>
            <dd data-testid="datasets-dir">{{ settings.datasets_dir }}</dd>
          </div>
          <div class="path-row">
            <dt>Runs</dt>
            <dd data-testid="runs-dir">{{ settings.runs_dir }}</dd>
          </div>
          <div class="path-row">
            <dt>Database</dt>
            <dd data-testid="db-path">{{ settings.db_path }}</dd>
          </div>
          <div class="path-row">
            <dt>Default</dt>
            <dd>
              <span class="badge" :class="settings.data_is_default ? 'default' : 'custom'" data-testid="data-default">
                {{ settings.data_is_default ? 'Using default' : 'Custom location' }}
              </span>
            </dd>
          </div>
        </dl>

        <div class="editor">
          <label for="data-dir-input">New data directory (absolute path)</label>
          <input
            id="data-dir-input"
            v-model="newDataDir"
            class="path-input"
            data-testid="data-dir-input"
            @input="dirty = true"
            @keyup.enter="saveDataDir"
          />
          <div class="actions">
            <button class="save-btn" data-testid="save-data-dir" :disabled="saving" @click="saveDataDir">
              {{ saving ? 'Saving...' : 'Save data directory' }}
            </button>
            <button class="reset-btn" data-testid="reset-data-dir" :disabled="saving" @click="resetDataDir">
              Reset to default
            </button>
          </div>
          <div v-if="saveMessage" class="save-message" :class="saveMessage.kind" data-testid="save-message">
            {{ saveMessage.text }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.settings-view { max-width: 760px; }
.settings-body { display: flex; flex-direction: column; gap: 1.25rem; }
.settings-card { padding: 1.25rem; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; }
.settings-card h3 { margin: 0 0 0.25rem; font-size: 1rem; }
.muted { color: var(--text-secondary); font-size: 0.8rem; margin: 0 0 0.75rem; }
.path-list { margin: 0; }
.path-row { display: flex; justify-content: space-between; gap: 1rem; padding: 0.4rem 0; border-bottom: 1px solid var(--border); }
.path-row:last-child { border-bottom: none; }
.path-row dt { color: var(--text-secondary); font-size: 0.8rem; }
.path-row dd { margin: 0; font-size: 0.8rem; font-family: monospace; word-break: break-all; text-align: right; }
.badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
.badge.default { background: var(--success); color: #000; }
.badge.custom { background: var(--warning); color: #000; }
.editor { margin-top: 1rem; }
.editor label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.4rem; }
.path-input { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 6px; color: var(--text-primary); font-family: monospace; font-size: 0.8rem; }
.actions { display: flex; gap: 0.75rem; margin-top: 0.75rem; }
.save-btn { padding: 0.5rem 1.25rem; background: var(--accent); color: #000; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; }
.save-btn:hover { background: var(--accent-hover); }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.reset-btn { padding: 0.5rem 1.25rem; background: transparent; border: 1px solid var(--border); color: var(--text-secondary); border-radius: 6px; font-weight: 600; cursor: pointer; }
.reset-btn:hover { border-color: var(--text-secondary); }
.save-message { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8rem; }
.save-message.ok { background: var(--success); color: #000; }
.save-message.error { background: var(--error); color: #000; }
.save-message.info { background: var(--bg-tertiary); color: var(--text-secondary); }
.loading { color: var(--text-secondary); padding: 2rem; text-align: center; }
.error-box { padding: 1rem; background: var(--error); color: #000; border-radius: 6px; }
</style>
