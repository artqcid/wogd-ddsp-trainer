import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import HealthView from '../views/HealthView.vue'
import { MockApiClient } from '../mocks/mockApiClient.js'

describe('HealthView', () => {
  it('renders with the injected mock API client', () => {
    const wrapper = mount(HealthView, {
      global: {
        provide: { apiClient: new MockApiClient() },
      },
    })
    expect(wrapper.get('[data-testid="api-client-status"]').text()).toBe(
      'API client injected'
    )
    expect(wrapper.text()).toContain('Health check')
  })
})
