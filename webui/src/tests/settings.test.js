import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { MockApiClient } from '../mocks/mockApiClient.js'
import { settingsFixture } from '../mocks/fixtures.js'
import SettingsView from '../views/SettingsView.vue'

describe('SettingsView', () => {
  it('renders install and data directories from mock', async () => {
    const wrapper = mount(SettingsView, {
      global: { provide: { apiClient: new MockApiClient() } },
    })
    await flushPromises()
    expect(wrapper.find('[data-testid="install-dir"]').text()).toBe(settingsFixture.install_dir)
    expect(wrapper.find('[data-testid="data-dir"]').text()).toBe(settingsFixture.data_dir)
    expect(wrapper.find('[data-testid="datasets-dir"]').text()).toBe(settingsFixture.datasets_dir)
    expect(wrapper.find('[data-testid="runs-dir"]').text()).toBe(settingsFixture.runs_dir)
    expect(wrapper.find('[data-testid="db-path"]').text()).toBe(settingsFixture.db_path)
    expect(wrapper.find('[data-testid="data-default"]').text()).toBe('Using default')
  })

  it('saves a new data directory and shows the updated path', async () => {
    const wrapper = mount(SettingsView, {
      global: { provide: { apiClient: new MockApiClient() } },
    })
    await flushPromises()

    const input = wrapper.find('[data-testid="data-dir-input"]')
    await input.setValue('C:/Users/demo/AppData/Local/wogd-ddsp-trainer-custom')
    await wrapper.find('[data-testid="save-data-dir"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="data-dir"]').text()).toBe(
      'C:/Users/demo/AppData/Local/wogd-ddsp-trainer-custom',
    )
    expect(wrapper.find('[data-testid="data-default"]').text()).toBe('Custom location')
  })

  it('rejects a relative data directory', async () => {
    const wrapper = mount(SettingsView, {
      global: { provide: { apiClient: new MockApiClient() } },
    })
    await flushPromises()

    const input = wrapper.find('[data-testid="data-dir-input"]')
    await input.setValue('relative/path')
    await wrapper.find('[data-testid="save-data-dir"]').trigger('click')
    await flushPromises()

    expect(wrapper.find('[data-testid="save-message"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="data-dir"]').text()).toBe(settingsFixture.data_dir)
  })
})
