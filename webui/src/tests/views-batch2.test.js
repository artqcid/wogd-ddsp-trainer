import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { MockApiClient } from '../mocks/mockApiClient.js'
import InferencePlaygroundView from '../views/InferencePlaygroundView.vue'
import ModelExportView from '../views/ModelExportView.vue'
import PresetManagerView from '../views/PresetManagerView.vue'

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

const mountOptions = {
  global: {
    provide: { apiClient: new MockApiClient() },
  },
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
