import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { MockApiClient } from '../mocks/mockApiClient.js'
import { PARAM_MANIFEST_FIXTURES } from '../mocks/fixtures.js'
import InferencePlaygroundView from '../views/InferencePlaygroundView.vue'
import ModelExportView from '../views/ModelExportView.vue'
import PresetManagerView from '../views/PresetManagerView.vue'
import ModelParameterBuilder from '../components/ModelParameterBuilder.vue'

vi.mock('wavesurfer.js', () => ({
  default: {
    create: vi.fn(() => ({
      loadBlob: vi.fn(),
      load: vi.fn(),
      on: vi.fn(),
      destroy: vi.fn(),
      play: vi.fn(),
      pause: vi.fn(),
    })),
  },
}))

vi.mock('vue-router', () => ({
  RouterLink: {
    props: ['to'],
    template: '<a :href="to"><slot /></a>',
  },
  RouterView: {
    template: '<div />',
  },
  useRouter: () => ({ push: vi.fn(), resolve: vi.fn(() => ({ href: '' })) }),
  useRoute: () => ({ path: '/', params: {} }),
}))

// Mock URL.createObjectURL for browser-like environment
global.URL = {
  createObjectURL: vi.fn(() => 'blob:mock-url'),
  revokeObjectURL: vi.fn(),
}

const pinia = createPinia()

const mountOptions = {
  global: {
    provide: { apiClient: new MockApiClient() },
    plugins: [pinia],
  },
}

// Mount helper for ModelExportView with spy-tracked apiClient
function mountExportView(overrides = {}) {
  const exportNeutoneSpy = vi.fn().mockResolvedValue(
    new Blob(['dummy'], { type: 'application/octet-stream' })
  )
  const exportCustomVstSpy = vi.fn().mockResolvedValue(
    new Blob(['dummy'], { type: 'application/octet-stream' })
  )

  const mockClient = new MockApiClient()
  mockClient.exportNeutone = exportNeutoneSpy
  mockClient.exportCustomVST = exportCustomVstSpy

  return {
    wrapper: mount(ModelExportView, {
      ...mountOptions,
      global: {
        ...mountOptions.global,
        provide: { apiClient: mockClient },
      },
      ...overrides,
    }),
    spies: { exportNeutoneSpy, exportCustomVstSpy },
  }
}

