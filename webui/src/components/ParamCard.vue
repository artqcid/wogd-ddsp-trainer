<template>
  <div class="param-card" data-testid="param-card" :class="{ 'param-card--readonly': readonly }">
    <div class="param-card__header">
      <span class="param-card__drag" data-testid="param-card-drag" aria-hidden="true">⠿</span>
      <span class="param-card__slot">P{{ param.slot }}</span>
      <span v-if="isNeutoneAssigned && param.neutone_slot !== null" class="badge badge--neutone" data-testid="neutone-badge">
        NEUTONE S{{ param.neutone_slot }}
      </span>
    </div>

    <div class="param-card__field" data-testid="param-name-field">
      <label class="form-label" for="param-name">Name</label>
      <input
        id="param-name"
        class="form-input"
        :class="{ 'form-input--error': nameOverflow }"
        type="text"
        :data-testid="'param-name-input'"
        :value="param.name"
        :disabled="readonly"
        maxlength="30"
        @input="onNameInput"
      />
      <span v-if="!readonly" class="param-card__counter" :class="{ 'param-card__counter--overflow': nameOverflow }" data-testid="name-counter">
        {{ param.name.length }}/30
      </span>
    </div>

    <div class="param-card__field">
      <label class="form-label" for="param-description">Description</label>
      <input
        id="param-description"
        class="form-input"
        type="text"
        :data-testid="'param-description-input'"
        :value="param.description"
        :disabled="readonly"
        @input="onDescriptionInput"
      />
    </div>

    <div class="param-card__field param-card__type">
      <label class="form-label">Type</label>
      <label class="param-card__radio">
        <input
          type="radio"
          name="param-type"
          :value="'continuous'"
          :data-testid="'param-type-radio'"
          :checked="param.param_type === 'continuous'"
          :disabled="readonly"
          @change="onTypeChange"
        />
        <span>Continuous</span>
      </label>
      <label class="param-card__radio">
        <input
          type="radio"
          name="param-type"
          :value="'categorical'"
          :data-testid="'param-type-radio'"
          :checked="param.param_type === 'categorical'"
          :disabled="readonly"
          @change="onTypeChange"
        />
        <span>Categorical</span>
      </label>
    </div>

    <div class="param-card__range param-card__grid">
      <div class="param-card__field param-card__range-item">
        <label class="form-label" for="param-min">Min</label>
        <input
          id="param-min"
          class="form-input"
          type="number"
          :data-testid="'param-min-input'"
          :value="param.min_value"
          :disabled="readonly"
          :class="{ 'form-input--error': minMaxError }"
          @input="onMinInput"
        />
      </div>
      <div class="param-card__field param-card__range-item">
        <label class="form-label" for="param-max">Max</label>
        <input
          id="param-max"
          class="form-input"
          type="number"
          :data-testid="'param-max-input'"
          :value="param.max_value"
          :disabled="readonly"
          :class="{ 'form-input--error': minMaxError }"
          @input="onMaxInput"
        />
      </div>
      <div class="param-card__field param-card__range-item">
        <label class="form-label" for="param-default">Default</label>
        <input
          id="param-default"
          class="form-input"
          type="number"
          :data-testid="'param-default-input'"
          :value="param.default_value"
          :disabled="readonly"
          @input="onDefaultInput"
        />
      </div>
    </div>

    <div class="param-card__mapping param-card__grid">
      <div class="param-card__field">
        <label class="form-label">Mapping</label>
        <label v-for="opt in mappingOptions" :key="opt.value" class="param-card__radio">
          <input
            type="radio"
            name="param-mapping"
            :data-testid="'param-mapping-select'"
            :value="opt.value"
            :checked="param.mapping === opt.value"
            :disabled="readonly"
            @change="onMappingChange"
          />
          <span>{{ opt.label }}</span>
        </label>
      </div>
      <div class="param-card__field">
        <label class="form-label" for="param-unit">Unit</label>
        <input
          id="param-unit"
          class="form-input"
          type="text"
          :data-testid="'param-unit-input'"
          :value="param.unit_hint"
          :disabled="readonly"
          @input="onUnitInput"
        />
      </div>
    </div>

    <div class="param-card__field">
      <label class="form-label" for="param-group">Group</label>
        <input
          id="param-group"
          class="form-input"
          type="text"
          :data-testid="'param-group-input'"
          :value="param.group"
          :disabled="readonly"
          @input="onGroupInput"
        />
    </div>

    <button
      v-if="!readonly"
      class="btn btn--danger param-card__remove"
      type="button"
      data-testid="param-remove-btn"
      @click="onRemove"
    >
      Remove
    </button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  param: { type: Object, required: true },
  index: { type: Number, required: true },
  isNeutoneAssigned: { type: Boolean, default: false },
  readonly: { type: Boolean, default: false },
})

