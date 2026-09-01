import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ModelParameterBuilder from '../components/ModelParameterBuilder.vue'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const standardManifest = {
  format: 'wogd-ddsp-checkpoint-params-v1',
  version: 1,
  params: [
    {
      slot: 1,
      name: 'Pitch Shift',
      description: 'F0 offset in semitones',
      param_type: 'continuous',
      min_value: -24,
      max_value: 24,
      default_value: 0,
      mapping: 'linear',
      unit_hint: 'st',
      group: 'Pitch',
      neutone_slot: null,
    },
  ],
  runId: 'run_abc123',
  checkpoint: 'step-100.pt',
}

const componentManifest = {
  format: 'wogd-ddsp-checkpoint-params-v1',
  version: 1,
  params: [
    {
      slot: 1,
      name: 'Harmonic Blend',
      description: 'Blend of harmonic oscillator',
      param_type: 'continuous',
      min_value: 0,
      max_value: 1,
      default_value: 0.7,
      mapping: 'linear',
      unit_hint: '',
      group: 'Harmonic',
      neutone_slot: 1,
    },
    {
      slot: 2,
      name: 'Noise Blend',
      description: 'Blend of noise generator',
      param_type: 'continuous',
      min_value: 0,
      max_value: 1,
      default_value: 0.3,
      mapping: 'linear',
      unit_hint: '',
      group: 'Harmonic',
      neutone_slot: 2,
    },
    {
      slot: 3,
      name: 'Reverb Mix',
      description: 'Dry/Wet reverb mix',
      param_type: 'continuous',
      min_value: 0,
      max_value: 1,
      default_value: 0.3,
      mapping: 'linear',
      unit_hint: '',
      group: 'Effects',
      neutone_slot: null,
    },
    {
      slot: 4,
      name: 'Attack',
      description: 'Envelope attack time',
      param_type: 'continuous',
      min_value: 0.001,
      max_value: 0.5,
      default_value: 0.01,
      mapping: 'log',
      unit_hint: 's',
      group: 'Envelope',
      neutone_slot: null,
    },
  ],
  runId: 'run_abc123',
  checkpoint: 'step-100.pt',
}

const advancedVaeManifest = {
  format: 'wogd-ddsp-checkpoint-params-v1',
  version: 1,
  params: Array.from({ length: 10 }, (_, i) => ({
    slot: i + 1,
    name: `Param ${i + 1}`,
    description: '',
    param_type: 'continuous',
    min_value: -3,
    max_value: 3,
    default_value: 0,
    mapping: 'linear',
    unit_hint: '',
    group: 'Latent',
    neutone_slot: i < 4 ? i + 1 : null,
  })),
  runId: 'run_abc123',
  checkpoint: 'step-100.pt',
}

// A param with min > max for validation error testing
const validationErrorManifest = {
  format: 'wogd-ddsp-checkpoint-params-v1',
  version: 1,
  params: [
    {
      slot: 1,
      name: 'Bad Param',
      description: '',
      param_type: 'continuous',
      min_value: 10,
      max_value: 1,
      default_value: 0.5,
      mapping: 'linear',
      unit_hint: '',
      group: '',
      neutone_slot: null,
    },
  ],
  runId: 'run_abc123',
  checkpoint: 'step-100.pt',
}

// ---------------------------------------------------------------------------
// Mount helper with mocked apiClient injection
// ---------------------------------------------------------------------------

let updateCheckpointParamsSpy
let exportNeutoneSpy
let exportCustomVstSpy

