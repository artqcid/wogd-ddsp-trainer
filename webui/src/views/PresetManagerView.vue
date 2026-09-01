<script setup>
import { inject, ref, computed, onMounted } from 'vue'

const apiClient = inject('apiClient')

const presets = ref([])
const loading = ref(false)
const error = ref(null)
const editingId = ref(null)
const tierFilter = ref('all')
const editForm = ref({
  name: '',
  type: 'custom',
  parameters: []
})

const GPU_BOUNDS = {
  hidden_dim: 256,
  encoder_dim: 256,
  decoder_dim: 256,
  postnet_dim: 256
}

const isBuiltin = (type) => type !== 'custom'

const parameterCount = (preset) => {
  return preset.parameters ? Object.keys(preset.parameters).length : 0
}

const clampWarning = (params) => {
  if (!params) return null
  const warnings = []
  for (const [key, value] of Object.entries(params)) {
    const bound = GPU_BOUNDS[key]
    if (bound && Number(value) > bound) {
      warnings.push(`${key} > ${bound}`)
    }
  }
  return warnings.length > 0 ? warnings.join(', ') : null
}

const filteredPresets = computed(() => {
  if (tierFilter.value === 'all') return presets.value
  return presets.value.filter(p => (p.model_tier || 'standard') === tierFilter.value)
})

const loadPresets = async () => {
  loading.value = true
  error.value = null
  try {
    presets.value = await apiClient.listPresets()
  } catch (e) {
    error.value = e.message || 'Failed to load presets'
  } finally {
    loading.value = false
  }
}

const createPreset = async () => {
  if (!editForm.value.name.trim()) return
  const params = {}
  for (const row of editForm.value.parameters) {
    if (row.key.trim() && row.value.trim()) {
      params[row.key.trim()] = row.value.trim()
    }
  }
  try {
    await apiClient.createPreset({
      name: editForm.value.name.trim(),
      type: 'custom',
      parameters: params
    })
    editForm.value = { name: '', parameters: [] }
    await loadPresets()
  } catch (e) {
    error.value = e.message || 'Failed to create preset'
  }
}

const startEdit = (preset) => {
  if (isBuiltin(preset.type)) return
  editingId.value = preset.id
  editForm.value = {
    name: preset.name,
    parameters: Object.entries(preset.parameters || {}).map(([k, v]) => ({ key: k, value: v }))
  }
}

const saveEdit = async () => {
  if (!editForm.value.name.trim()) return
  const params = {}
  for (const row of editForm.value.parameters) {
    if (row.key.trim() && row.value.trim()) {
      params[row.key.trim()] = row.value.trim()
    }
  }
  try {
    await apiClient.updatePreset(editingId.value, {
      name: editForm.value.name.trim(),
      parameters: params
    })
    editingId.value = null
    await loadPresets()
  } catch (e) {
    error.value = e.message || 'Failed to save preset'
  }
}

const cancelEdit = () => {
  editingId.value = null
  editForm.value = { name: '', parameters: [] }
}

const deletePreset = async (id) => {
  if (!window.confirm('Delete this preset?')) return
  try {
    await apiClient.deletePreset(id)
    await loadPresets()
  } catch (e) {
    error.value = e.message || 'Failed to delete preset'
  }
}

const addParam = () => {
  editForm.value.parameters.push({ key: '', value: '' })
}

const removeParam = (index) => {
  editForm.value.parameters.splice(index, 1)
}

onMounted(() => {
  loadPresets()
})
</script>

