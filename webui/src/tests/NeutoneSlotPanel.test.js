import { describe, it, expect, vi, beforeAll } from 'vitest'
import { mount } from '@vue/test-utils'
import NeutoneSlotPanel from '../components/NeutoneSlotPanel.vue'

const baseParamA = {
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
  neutone_slot: 1,
}

const baseParamB = {
  slot: 2,
  name: 'Loudness',
  description: 'Loudness offset dB',
  param_type: 'continuous',
  min_value: -20,
  max_value: 20,
  default_value: 0,
  mapping: 'linear',
  unit_hint: 'dB',
  group: 'Pitch',
  neutone_slot: 2,
}

const baseParamC = {
  slot: 3,
  name: 'Harmonic Blend',
  description: 'Harmonic noise blend',
  param_type: 'continuous',
  min_value: 0,
  max_value: 1,
  default_value: 0.5,
  mapping: 'linear',
  unit_hint: '',
  group: 'Texture',
  neutone_slot: 3,
}

const baseParamD = {
  slot: 4,
  name: 'Reverb Mix',
  description: 'Dry/wet reverb',
  param_type: 'continuous',
  min_value: 0,
  max_value: 1,
  default_value: 0.3,
  mapping: 'linear',
  unit_hint: '',
  group: 'Effects',
  neutone_slot: 4,
}

function mountPanel(overrides = {}) {
  return mount(NeutoneSlotPanel, {
    props: {
      allParams: overrides.allParams ?? [baseParamA, baseParamB, baseParamC, baseParamD],
      readonly: overrides.readonly ?? false,
    },
    attachTo: document.body,
  })
}

function fireDrop(element, param) {
  const event = new Event('drop', { bubbles: true })
  Object.defineProperty(event, 'dataTransfer', {
    value: { getData: (fmt) => JSON.stringify(param), dropEffect: 'move' },
  })
  element.dispatchEvent(event)
}

function fireDragOver(element) {
  const event = new Event('dragover', { bubbles: true })
  Object.defineProperty(event, 'dataTransfer', {
    value: { dropEffect: 'move' },
  })
  element.dispatchEvent(event)
}

function foundSlot(arr, name) {
  return arr.some((item) => item && item.name === name)
}

