<script setup>
import { inject, ref, computed, onMounted } from 'vue'
import { useModelConfigStore } from '../stores/modelConfig.js'
import { tierLabel, tierColor, tierIcon } from '../utils/tierColors.js'
import GpuFeasibilityBanner from '../components/GpuFeasibilityBanner.vue'
import WizardModal from '../components/WizardModal.vue'
import TabCore from '../components/TabCore.vue'
import TabComponent from '../components/TabComponent.vue'
import TabHacks from '../components/TabHacks.vue'
import TabEngine from '../components/TabEngine.vue'
import TabAdvanced from '../components/TabAdvanced.vue'
import PresetSaveDialog from '../components/PresetSaveDialog.vue'

const apiClient = inject('apiClient')
const store = useModelConfigStore()

const activeTab = ref('core')
const showDialog = ref(false)
const validationResult = ref(null)
const showWizard = ref(!store.wizardCompleted)
const showTierMismatchWarning = ref(false)
const pendingConfig = ref(null)

const TIER_TAB_MAP = {
  standard: ['core', 'component'],
  component: ['core', 'component'],
  hacks: ['core', 'component', 'hacks'],
  engine: ['core', 'component', 'hacks', 'engine'],
  advanced: ['core', 'component', 'hacks', 'engine', 'advanced'],
}

const tabs = computed(() => {
  const allowed = TIER_TAB_MAP[store.activeTier] ?? ['core', 'component']
  return [
    { key: 'core', label: 'Core', available: allowed.includes('core') },
    { key: 'component', label: 'Component', available: allowed.includes('component') },
    { key: 'hacks', label: 'Hacks', available: allowed.includes('hacks') },
    { key: 'engine', label: 'Engine', available: allowed.includes('engine') },
    { key: 'advanced', label: 'Advanced', available: allowed.includes('advanced') },
  ]
})

const currentTabComponent = computed(() => {
  const map = { core: TabCore, component: TabComponent, hacks: TabHacks, engine: TabEngine, advanced: TabAdvanced }
  return map[activeTab.value] || TabCore
})

function selectTab(key) {
  const t = tabs.value.find(t => t.key === key)
  if (t && t.available) {
    activeTab.value = key
  }
}

function reconfigure() {
  store.resetToWizard()
  showWizard.value = true
}

async function handleStartTraining() {
  if (!apiClient) return
  validationResult.value = null
  const config = store.buildFullConfig()
  try {
    const validation = await apiClient.validateConfig(config)
    const clamped = validation.clamped_fields || []
    if (validation.model_tier_mismatch) {
      pendingConfig.value = config
      showTierMismatchWarning.value = true
      if (clamped.length > 0) {
        validationResult.value = { ok: null, message: `Note: ${clamped.length} param(s) were clamped to hardware bounds.` }
      }
      return
    }
    await _doStartRun(config, clamped)
  } catch (e) {
    validationResult.value = { ok: false, message: e.message || 'Validation failed' }
  }
}

onMounted(async () => {
  if (apiClient && !store.gpuFeasibility) {
    await store.checkFeasibility(apiClient)
  }
})

async function _doStartRun(config, clamped) {
  try {
    const run = await apiClient.startRun(config)
    let msg = `Training started: ${run.run_id} (${run.status})`
    if (clamped && clamped.length > 0) msg += ` — ${clamped.length} param(s) clamped.`
    validationResult.value = { ok: true, message: msg }
    showTierMismatchWarning.value = false
    pendingConfig.value = null
  } catch (e) {
    validationResult.value = { ok: false, message: e.message || 'Failed to start run' }
  }
}

async function handleTierMismatchProceed() {
  if (!pendingConfig.value) return
  await _doStartRun(pendingConfig.value, [])
}

function handleTierMismatchCancel() {
  showTierMismatchWarning.value = false
  pendingConfig.value = null
}
</script>