const emit = defineEmits(['update:param', 'remove'])

const debounceTimer = ref(null)

const mappingOptions = [
  { value: 'linear', label: 'linear' },
  { value: 'log', label: 'log' },
  { value: 'exp', label: 'exp' },
]

const nameOverflow = ref(false)
const minMaxError = ref(false)

function recalcValidation() {
  nameOverflow.value = props.param.name.length > 30
  minMaxError.value = props.param.min_value > props.param.max_value
}

recalcValidation()
watch(
  () => [props.param.name, props.param.min_value, props.param.max_value],
  () => recalcValidation(),
  { immediate: true }
)

function scheduleUpdate(newParam) {
  if (debounceTimer.value != null) {
    clearTimeout(debounceTimer.value)
  }
  debounceTimer.value = setTimeout(() => {
    emit('update:param', newParam)
  }, 200)
}

function onNameInput(e) {
  const next = { ...props.param, name: e.target.value }
  scheduleUpdate(next)
}

function onDescriptionInput(e) {
  const next = { ...props.param, description: e.target.value }
  scheduleUpdate(next)
}

function onTypeChange(e) {
  const next = { ...props.param, param_type: e.target.value }
  scheduleUpdate(next)
}

function onMinInput(e) {
  const val = Number(e.target.value)
  const next = { ...props.param, min_value: isNaN(val) ? 0 : val }
  scheduleUpdate(next)
}

function onMaxInput(e) {
  const val = Number(e.target.value)
  const next = { ...props.param, max_value: isNaN(val) ? 0 : val }
  scheduleUpdate(next)
}

function onDefaultInput(e) {
  const val = Number(e.target.value)
  const next = { ...props.param, default_value: isNaN(val) ? 0 : val }
  scheduleUpdate(next)
}

function onMappingChange(e) {
  const next = { ...props.param, mapping: e.target.value }
  scheduleUpdate(next)
}

function onUnitInput(e) {
  const next = { ...props.param, unit_hint: e.target.value }
  scheduleUpdate(next)
}

function onGroupInput(e) {
  const next = { ...props.param, group: e.target.value }
  scheduleUpdate(next)
}

function onRemove() {
  emit('remove', props.index)
}
</script>

<style scoped>
.param-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.param-card--readonly {
  opacity: 0.85;
}

.param-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.param-card__drag {
  font-size: 1.1rem;
  color: var(--text-secondary);
  cursor: grab;
  user-select: none;
}

.param-card__slot {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.05em;
}

.param-card__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.param-card__field--error {
  /* used alongside form-input--error on the input itself */
}

.param-card__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.param-card__range-item,
.param-card__mapping {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.param-card__type {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  align-items: center;
}

.param-card__radio {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.param-card__radio input {
  accent-color: var(--accent);
}

.form-input--error {
  border-color: var(--error);
}

.param-card__counter {
  font-size: 0.75rem;
  color: var(--text-muted);
  align-self: flex-end;
}

.param-card__counter--overflow {
  color: var(--error);
}

.badge--neutone {
  background: var(--tier-standard-subtle);
  color: var(--tier-standard);
  border: 1px solid var(--tier-standard);
}

.param-card__remove {
  align-self: flex-end;
}
</style>