<template>
  <section class="preset-view">
    <header class="preset-header">
      <h2>Preset Manager</h2>
      <div class="filter-row">
        <label class="filter-label">Tier:</label>
        <select v-model="tierFilter" class="tier-filter" data-testid="tier-filter" @change="loadPresets">
          <option value="all">All tiers</option>
          <option value="standard">Standard</option>
          <option value="component">Component</option>
          <option value="hacks">Hacks</option>
          <option value="engine">Engine</option>
          <option value="advanced">Advanced</option>
        </select>
      </div>
      <p v-if="error" style="color: var(--error); font-size: 0.875rem;">{{ error }}</p>
    </header>

    <form class="create-form" data-testid="create-form">
      <h3>Create New Preset</h3>
      <div class="form-row">
        <div class="form-group">
          <label for="preset-name-input">Name</label>
          <input
            id="preset-name-input"
            v-model="editForm.name"
            data-testid="preset-name-input"
            placeholder="my_custom_preset"
          />
        </div>
        <div class="form-group">
          <label>Type</label>
          <select v-model="editForm.type" disabled>
            <option value="custom">Custom</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <div class="param-row">
            <template v-for="(param, idx) in editForm.parameters" :key="idx">
              <input
                v-model="param.key"
                placeholder="param_key"
                style="flex: 1; margin-right: 0.5rem;"
              />
              <input
                v-model="param.value"
                placeholder="value"
                style="flex: 1; margin-right: 0.5rem;"
              />
              <button
                type="button"
                class="param-remove"
                @click="removeParam(idx)"
                v-if="editForm.parameters.length > 1"
              >
                Remove
              </button>
            </template>
          </div>
        </div>
      </div>
      <button type="button" class="add-param-btn" data-testid="add-param-btn" @click="addParam">
        + Add Parameter
      </button>
      <div class="form-row">
        <button type="button" class="add-param-btn" style="background: var(--accent); color: #000; border-color: var(--accent);" data-testid="create-btn" @click="createPreset">
          Create Preset
        </button>
      </div>
    </form>

    <div v-if="editingId" class="create-form" style="margin-top: 1rem;">
      <h3>Edit Preset: {{ editForm.name || 'Unnamed' }}</h3>
      <div class="form-row">
        <div class="form-group">
          <label for="edit-name-input">Name</label>
          <input
            id="edit-name-input"
            v-model="editForm.name"
            data-testid="preset-name-input"
            placeholder="preset_name"
          />
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <div class="param-row">
            <template v-for="(param, idx) in editForm.parameters" :key="idx">
              <input
                v-model="param.key"
                placeholder="param_key"
                style="flex: 1; margin-right: 0.5rem;"
              />
              <input
                v-model="param.value"
                placeholder="value"
                style="flex: 1; margin-right: 0.5rem;"
              />
              <button
                type="button"
                class="param-remove"
                @click="removeParam(idx)"
                v-if="editForm.parameters.length > 1"
              >
                Remove
              </button>
            </template>
          </div>
        </div>
      </div>
      <button type="button" class="add-param-btn" data-testid="add-param-btn" @click="addParam">
        + Add Parameter
      </button>
      <p v-if="clampWarning(editForm.parameters.reduce((acc, row) => ({ ...acc, [row.key]: row.value }), {}))" class="clamp-warning" data-testid="clamp-warning">
        {{ clampWarning(editForm.parameters.reduce((acc, row) => ({ ...acc, [row.key]: row.value }), {})) }}
      </p>
      <div class="form-row">
        <button type="button" class="add-param-btn" style="background: var(--accent); color: #000; border-color: var(--accent);" data-testid="create-btn" @click="saveEdit">
          Save Preset
        </button>
        <button type="button" class="add-param-btn" @click="cancelEdit">
          Cancel
        </button>
      </div>
    </div>

    <div v-if="loading" class="empty-state">Loading presets...</div>
    <div v-else-if="presets.length === 0" class="empty-state">No presets found. Create one above.</div>
    <div v-else class="preset-list">
      <div
        v-for="preset in filteredPresets"
        :key="preset.id"
        class="preset-card"
        data-testid="preset-card"
      >
        <div class="preset-card-header">
          <div>
            <span class="preset-card-name" data-testid="preset-name">{{ preset.name }}</span>
            <span class="badge" :class="isBuiltin(preset.type) ? 'builtin' : 'custom'" data-testid="preset-type-badge">
              {{ preset.type }}
            </span>
            <span v-if="clampWarning(preset.parameters)" class="clamp-warning" data-testid="clamp-warning">
              {{ clampWarning(preset.parameters) }}
            </span>
          </div>
          <div class="preset-card-params">{{ parameterCount(preset) }} parameters</div>
        </div>
        <p class="preset-card-params">{{ preset.parameters ? Object.entries(preset.parameters).map(([k, v]) => `${k}: ${v}`).join(', ') : '' }}</p>
        <div class="preset-card-actions" v-if="!isBuiltin(preset.type)">
          <button data-testid="edit-btn" @click="startEdit(preset)">Edit</button>
          <button data-testid="delete-btn" class="delete" @click="deletePreset(preset.id)">Delete</button>
        </div>
        <div class="preset-card-actions" v-else>
          <span style="font-size: 0.75rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.25rem;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" style="opacity: 0.5;"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 15c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v2h-2zm0 8h2v4h-2z"/></svg>
            Built-in preset
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.preset-view { max-width: 900px; }
.preset-header { margin-bottom: 1.5rem; }
.filter-row { display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0; }
.filter-label { font-size: 0.8rem; color: var(--text-secondary); }
.tier-filter { padding: 0.25rem 0.5rem; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.8rem; }
.create-form { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; }
.create-form h3 { margin: 0 0 1rem; font-size: 0.9rem; }
.form-row { display: flex; gap: 1rem; margin-bottom: 0.75rem; }
.form-group { flex: 1; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group input, .form-group select { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; }
.param-row { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; }
.param-row input { flex: 1; }
.param-remove { padding: 0.25rem 0.5rem; background: transparent; border: 1px solid var(--error); color: var(--error); border-radius: 4px; cursor: pointer; font-size: 0.75rem; }
.add-param-btn { padding: 0.25rem 0.75rem; background: transparent; border: 1px solid var(--border); color: var(--text-secondary); border-radius: 4px; cursor: pointer; font-size: 0.8rem; margin-bottom: 1rem; }
.preset-list { display: flex; flex-direction: column; gap: 0.75rem; }
.preset-card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
.preset-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.preset-card-name { font-weight: 600; font-size: 0.9rem; }
.preset-card-params { font-size: 0.8rem; color: var(--text-secondary); }
.preset-card-actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
.preset-card-actions button { padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.8rem; cursor: pointer; border: 1px solid var(--border); background: transparent; color: var(--text-primary); }
.preset-card-actions button:hover { background: var(--bg-tertiary); }
.preset-card-actions .delete { border-color: var(--error); color: var(--error); }
.badge { display: inline-block; padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
.badge.builtin { background: var(--bg-tertiary); color: var(--text-secondary); }
.badge.custom { background: var(--accent); color: #000; }
.clamp-warning { display: inline-block; padding: 0.125rem 0.5rem; background: var(--warning); color: #000; border-radius: 4px; font-size: 0.75rem; margin-top: 0.25rem; }
.empty-state { text-align: center; padding: 3rem; color: var(--text-secondary); }
</style>
