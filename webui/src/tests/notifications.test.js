import { describe, it, expect } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useNotificationsStore } from '../stores/notifications.js'

describe('notifications store', () => {
  it('adds and dismisses notifications', () => {
    setActivePinia(createPinia())
    const store = useNotificationsStore()
    expect(store.items).toHaveLength(0)

    const id = store.info('hello')
    expect(store.items).toHaveLength(1)
    expect(store.items[0].message).toBe('hello')
    expect(store.items[0].kind).toBe('info')

    store.dismiss(id)
    expect(store.items).toHaveLength(0)
  })
})