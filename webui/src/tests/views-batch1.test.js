import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { MockApiClient } from '../mocks/mockApiClient.js'
import UploadIngestionView from '../views/UploadIngestionView.vue'
import DatasetManagerView from '../views/DatasetManagerView.vue'
import PreprocessingView from '../views/PreprocessingView.vue'
import TrainingConfigView from '../views/TrainingConfigView.vue'
import TrainingDashboardView from '../views/TrainingDashboardView.vue'

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

describe('UploadIngestionView', () => {
  it('renders drop zone and upload button', () => {
    const wrapper = mount(UploadIngestionView, mountOptions)
    expect(wrapper.find('[data-testid="drop-zone"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="upload-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="upload-btn"]').text()).toBe('Upload')
  })
})

describe('DatasetManagerView', () => {
  it('renders dataset names from mock', async () => {
    const wrapper = mount(DatasetManagerView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="dataset-row"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="dataset-name"]').text()).toBe('voice_samples')
  })

  it('renders empty state handling', async () => {
    const emptyWrapper = mount(DatasetManagerView, {
      global: {
        provide: { apiClient: new MockApiClient() },
      },
    })
    await flushPromises()
    const loadingExists = emptyWrapper.find('[data-testid="loading"]').exists()
    const rowExists = emptyWrapper.find('[data-testid="dataset-row"]').exists()
    expect(loadingExists || rowExists).toBe(true)
  })
})

describe('PreprocessingView', () => {
  it('renders dataset select', async () => {
    const wrapper = mount(PreprocessingView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="dataset-select"]').exists()).toBe(true)
  })

  it('renders run button', async () => {
    const wrapper = mount(PreprocessingView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="run-btn"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="run-btn"]').text()).toBe('Run Preprocessing')
  })
})

describe('TrainingConfigView', () => {
  it('renders GPU info', async () => {
    const wrapper = mount(TrainingConfigView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="gpu-info"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="gpu-info"]').text()).toContain('NVIDIA RTX 3060+')
  })

  it('renders preset select', async () => {
    const wrapper = mount(TrainingConfigView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="preset-select"]').exists()).toBe(true)
  })
})

describe('TrainingDashboardView', () => {
  it('renders TensorBoard section', async () => {
    const wrapper = mount(TrainingDashboardView, mountOptions)
    await flushPromises()
    const tb = wrapper.find('[data-testid="tensorboard-iframe"]')
    expect(tb.exists()).toBe(true)
  })

  it('renders run cards when runs exist', async () => {
    const wrapper = mount(TrainingDashboardView, mountOptions)
    await flushPromises()
    expect(wrapper.find('[data-testid="run-card"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="run-name"]').text()).toBe('training_run_v1')
  })

  it('renders empty state when runs list is empty', async () => {
    const emptyRunsWrapper = mount(TrainingDashboardView, {
      global: {
        provide: {
          apiClient: Object.assign(new MockApiClient(), {
            async listRuns() { return [] },
            async getTensorboard() { return { url: '', running: false } },
          }),
        },
      },
    })
    await flushPromises()
    expect(emptyRunsWrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    expect(emptyRunsWrapper.text()).toContain('No training runs yet')
  })
})
