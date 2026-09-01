<template>
  <div class="param-builder" data-testid="param-builder">
    <header class="param-builder__header">
      <h2 class="param-builder__title">PARAMETER CONFIGURATION</h2>
      <div class="param-builder__actions">
        <button
          class="btn btn--secondary"
          type="button"
          data-testid="param-builder-reset-btn"
          :disabled="readonly"
          @click="onReset"
        >
          Reset
        </button>
        <button
          class="btn btn--primary"
          type="button"
          data-testid="param-builder-save-btn"
          :disabled="!isDirty || readonly"
          @click="onSave"
        >
          Save
        </button>
      </div>
    </header>

    <!-- NEUTONE FX SECTION -->
    <section v-if="showNeutoneSection" class="param-builder__neutone" data-testid="param-builder-neutone-section">
      <h3 class="section-title section-title--neutone">
        NEUTONE FX
        <span class="section-title__hint">(max 4)</span>
      </h3>
      <NeutoneSlotPanel
        :allParams="localParams"
        :readonly="readonly || modelTier === 'standard'"
        @update:slots="onSlotsUpdate"
      />
    </section>

    <!-- CUSTOM VST SECTION -->
    <section v-if="showCustomSection" class="param-builder__custom" data-testid="param-builder-custom-section">
      <h3 class="section-title section-title--custom">
        CUSTOM VST (up to 16)
        <span class="section-title__count">{{ customParamCount }}</span>
      </h3>

      <div class="param-builder__cards">
        <ParamCard
          v-for="(param, index) in visibleCustomParams"
          :key="param.slot"
          :param="param"
          :index="index"
          :isNeutoneAssigned="isNeutoneAssigned(param)"
          :readonly="readonly || modelTier === 'standard'"
          @update:param="onParamUpdate"
          @remove="onParamRemove"
        />
      </div>

      <button
        class="btn btn--secondary param-builder__add"
        type="button"
        data-testid="param-builder-add-btn"
        :disabled="localParams.length >= 16 || readonly"
        @click="onAddParameter"
      >
        + Add Parameter
      </button>

      <p v-if="localParams.length >= 16" class="param-builder__max-warning" data-testid="param-builder-max-warning">
        Maximum of 16 parameters reached.
      </p>
    </section>

    <div class="param-builder__divider">
      <span class="divider-rule"></span>
    </div>

    <!-- EXPORT SECTION -->
    <div class="param-builder__export">
      <button
        class="btn btn--ghost"
        type="button"
        data-testid="param-builder-export-neutone"
        :disabled="!isDirty || hasValidationErrors || readonly"
        @click="onExportNeutone"
      >
        Export → Neutone FX (.nm)
      </button>
      <button
        class="btn btn--ghost"
        type="button"
        data-testid="param-builder-export-custom"
        :disabled="!isDirty || hasValidationErrors || readonly"
        @click="onExportCustomVST"
      >
        Export → Custom VST (.pt)
      </button>
    </div>

    <!-- SAVE STATUS -->
    <p v-if="saveStatus !== null" class="param-builder__save-status" data-testid="param-builder-save-status">
      {{ saveStatus }}
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import ParamCard from './ParamCard.vue'
import NeutoneSlotPanel from './NeutoneSlotPanel.vue'