describe('InferencePlaygroundView', () => {
  it('renders model select', async () => {
    const wrapper = mount(InferencePlaygroundView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="model-select"]').exists()).toBe(true)
  })

  it('renders synthesize button', async () => {
    const wrapper = mount(InferencePlaygroundView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="synthesize-btn"]').exists()).toBe(true)
  })

  it('renders 4 sliders when standard manifest is returned', async () => {
    const mockClient = new MockApiClient()
    const standardManifest = PARAM_MANIFEST_FIXTURES.standard
    mockClient._paramManifestStore.set('run_abc123::step-100.pt', standardManifest)

    const wrapper = mount(InferencePlaygroundView, {
      ...mountOptions,
      global: {
        ...mountOptions.global,
        provide: { apiClient: mockClient },
      },
    })
    await flushPromises()

    // Set up models via the models ref (as would happen on mount)
    wrapper.vm.models = [
      { run_id: 'run_abc123', checkpoints: ['step-100.pt'], created_at: '2024-01-15T10:30:00Z' },
    ]

    // Set selectedModelId to trigger the watcher which calls loadParamManifest
    wrapper.vm.selectedModelId = 'run_abc123'
    await wrapper.vm.$nextTick()
    await flushPromises()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Verify the param manifest was loaded
    expect(wrapper.vm.paramManifest).toBeTruthy()
    expect(wrapper.vm.paramManifest.params.length).toBe(4)

    // Verify param values are set to defaults
    expect(wrapper.vm.paramValues[1]).toBe(0)
    expect(wrapper.vm.paramValues[2]).toBe(0)
    expect(wrapper.vm.paramValues[3]).toBe(0.5)
    expect(wrapper.vm.paramValues[4]).toBe(0.3)

    // Check that the param-sliders-section renders
    expect(wrapper.find('[data-testid="param-sliders-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-1"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-2"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-4"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-1"]').element.min).toBe('-24')
    expect(wrapper.find('[data-testid="param-slider-1"]').element.max).toBe('24')
  })

  it('renders 10 sliders when advanced_vae manifest is returned', async () => {
    const mockClient = new MockApiClient()
    const advancedVaeManifest = PARAM_MANIFEST_FIXTURES.advanced_vae
    mockClient._paramManifestStore.set('run_def456::step-45.pt', advancedVaeManifest)

    const wrapper = mount(InferencePlaygroundView, {
      ...mountOptions,
      global: {
        ...mountOptions.global,
        provide: { apiClient: mockClient },
      },
    })
    await flushPromises()

    // Set up models via the models ref
    wrapper.vm.models = [
      { run_id: 'run_def456', checkpoints: ['step-45.pt'], created_at: '2024-02-20T14:00:00Z' },
    ]

    // Set selectedModelId to trigger the watcher
    wrapper.vm.selectedModelId = 'run_def456'
    await wrapper.vm.$nextTick()
    await flushPromises()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Verify the param manifest was loaded with 10 params
    expect(wrapper.vm.paramManifest).toBeTruthy()
    expect(wrapper.vm.paramManifest.params.length).toBe(10)

    expect(wrapper.find('[data-testid="param-sliders-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-9"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-10"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-group-Latent"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-slider-group-Pitch"]').exists()).toBe(true)
  })

  it('shows no param sliders section when getCheckpointParams returns null', async () => {
    const mockClient = new MockApiClient()
    mockClient.getCheckpointParams = vi.fn().mockResolvedValue(null)

    const wrapper = mount(InferencePlaygroundView, {
      ...mountOptions,
      global: {
        ...mountOptions.global,
        provide: { apiClient: mockClient },
      },
    })
    await flushPromises()

    // Set up models and trigger the watcher
    wrapper.vm.models = [
      { run_id: 'run_abc123', checkpoints: ['step-100.pt'], created_at: '2024-01-15T10:30:00Z' },
    ]
    wrapper.vm.selectedModelId = 'run_abc123'
    await wrapper.vm.$nextTick()
    await flushPromises()

    expect(wrapper.vm.paramManifest).toBeNull()
    expect(wrapper.find('[data-testid="param-sliders-section"]').exists()).toBe(false)
  })

  it('calls synthesize with updated params when slider is changed', async () => {
    const mockClient = new MockApiClient()
    const standardManifest = PARAM_MANIFEST_FIXTURES.standard
    mockClient._paramManifestStore.set('run_abc123::step-100.pt', standardManifest)

    const synthesizeSpy = vi.spyOn(mockClient, 'synthesize').mockResolvedValue({
      job_id: 'job_synth_001',
      status: 'queued',
    })

    const wrapper = mount(InferencePlaygroundView, {
      ...mountOptions,
      global: {
        ...mountOptions.global,
        provide: { apiClient: mockClient },
      },
    })
    await flushPromises()

    // Set up models and trigger the watcher
    wrapper.vm.models = [
      { run_id: 'run_abc123', checkpoints: ['step-100.pt'], created_at: '2024-01-15T10:30:00Z' },
    ]
    wrapper.vm.selectedModelId = 'run_abc123'
    wrapper.vm.audioFile = new Blob(['dummy'], { type: 'audio/wav' })
    await wrapper.vm.$nextTick()
    await flushPromises()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Change slider value
    const slider = wrapper.find('[data-testid="param-slider-1"]')
    await slider.setValue('12')
    await wrapper.vm.$nextTick()

    // Click synthesize
    const synthesizeBtn = wrapper.find('[data-testid="synthesize-btn"]')
    await synthesizeBtn.trigger('click')
    await flushPromises()

    expect(synthesizeSpy).toHaveBeenCalledWith({
      model_id: 'run_abc123',
      audio_file: expect.any(Blob),
      enhance: false,
      params: { '1': 12, '2': 0, '3': 0.5, '4': 0.3 },
    })
  })

  it('resets all sliders to default values when Reset button is clicked', async () => {
    const mockClient = new MockApiClient()
    const standardManifest = PARAM_MANIFEST_FIXTURES.standard
    mockClient._paramManifestStore.set('run_abc123::step-100.pt', standardManifest)

    const wrapper = mount(InferencePlaygroundView, {
      ...mountOptions,
      global: {
        ...mountOptions.global,
        provide: { apiClient: mockClient },
      },
    })
    await flushPromises()

    // Set up models and trigger the watcher
    wrapper.vm.models = [
      { run_id: 'run_abc123', checkpoints: ['step-100.pt'], created_at: '2024-01-15T10:30:00Z' },
    ]
    wrapper.vm.selectedModelId = 'run_abc123'
    await wrapper.vm.$nextTick()
    await flushPromises()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Change slider values
    const slider1 = wrapper.find('[data-testid="param-slider-1"]')
    await slider1.setValue('10')
    const slider3 = wrapper.find('[data-testid="param-slider-3"]')
    await slider3.setValue('0.8')
    await wrapper.vm.$nextTick()

    // Verify values changed
    expect(wrapper.vm.paramValues[1]).toBe(10)
    expect(wrapper.vm.paramValues[3]).toBe(0.8)

    // Click reset button
    const resetBtn = wrapper.find('[data-testid="param-slider-reset"]')
    await resetBtn.trigger('click')
    await wrapper.vm.$nextTick()
    await flushPromises()

    // Verify values are reset to defaults (check component state)
    expect(wrapper.vm.paramValues[1]).toBe(0)
    expect(wrapper.vm.paramValues[2]).toBe(0)
    expect(wrapper.vm.paramValues[3]).toBe(0.5)
    expect(wrapper.vm.paramValues[4]).toBe(0.3)
  })
})

