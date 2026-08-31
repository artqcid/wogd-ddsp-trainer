<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  show: Boolean,
  currentConfig: Object
})

const emit = defineEmits(['close', 'save'])

const presetName = ref('')
const nameError = ref('')

const parametersPreview = computed(() => {
  if (!props.currentConfig?.parameters) return []
  return Object.entries(props.currentConfig.parameters).map(([key, value]) => ({
    key,
    value: String(value)
  }))
})

function handleSave() {
  nameError.value = ''
  if (!presetName.value.trim()) {
    nameError.value = 'Preset name is required'
    return
  }
  emit('save', {
    name: presetName.value.trim(),
    parameters: props.currentConfig.parameters || {}
  })
}

function handleBackdropClick(e) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}
</script>

<template>
  <div
    v-if="show"
    class="dialog-overlay"
    data-testid="dialog-overlay"
    @click="handleBackdropClick"
  >
    <div class="dialog-card">
      <h3>Save as Custom Preset</h3>

      <div class="form-group">
        <input
          type="text"
          data-testid="dialog-name-input"
          placeholder="Preset name (e.g. my_custom_voice)"
          v-model="presetName"
          @input="nameError = ''"
        />
        <span v-if="nameError" style="color: var(--error); font-size: 0.75rem; margin-top: 0.25rem; display: block;">
          {{ nameError }}
        </span>
      </div>

      <div class="param-preview" v-if="parametersPreview.length">
        <dl class="param-preview">
          <div v-for="param in parametersPreview" :key="param.key">
            <dt>{{ param.key }}:</dt>
            <dd>{{ param.value }}</dd>
          </div>
        </dl>
      </div>

      <div class="dialog-actions">
        <button
          class="btn-secondary"
          @click="emit('close')"
        >
          Cancel
        </button>
        <button
          class="btn-primary"
          data-testid="dialog-save-btn"
          @click="handleSave"
        >
          Save Preset
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 1.5rem; width: 100%; max-width: 400px; }
.dialog-card h3 { margin: 0 0 1rem; font-size: 1rem; }
.dialog-card input { width: 100%; padding: 0.5rem 0.75rem; background: var(--bg-primary); border: 1px solid var(--border); color: var(--text-primary); border-radius: 6px; font-size: 0.875rem; margin-bottom: 1rem; }
.param-preview { font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem; }
.param-preview dt { font-weight: 600; }
.param-preview dd { margin: 0 0 0.5rem 1rem; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 0.5rem; }
</style>