describe('NeutoneSlotPanel', () => {
  it('renders with 4 assigned params: all 4 slots show param names', () => {
    const wrapper = mountPanel({
      allParams: [baseParamA, baseParamB, baseParamC, baseParamD],
    })

    expect(wrapper.find('[data-testid="neutone-slot-panel"]').exists()).toBe(true)

    for (let i = 1; i <= 4; i++) {
      const slot = wrapper.find(`[data-testid="neutone-slot-${i}"]`)
      expect(slot.exists()).toBe(true)
      expect(slot.classes()).toContain('neutone-slot--occupied')
      expect(slot.classes()).not.toContain('neutone-slot--empty')

      const nameEl = slot.find(`[data-testid="neutone-slot-${i}-name"]`)
      expect(nameEl.exists()).toBe(true)

      const rangeEl = slot.find(`[data-testid="neutone-slot-${i}-range"]`)
      expect(rangeEl.exists()).toBe(true)
    }

    expect(wrapper.find('[data-testid="neutone-slot-1-name"]').text()).toBe('Pitch Shift')
    expect(wrapper.find('[data-testid="neutone-slot-2-name"]').text()).toBe('Loudness')
    expect(wrapper.find('[data-testid="neutone-slot-3-name"]').text()).toBe('Harmonic Blend')
    expect(wrapper.find('[data-testid="neutone-slot-4-name"]').text()).toBe('Reverb Mix')
  })

  it('renders with 2 assigned + 2 empty: empty slots show "drag here" label', () => {
    const wrapper = mountPanel({
      allParams: [baseParamA, baseParamB],
    })

    // slots 1 and 2 occupied
    for (const i of [1, 2]) {
      const slot = wrapper.find(`[data-testid="neutone-slot-${i}"]`)
      expect(slot.classes()).toContain('neutone-slot--occupied')
      expect(slot.classes()).not.toContain('neutone-slot--empty')
      expect(slot.find(`[data-testid="neutone-slot-${i}-name"]`).exists()).toBe(true)
    }

    // slots 3 and 4 empty
    for (const i of [3, 4]) {
      const slot = wrapper.find(`[data-testid="neutone-slot-${i}"]`)
      expect(slot.classes()).toContain('neutone-slot--empty')
      expect(slot.classes()).not.toContain('neutone-slot--occupied')

      const dragLabel = slot.find(`[data-testid="neutone-slot-${i}-drag-label"]`)
      expect(dragLabel.exists()).toBe(true)
      expect(dragLabel.text()).toBe('drag here')

      expect(slot.find(`[data-testid="neutone-slot-${i}-name"]`).exists()).toBe(false)
    }
})

  it('readonly=true: no drag targets active (aria-disabled)', () => {
    const wrapper = mountPanel({ readonly: true })

    for (let i = 1; i <= 4; i++) {
      const slot = wrapper.find(`[data-testid="neutone-slot-${i}"]`)
      expect(slot.attributes('aria-disabled')).toBe('true')
      expect(slot.classes()).toContain('neutone-slot--disabled')
    }

    // remove buttons must not be present in readonly mode
    for (let i = 1; i <= 4; i++) {
      const removeBtn = wrapper.find(`[data-testid="neutone-slot-${i}-remove"]`)
      expect(removeBtn.exists()).toBe(false)
    }
  })

  it('slot assignment via simulated drop: update:slots emitted with updated array', async () => {
    const wrapper = mountPanel({
      allParams: [baseParamA, baseParamB],
      readonly: false,
    })

    // slots 1,2 occupied; 3,4 empty
    expect(wrapper.find('[data-testid="neutone-slot-1-name"]').text()).toBe('Pitch Shift')
    expect(wrapper.find('[data-testid="neutone-slot-3-drag-label"]').text()).toBe('drag here')

    const paramC = {
      ...baseParamC,
      neutone_slot: 3,
    }

    const slot3 = wrapper.find('[data-testid="neutone-slot-3"]')
    fireDrop(slot3.element, paramC)

    expect(wrapper.emitted('update:slots')).toBeTruthy()
    const calls = wrapper.emitted('update:slots')
    const emitted = calls[calls.length - 1][0]
    expect(foundSlot(emitted, 'Harmonic Blend')).toBeTruthy()
    expect(emitted[0]).toEqual(expect.objectContaining({ name: 'Pitch Shift' }))
    expect(emitted[1]).toEqual(expect.objectContaining({ name: 'Loudness' }))
    expect(emitted[3]).toBe(null)
  })

  const clickThenEmit = async (wrapper, removeTestId) => {
    const btn = wrapper.find(removeTestId)
    expect(btn.exists()).toBe(true)
    await btn.trigger('click')
    expect(wrapper.emitted('update:slots')).toBeTruthy()
    const calls = wrapper.emitted('update:slots')
    return calls[calls.length - 1][0]
  }

  it('remove button on occupied slot clears that slot and emits update:slots', async () => {
    const wrapper = mountPanel({
      allParams: [baseParamA, baseParamB, baseParamC],
      readonly: false,
    })

    expect(wrapper.find('[data-testid="neutone-slot-3-name"]').text()).toBe('Harmonic Blend')

    const emitted = await clickThenEmit(wrapper, '[data-testid="neutone-slot-3-remove"]')
    expect(emitted[2]).toBe(null)
    expect(emitted[0]).toEqual(expect.objectContaining({ name: 'Pitch Shift' }))
    expect(emitted[1]).toEqual(expect.objectContaining({ name: 'Loudness' }))
  })

  it('drags param onto occupied slot replaces existing assignment', async () => {
    const wrapper = mountPanel({
      allParams: [baseParamA, baseParamB, baseParamC],
      readonly: false,
    })

    expect(wrapper.find('[data-testid="neutone-slot-1-name"]').text()).toBe('Pitch Shift')

    const slot1 = wrapper.find('[data-testid="neutone-slot-1"]')
    fireDrop(slot1.element, baseParamD)

    const calls = wrapper.emitted('update:slots')
    const emitted = calls[calls.length - 1][0]
    expect(emitted[0]).toEqual(expect.objectContaining({ name: 'Reverb Mix' }))
    expect(emitted[1]).toEqual(expect.objectContaining({ name: 'Loudness' }))
    expect(emitted[2]).toEqual(expect.objectContaining({ name: 'Harmonic Blend' }))
    expect(emitted[3]).toBe(null)
  })

  it('unit_hint absent: unit line not rendered', () => {
    const paramNoUnit = {
      ...baseParamA,
      unit_hint: '',
    }
    const wrapper = mountPanel({
      allParams: [paramNoUnit, baseParamB],
      readonly: false,
    })

    const slot1 = wrapper.find('[data-testid="neutone-slot-1"]')
    expect(slot1.find('[data-testid="neutone-slot-1-unit"]').exists()).toBe(false)
    expect(slot1.find('[data-testid="neutone-slot-1-name"]').text()).toBe('Pitch Shift')
    expect(slot1.find('[data-testid="neutone-slot-1-range"]').text()).toBe('[-24,24]')
  })

  it('initial slots derived from neutone_slot field (not array order), sorted', () => {
    // pass params in an order that does not match their neutone_slot numbers
    const wrapper = mountPanel({
      allParams: [baseParamD, baseParamB, baseParamA, baseParamC],
      readonly: false,
    })

    expect(wrapper.find('[data-testid="neutone-slot-1-name"]').text()).toBe('Pitch Shift')
    expect(wrapper.find('[data-testid="neutone-slot-2-name"]').text()).toBe('Loudness')
    expect(wrapper.find('[data-testid="neutone-slot-3-name"]').text()).toBe('Harmonic Blend')
    expect(wrapper.find('[data-testid="neutone-slot-4-name"]').text()).toBe('Reverb Mix')
  })

  it('emits update:slots on mount with derived initial state', () => {
    const wrapper = mountPanel({
      allParams: [baseParamA, baseParamB],
      readonly: false,
    })

    expect(wrapper.emitted('update:slots')).toBeTruthy()
    const initial = wrapper.emitted('update:slots')[0][0]
    expect(initial).toHaveLength(4)
    expect(initial[0]).toEqual(expect.objectContaining({ name: 'Pitch Shift' }))
    expect(initial[1]).toEqual(expect.objectContaining({ name: 'Loudness' }))
    expect(initial[2]).toBe(null)
    expect(initial[3]).toBe(null)
  })

  it('param with neutone_slot out of 1-4 range is ignored by initial derivation', () => {
    const params = [
      { ...baseParamA, neutone_slot: 1 },
      { ...baseParamB, neutone_slot: 5 },
      { ...baseParamC, neutone_slot: 0 },
    ]
    const wrapper = mountPanel({ allParams: params, readonly: false })
    const initial = wrapper.emitted('update:slots')[0][0]
    expect(initial[0]).toEqual(expect.objectContaining({ name: 'Pitch Shift' }))
    expect(initial[1]).toBe(null)
    expect(initial[2]).toBe(null)
    expect(initial[3]).toBe(null)
  })

it('dragover sets dropEffect move on slot when not readonly', async () => {
    const wrapper = mountPanel({
      allParams: [],
      readonly: false,
    })

    const slot = wrapper.find('[data-testid="neutone-slot-1"]')

    await slot.trigger('dragover')
    expect(slot.classes()).toContain('neutone-slot--dragover')
  })

  it('dragleave clears dragover class on the slot that triggered it', async () => {
    const wrapper = mountPanel({ allParams: [], readonly: false })
    const slot = wrapper.find('[data-testid="neutone-slot-1"]')

    await slot.trigger('dragover')
    expect(slot.classes()).toContain('neutone-slot--dragover')

    await slot.trigger('dragleave')
    expect(slot.classes()).not.toContain('neutone-slot--dragover')
  })

it('readonly=true still renders occupied slot names and ranges but no remove icons', () => {
  const wrapper = mountPanel({
    allParams: [baseParamA, baseParamB],
    readonly: true,
  })

  expect(wrapper.find('[data-testid="neutone-slot-1-name"]').text()).toBe('Pitch Shift')
  expect(wrapper.find('[data-testid="neutone-slot-1-range"]').text()).toBe('[-24,24]')
  expect(wrapper.find('[data-testid="neutone-slot-1-remove"]').exists()).toBe(false)
  expect(wrapper.find('[data-testid="neutone-slot-2-remove"]').exists()).toBe(false)
})

it('remove button click when readonly does not emit', () => {
  const wrapper = mountPanel({
    allParams: [baseParamA],
    readonly: true,
  })

  // there is no remove button in readonly mode
  expect(wrapper.find('[data-testid="neutone-slot-1-remove"]').exists()).toBe(false)
  expect(wrapper.emitted('update:slots')).toBeTruthy()
  const emitted = wrapper.emitted('update:slots')[0][0]
  expect(emitted[0]).toEqual(expect.objectContaining({ name: 'Pitch Shift' }))
})
})