<template>
  <section class="config-view">
    <div class="config-header">
      <h2>Training Config</h2>
      <div class="config-header-actions">
        <span v-if="store.activeTier" class="tier-badge" :style="{ color: tierColor(store.activeTier) }" data-testid="tier-badge">
          {{ tierIcon(store.activeTier) }} {{ tierLabel(store.activeTier) }}
        </span>
        <button class="btn btn--ghost" @click="reconfigure" data-testid="reconfigure-btn">⚙ Reconfigure Model</button>
        <button class="btn btn--ghost" data-testid="save-preset-btn" @click="showDialog = true">Save as Preset</button>
      </div>
    </div>

    <WizardModal v-if="showWizard" @complete="showWizard = false" />

    <template v-if="store.wizardCompleted">
      <GpuFeasibilityBanner :availableGb="store.gpuFeasibility?.available_gb ?? 0" />

      <div
          v-if="store.synthesisMode === 'midi_synth' || store.synthesisMode === 'both'"
          class="midi-hint-banner"
          data-testid="midi-hint-banner"
        >
          <span class="midi-hint-icon">🎹</span>
          <div class="midi-hint-content">
            <strong>MIDI Synth Training Tip</strong>
            <p>For best MIDI synth results, quantize the training audio F0 to semitones in the preprocessing step
            (<a href="/preprocessing" class="hint-link">Dataset → Preprocessing → Pitch Curve Editor</a>).</p>
          </div>
        </div>

        <div class="tab-bar" data-testid="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ 'tab-btn--active': activeTab === tab.key, 'tab-btn--disabled': !tab.available }"
          :disabled="!tab.available"
          :data-testid="`tab-${tab.key}`"
          @click="selectTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="tab-content">
        <component :is="currentTabComponent" />
      </div>

      <div
        v-if="showTierMismatchWarning"
        class="tier-mismatch-banner"
        data-testid="tier-mismatch-banner"
      >
        <strong>⚠ Tier Mismatch</strong>
        <p>The selected preset was created with a different model tier than the current configuration. Training may produce unexpected results.</p>
        <div class="tier-mismatch-actions">
          <button class="btn btn--primary" data-testid="tier-mismatch-proceed" @click="handleTierMismatchProceed">Proceed anyway</button>
          <button class="btn btn--ghost" data-testid="tier-mismatch-cancel" @click="handleTierMismatchCancel">Cancel</button>
        </div>
      </div>

      <div class="btn-row">
        <button class="btn btn--primary" data-testid="start-training-btn" @click="handleStartTraining">▶ Start Training</button>
      </div>

      <div v-if="validationResult" class="validation-result" :class="validationResult.ok ? 'ok' : 'err'" data-testid="validation-result">
        {{ validationResult.message }}
      </div>
    </template>

    <PresetSaveDialog
      :show="showDialog"
      :currentConfig="store.buildFullConfig()"
      @close="showDialog = false"
      @save="(payload) => {
        showDialog = false
        if (apiClient) {
          apiClient.createPreset(payload).then(() => {})
        }
      }"
    />
  </section>
</template>

<style scoped>
.config-view { max-width: 900px; }
.config-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.config-header-actions { display: flex; align-items: center; gap: 0.75rem; }
.tier-badge { font-weight: 600; font-size: 0.8rem; }
.tab-content { margin-top: 1rem; }
.btn-row { margin-top: 1.5rem; }
.validation-result { margin-top: 0.75rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.875rem; }
.validation-result.ok { background: var(--success); color: #000; }
.validation-result.err { background: var(--error); color: #fff; }

.midi-hint-banner {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  margin-bottom: var(--space-4);
  background: var(--bg-tertiary);
  border: 1px solid var(--tier-hacks);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
}
.midi-hint-icon { font-size: 1.2rem; line-height: 1; }
.midi-hint-content strong { display: block; margin-bottom: var(--space-1); }
.midi-hint-content p { color: var(--text-secondary); margin: 0; }
.hint-link { color: var(--accent); text-decoration: none; }
.hint-link:hover { text-decoration: underline; }

.tier-mismatch-banner {
  margin-top: 1rem;
  padding: var(--space-3);
  background: var(--bg-tertiary);
  border: 1px solid var(--tier-hacks);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
}
.tier-mismatch-banner strong { display: block; margin-bottom: var(--space-1); color: var(--warning); }
.tier-mismatch-banner p { color: var(--text-secondary); margin: 0 0 var(--space-2); }
.tier-mismatch-actions { display: flex; gap: 0.5rem; }
</style>