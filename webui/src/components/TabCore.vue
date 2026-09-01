<template>
  <div class="tab-core" data-testid="tab-core">
    <div class="form-group">
      <label class="form-label">Preset</label>
      <select class="form-select" v-model="selectedPresetName" data-testid="preset-select">
        <option value="">-- Select Preset --</option>
        <optgroup label="Built-in">
          <option v-for="p in builtinPresets" :key="p.id" :value="p.name">{{ p.name }}</option>
        </optgroup>
        <optgroup label="Custom" v-if="customPresets.length">
          <option v-for="p in customPresets" :key="p.id" :value="p.name">{{ p.name }}</option>
        </optgroup>
      </select>
    </div>
    <div class="form-group">
      <label class="form-label">Learning Rate</label>
      <input class="form-input" type="number" step="0.0001" v-model.number="store.coreParams.learning_rate" data-testid="learning-rate" />
    </div>
    <div class="form-group">
      <label class="form-label">Batch Size</label>
      <input class="form-input" type="number" v-model.number="store.coreParams.batch_size" data-testid="batch-size" />
    </div>
    <div class="form-group">
      <label class="form-label">Epochs</label>
      <input class="form-input" type="number" v-model.number="store.coreParams.epochs" data-testid="epochs" />
    </div>
    <div class="form-group">
      <label class="form-label">Decoder Type</label>
      <select class="form-select" v-model="store.coreParams.decoder_type" data-testid="decoder-type">
        <option value="gru">GRU</option>
        <option value="rnn">RNN</option>
      </select>
    </div>
    <div class="form-group">
      <label class="checkbox-label">
        <input type="checkbox" v-model="store.coreParams.use_reverb" data-testid="use-reverb" />
        Enable Reverb
      </label>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from 'vue'
import { useModelConfigStore } from '../stores/modelConfig.js'

const store = useModelConfigStore()
const apiClient = inject('apiClient')
const presets = ref([])
const selectedPresetName = ref('')

const builtinPresets = computed(() => presets.value.filter(p => p.is_builtin))
const customPresets = computed(() => presets.value.filter(p => !p.is_builtin))

onMounted(async () => {
  if (apiClient) {
    presets.value = await apiClient.listPresets()
  }
})
</script>

<style scoped>
.tab-core { display: flex; flex-direction: column; gap: var(--space-3); }
.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  cursor: pointer;
}
</style>