function mountBuilder(overrides = {}) {
  updateCheckpointParamsSpy = vi.fn().mockResolvedValue({
    format: 'wogd-ddsp-checkpoint-params-v1',
    version: 1,
    params: [],
  })
  exportNeutoneSpy = vi.fn().mockResolvedValue(new Blob(['dummy']), {
    type: 'application/octet-stream',
  })
  exportCustomVstSpy = vi.fn().mockResolvedValue(new Blob(['dummy']), {
    type: 'application/octet-stream',
  })

  return mount(ModelParameterBuilder, {
    props: {
      manifest: overrides.manifest ?? standardManifest,
      modelTier: overrides.modelTier ?? 'standard',
      readonly: overrides.readonly ?? false,
    },
    global: {
      provide: {
        apiClient: {
          updateCheckpointParams: updateCheckpointParamsSpy,
          exportNeutone: exportNeutoneSpy,
          exportCustomVST: exportCustomVstSpy,
        },
      },
    },
    attachTo: document.body,
  })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ModelParameterBuilder', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with standard fixture — Custom VST section absent', () => {
    const wrapper = mountBuilder({ manifest: standardManifest, modelTier: 'standard' })

    expect(wrapper.find('[data-testid="param-builder"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-builder-neutone-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-builder-custom-section"]').exists()).toBe(false)
  })

  it('renders with component fixture — both sections visible', () => {
    const wrapper = mountBuilder({ manifest: componentManifest, modelTier: 'component' })

    expect(wrapper.find('[data-testid="param-builder-neutone-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-builder-custom-section"]').exists()).toBe(true)
  })

  it('renders with advanced_vae fixture — 6 custom param cards (Neutone-assigned params NOT in Custom VST)', async () => {
    const wrapper = mountBuilder({ manifest: advancedVaeManifest, modelTier: 'advanced_vae' })

    const section = wrapper.find('[data-testid="param-builder-custom-section"]')
    expect(section.exists()).toBe(true)

    // The custom VST section shows only non-neutone params via
    // visibleCustomParams — Param 5–10 in the advanced_vae fixture.
    const paramCards = section.findAllComponents({
      name: 'ParamCard',
    })
    expect(paramCards.length).toBe(6)

    // Verify the first custom card (slot 5) is NOT readonly.
    const firstCustomCard = paramCards[0]
    expect(firstCustomCard.props('readonly')).toBe(false)

    // Verify the last custom card (slot 10) is NOT readonly.
    const lastCustomCard = paramCards[5]
    expect(lastCustomCard.props('readonly')).toBe(false)
  })

  it('name edit on param card emits update:manifest', async () => {
    vi.useFakeTimers()
    const wrapper = mountBuilder({ manifest: componentManifest, modelTier: 'component' })

    const customSection = wrapper.find('[data-testid="param-builder-custom-section"]')
    const paramCards = customSection.findAllComponents({
      name: 'ParamCard',
    })

    // The first card in the custom section is "Reverb Mix" (slot 3)
    const targetCard = paramCards[0]
    const nameInput = targetCard.find('[data-testid="param-name-input"]')

    expect(nameInput.exists()).toBe(true)

    await nameInput.setValue('Renamed Reverb')
    // Wait for debounce timer in ParamCard to fire
    vi.advanceTimersByTime(250)

    const emitted = wrapper.emitted('update:manifest')
    expect(emitted).toBeTruthy()
    expect(emitted.length).toBeGreaterThan(0)

    const lastManifest = emitted[emitted.length - 1][0]
    expect(lastManifest).toHaveProperty('params')
    const updatedParam = lastManifest.params.find((p) => p.slot === 3)
    expect(updatedParam).toBeTruthy()
    expect(updatedParam.name).toBe('Renamed Reverb')
    vi.useRealTimers()
  })

  it('+ Add Parameter increments param count', async () => {
    const wrapper = mountBuilder({
      manifest: { ...standardManifest, params: [standardManifest.params[0]] },
      modelTier: 'component',
    })

    expect(wrapper.find('[data-testid="param-builder-add-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-builder-add-btn"]').attributes('disabled')).toBeUndefined()

    await wrapper.find('[data-testid="param-builder-add-btn"]').trigger('click')

    const customSection = wrapper.find('[data-testid="param-builder-custom-section"]')
    const paramCards = customSection.findAllComponents({ name: 'ParamCard' })

    expect(paramCards.length).toBe(2)
  })

  it('save button disabled when !isDirty', () => {
    const wrapper = mountBuilder({ manifest: standardManifest, modelTier: 'component' })

    // Immediately after mount, localParams === prop manifest → isDirty is false
    const saveBtn = wrapper.find('[data-testid="param-builder-save-btn"]')
    expect(saveBtn.exists()).toBe(true)
    expect(saveBtn.attributes('disabled')).toBeDefined()
  })

  it('save button calls updateCheckpointParams (via inject mock)', async () => {
    vi.useFakeTimers()
    const wrapper = mountBuilder({
      manifest: { ...standardManifest, params: [standardManifest.params[0]] },
      modelTier: 'component',
    })

    // Make the component dirty by adding a param
    await wrapper.find('[data-testid="param-builder-add-btn"]').trigger('click')

    const saveBtn = wrapper.find('[data-testid="param-builder-save-btn"]')
    expect(saveBtn.attributes('disabled')).toBeUndefined()

    await saveBtn.trigger('click')

    // Wait for the async save to complete
    vi.advanceTimersByTime(0)

    // Verify the injected mock's updateCheckpointParams was called
    expect(updateCheckpointParamsSpy).toHaveBeenCalledTimes(1)
    expect(updateCheckpointParamsSpy).toHaveBeenCalledWith(
      'run_abc123',
      'step-100.pt',
      expect.objectContaining({ params: expect.any(Array) })
    )

    // Assert the save status updated
    expect(wrapper.find('[data-testid="param-builder-save-status"]').text()).toBe('Saved')
    vi.useRealTimers()
  })

  it('export buttons disabled when validation errors (min > max on any param)', async () => {
    const wrapper = mountBuilder({
      manifest: validationErrorManifest,
      modelTier: 'component',
    })

    // Induce isDirty so the disable isn't just from isDirty=false
    await wrapper.find('[data-testid="param-builder-add-btn"]').trigger('click')

    const neutoneExportBtn = wrapper.find('[data-testid="param-builder-export-neutone"]')
    const customExportBtn = wrapper.find('[data-testid="param-builder-export-custom"]')

    expect(neutoneExportBtn.attributes('disabled')).toBeDefined()
    expect(customExportBtn.attributes('disabled')).toBeDefined()
  })
})