describe('ModelExportView', () => {
  it('renders format cards', async () => {
    const wrapper = mount(ModelExportView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="format-card"]').exists()).toBe(true)
  })

  it('renders export button', async () => {
    const wrapper = mount(ModelExportView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="export-btn"]').exists()).toBe(true)
  })

  it('renders ModelParameterBuilder with mock manifest', async () => {
    const { wrapper } = mountExportView()
    await flushPromises()
    wrapper.vm.selectedModel = wrapper.vm.models[0]
    await flushPromises()
    expect(wrapper.find('[data-testid="export-param-builder"]').exists()).toBe(true)
  })

  it('calls apiClient.exportNeutone when Export → Neutone FX is clicked', async () => {
    const { wrapper, spies } = mountExportView()
    await flushPromises()
    wrapper.vm.selectedModel = wrapper.vm.models[0]
    await flushPromises()
    const builder = wrapper.find('[data-testid="export-param-builder"]')
    const exportNeutoneBtn = builder.find('[data-testid="param-builder-export-neutone"]')
    expect(exportNeutoneBtn.exists()).toBe(true)
    await exportNeutoneBtn.trigger('click')
    await flushPromises()
    expect(spies.exportNeutoneSpy).toHaveBeenCalled()
  })

  it('calls apiClient.exportCustomVST when Export → Custom VST is clicked', async () => {
    const { wrapper, spies } = mountExportView()
    await flushPromises()
    wrapper.vm.selectedModel = wrapper.vm.models[0]
    await flushPromises()
    const builder = wrapper.find('[data-testid="export-param-builder"]')
    const exportCustomBtn = builder.find('[data-testid="param-builder-export-custom"]')
    expect(exportCustomBtn.exists()).toBe(true)
    await exportCustomBtn.trigger('click')
    await flushPromises()
    expect(spies.exportCustomVstSpy).toHaveBeenCalled()
  })
})

describe('PresetManagerView', () => {
  it('renders create form', async () => {
    const wrapper = mount(PresetManagerView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="create-form"]').exists()).toBe(true)
  })

  it('renders preset cards', async () => {
    const wrapper = mount(PresetManagerView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="preset-card"]').exists()).toBe(true)
  })
})
