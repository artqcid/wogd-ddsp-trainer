<template>
  <div class="neutone-slot-panel" data-testid="neutone-slot-panel">
    <div
      v-for="(slot, index) in slots"
      :key="index"
      class="neutone-slot"
      :class="{
        'neutone-slot--occupied': !!slot,
        'neutone-slot--empty': !slot,
        'neutone-slot--disabled': readonly,
        'neutone-slot--dragover': overIndex === index,
      }"
      :data-testid="`neutone-slot-${index + 1}`"
      :aria-disabled="readonly"
      @dragover="onDragOver(index, $event)"
      @drop="onDrop(index, $event)"
      @dragleave="onDragLeave(index)"
    >
  <header class="neutone-slot__header">
    <span class="neutone-slot__label">KNOB {{ index + 1 }}</span>
  </header>

  <div class="neutone-slot__body" data-testid="neutone-slot-body">
    <template v-if="!!slot">
      <p class="neutone-slot__name" :data-testid="`neutone-slot-${index + 1}-name`">{{ slot.name }}</p>
      <p v-if="slot.unit_hint" class="neutone-slot__unit" :data-testid="`neutone-slot-${index + 1}-unit`">{{ slot.unit_hint }}</p>
      <p class="neutone-slot__range" :data-testid="`neutone-slot-${index + 1}-range`">
        [{{ slot.min_value }},{{ slot.max_value }}]
      </p>
      <button
        v-if="!readonly && !!slot"
        class="neutone-slot__remove-bottom"
        type="button"
        :data-testid="`neutone-slot-${index + 1}-remove`"
        aria-label="Remove from slot"
        @click="onRemove(index)"
      >
        Remove
      </button>
    </template>
        <template v-else>
          <p class="neutone-slot__empty-label" :data-testid="`neutone-slot-${index + 1}-drag-label`">drag here</p>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  allParams: {
    type: Array,
    required: true,
    default: () => [],
  },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update:slots'])

/** Internal 4-slot array, initialised from allParams where neutone_slot is set. */
const slots = ref([null, null, null, null])

function initSlots() {
  const assigned = props.allParams
    .filter((p) => p.neutone_slot != null && p.neutone_slot >= 1 && p.neutone_slot <= 4)
  const arr = [null, null, null, null]
  for (const p of assigned) {
    arr[p.neutone_slot - 1] = p
  }
  slots.value = arr
  emit('update:slots', arr.slice())
}

initSlots()

/** Re-initialise when allParams identity changes (new array from parent). */
onMounted(() => {
  // already done via initSlots above
})

/** HTML5 DnD: slot visual cue while a param is over it. */
const overIndex = ref(-1)

function onDragOver(index, event) {
  if (props.readonly) return
  overIndex.value = index
  if (event && event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

function onDragLeave(index) {
  if (overIndex.value === index) overIndex.value = -1
}

function onDrop(index, event) {
  if (props.readonly) return
  overIndex.value = -1
  try {
    const dataTransfer = event && event.dataTransfer
    if (!dataTransfer) return
    const payload = dataTransfer.getData('text/plain')
    if (!payload) return
    const param = JSON.parse(payload)
    assignToSlot(index, param)
  } catch {
    // malformed drag payload: ignore
  }
}

/** Assign a param to a specific slot; emits after mutation. */
function assignToSlot(index, param) {
  const next = slots.value.slice()
  next[index] = param
  emit('update:slots', next)
}

/** Remove the param from a slot. */
function onRemove(index) {
  if (props.readonly) return
  const next = slots.value.slice()
  next[index] = null
  emit('update:slots', next)
}
</script>

<style scoped>
.neutone-slot-panel {
  display: flex;
  gap: var(--space-4);
  align-items: stretch;
}

.neutone-slot {
  position: relative;
  flex: 1;
  min-width: 0;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.neutone-slot--occupied {
  border-style: solid;
}

.neutone-slot--empty {
  border-style: dashed;
  border-color: var(--text-muted);
}

.neutone-slot--empty.neutone-slot--dragover {
  border-color: var(--accent);
  background: var(--bg-tertiary);
}

.neutone-slot--disabled {
  opacity: 0.85;
}

.neutone-slot__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.neutone-slot__label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.neutone-slot__remove,
.neutone-slot__remove-bottom {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-family: var(--font-sans);
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  transition: background var(--transition-fast), color var(--transition-fast), border-color var(--transition-fast);
}

.neutone-slot__remove:hover,
.neutone-slot__remove-bottom:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.neutone-slot__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-height: 80px;
}

.neutone-slot__name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.neutone-slot__unit {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.neutone-slot__range {
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: var(--space-1);
}

.neutone-slot__empty-label {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.875rem;
  font-style: italic;
}

.neutone-slot__remove-bottom {
  align-self: flex-end;
  margin-top: var(--space-1);
}
</style>