const props = defineProps({
  manifest: {
    type: Object,
    required: true,
  },
  modelTier: {
    type: String,
    default: 'standard',
  },
  readonly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:manifest'])

const apiClient = inject('apiClient')

// Internal working copy of params
const localParams = ref([])
const isDirty = ref(false)
const saveStatus = ref(null)

// Reset localParams back to the original prop manifest
function resetToManifest() {
  localParams.value = props.manifest?.params?.slice() ?? []
  isDirty.value = false
  saveStatus.value = null
}

// Keep localParams in sync when the manifest prop changes (e.g. after save)
watch(
  () => props.manifest,
  () => {
    if (!isDirty.value) {
      resetToManifest()
    }
  },
  { deep: true }
)

// Initialise from prop on mount
resetToManifest()

// ---- Tier-aware section visibility ----

const showNeutoneSection = computed(() => {
  return props.modelTier === 'standard' || props.modelTier === 'component' || props.modelTier === 'advanced_vae'
})

const showCustomSection = computed(() => {
  return props.modelTier !== 'standard'
})

// ---- Custom VST param visibility ----

/**
 * Params visible in the Custom VST section.
 *
 * For 'component' and above: show ALL params (including neutone-assigned ones)
 * as fully editable ParamCards. For 'standard' the section is hidden entirely.
 */
const visibleCustomParams = computed(() => {
  return localParams.value.filter(isCustomParam)
})

const customParamCount = computed(() => {
  return localParams.value.length
})

// ---- Helpers ----

function isNeutoneAssigned(param) {
  return param.neutone_slot != null && Number(param.neutone_slot) >= 1 && Number(param.neutone_slot) <= 4
}

function isCustomParam(param) {
  return param.neutone_slot == null || Number(param.neutone_slot) > 4
}

function paramHasValidationError(param) {
  return param.min_value > param.max_value
}

const hasValidationErrors = computed(() => {
  return localParams.value.some((p) => paramHasValidationError(p))
})

// ---- Events from ParamCard ----

function onParamUpdate(updatedParam) {
  const idx = localParams.value.findIndex((p) => p.slot === updatedParam.slot)
  if (idx === -1) return

  localParams.value[idx] = updatedParam
  isDirty.value = true
  saveStatus.value = null

  emitManifestUpdate()
}

function onParamRemove(index) {
  const removed = localParams.value[index]
  if (!removed) return

  // If the removed param had a neutone_slot, clear that slot assignment
  if (removed.neutone_slot != null) {
    const nextSlots = neutoneSlots.value.slice()
    const slotIdx = (removed.neutone_slot - 1)
    if (slotIdx >= 0 && slotIdx < nextSlots.length) {
      nextSlots[slotIdx] = null
    }
    neutoneSlots.value = nextSlots
  }

  localParams.value.splice(index, 1)
  isDirty.value = true
  saveStatus.value = null

  emitManifestUpdate()
}

/** NeutoneSlotPanel slot sync. */
const neutoneSlots = ref([null, null, null, null])

function onSlotsUpdate(slots) {
  neutoneSlots.value = slots
  isDirty.value = true
  saveStatus.value = null
  emitManifestUpdate()
}

// ---- Add Parameter ----

function onAddParameter() {
  if (localParams.value.length >= 16) return

  const nextSlot = localParams.value.length + 1
  const newParam = {
    slot: nextSlot,
    name: `Parameter ${nextSlot}`,
    description: '',
    param_type: 'continuous',
    min_value: 0,
    max_value: 1,
    default_value: 0.5,
    mapping: 'linear',
    unit_hint: '',
    group: '',
    neutone_slot: null,
  }

  localParams.value.push(newParam)
  isDirty.value = true
  saveStatus.value = null
  emitManifestUpdate()
}

// ---- Reset / Save ----

function onReset() {
  resetToManifest()
}

async function onSave() {
  if (!isDirty.value || props.readonly) return

  const runId = props.manifest?.runId ?? 'run_abc123'
  const checkpoint = props.manifest?.checkpoint ?? 'step-100.pt'

  try {
    await apiClient.updateCheckpointParams(runId, checkpoint, buildManifest())
    saveStatus.value = 'Saved'
    isDirty.value = false
    emitManifestUpdate()
  } catch (err) {
    saveStatus.value = 'Save failed'
  }
}

// ---- Export ----

async function onExportNeutone() {
  if (!isDirty.value || hasValidationErrors.value || props.readonly) return

  const runId = props.manifest?.runId ?? 'run_abc123'
  const checkpoint = props.manifest?.checkpoint ?? 'step-100.pt'

  try {
    await apiClient.exportNeutone(runId, checkpoint)
    saveStatus.value = 'Neutone export started'
  } catch (err) {
    saveStatus.value = 'Export failed'
  }
}

async function onExportCustomVST() {
  if (!isDirty.value || hasValidationErrors.value || props.readonly) return

  const runId = props.manifest?.runId ?? 'run_abc123'
  const checkpoint = props.manifest?.checkpoint ?? 'step-100.pt'

  try {
    await apiClient.exportCustomVST(runId, checkpoint)
    saveStatus.value = 'Custom VST export started'
  } catch (err) {
    saveStatus.value = 'Export failed'
  }
}

// ---- Manifest emission ----

function buildManifest() {
  return {
    format: props.manifest?.format ?? 'wogd-vst-params',
    version: props.manifest?.version ?? '1.0',
    params: localParams.value.slice(),
  }
}

function emitManifestUpdate() {
  emit('update:manifest', buildManifest())
}
</script>

<style scoped>
.param-builder {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
  padding: var(--space-6);
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
}

.param-builder__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.param-builder__title {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  margin: 0;
}

.param-builder__actions {
  display: flex;
  gap: var(--space-3);
}

.param-builder__neutone,
.param-builder__custom {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.param-builder__cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.param-builder__add {
  align-self: flex-start;
}

.param-builder__max-warning {
  margin-top: var(--space-2);
  font-size: 0.875rem;
  color: var(--error);
  font-weight: 500;
}

.param-builder__divider {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin: var(--space-2) 0;
}

.divider-rule {
  flex: 1;
  height: 1px;
  background: var(--border);
}

.param-builder__export {
  display: flex;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.param-builder__save-status {
  margin: 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.section-title {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-secondary);
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
  margin: 0;
}

.section-title__hint {
  font-weight: 400;
  color: var(--text-muted);
  text-transform: none;
  letter-spacing: 0;
}

.section-title__count {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--accent);
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-1) var(--space-2);
}
</style>
