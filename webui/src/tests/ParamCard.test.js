import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ParamCard from '../components/ParamCard.vue'

const baseParam = {
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
}

function mountParamCard(overrides = {}) {
  return mount(ParamCard, {
    props: {
      param: { ...baseParam, ...overrides.param },
      index: overrides.index ?? 0,
      isNeutoneAssigned: overrides.isNeutoneAssigned ?? true,
      readonly: overrides.readonly ?? false,
    },
    attachTo: document.body,
  })
}

describe('ParamCard', () => {
  it('renders with continuous param fixture: all fields populated', () => {
    const wrapper = mountParamCard()
    expect(wrapper.find('[data-testid="param-card"]').exists()).toBe(true)

    expect(wrapper.find('[data-testid="param-name-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-name-input"]').element.value).toBe(baseParam.name)

    expect(wrapper.find('[data-testid="param-description-input"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="param-description-input"]').element.value).toBe(baseParam.description)

    const typeRadios = wrapper.findAll('[data-testid="param-type-radio"]')
    const continuousRadio = typeRadios.filter(el => el.attributes('value') === 'continuous')[0]
    expect(continuousRadio.exists()).toBe(true)
    expect(continuousRadio.element.checked).toBe(true)

    expect(wrapper.find('[data-testid="param-min-input"]').element.value).toBe(String(baseParam.min_value))
    expect(wrapper.find('[data-testid="param-max-input"]').element.value).toBe(String(baseParam.max_value))
    expect(wrapper.find('[data-testid="param-default-input"]').element.value).toBe(String(baseParam.default_value))

    const mappingRadios = wrapper.findAll('[data-testid="param-mapping-select"]')
    const linearRadio = mappingRadios.filter(el => el.attributes('value') === 'linear')[0]
    expect(linearRadio.exists()).toBe(true)

    expect(wrapper.find('[data-testid="param-unit-input"]').element.value).toBe(baseParam.unit_hint)
    expect(wrapper.find('[data-testid="param-group-input"]').element.value).toBe(baseParam.group)

    // Default base param is not neutone-assigned → no badge
    expect(wrapper.find('[data-testid="neutone-badge"]').exists()).toBe(false)
  })

  it('renders categorical param with correct radio checked', () => {
    const wrapper = mountParamCard({ param: { ...baseParam, param_type: 'categorical' } })
    const typeRadios = wrapper.findAll('[data-testid="param-type-radio"]')
    const categoricalRadio = typeRadios.filter(el => el.attributes('value') === 'categorical')[0]
    expect(categoricalRadio.exists()).toBe(true)
    expect(categoricalRadio.element.checked).toBe(true)
  })

  it('name >30 chars shows validation error', async () => {
    const longName = 'A'.repeat(31)
    const wrapper = mountParamCard({ param: { ...baseParam, name: longName } })
    expect(wrapper.find('[data-testid="name-counter"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="name-counter"]').text()).toBe('31/30')

    const nameInput = wrapper.find('[data-testid="param-name-input"]')
    expect(nameInput.classes('form-input--error')).toBe(true)

    // grow further and verify counter stays in overflow state
    await nameInput.setValue('AB'.repeat(16))
    expect(wrapper.find('[data-testid="name-counter"]').text()).toContain('/30')
    expect(wrapper.find('[data-testid="name-counter"]').classes('param-card__counter--overflow')).toBe(true)
    expect(nameInput.classes('form-input--error')).toBe(true)
  })

  it('min > max shows validation error on both fields', async () => {
    const wrapper = mountParamCard({ param: { ...baseParam, min_value: 50, max_value: 10 } })

    expect(wrapper.find('[data-testid="param-min-input"]').classes('form-input--error')).toBe(true)
    expect(wrapper.find('[data-testid="param-max-input"]').classes('form-input--error')).toBe(true)
  })

  it('update:param emitted on name change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    const nameInput = wrapper.find('[data-testid="param-name-input"]')

    vi.useFakeTimers()
    await nameInput.setValue('New Param Name')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ name: 'New Param Name' })
    )
  })

  it('update:param emitted on description change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    const descInput = wrapper.find('[data-testid="param-description-input"]')

    vi.useFakeTimers()
    await descInput.setValue('Updated description')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ description: 'Updated description' })
    )
  })

  it('update:param emitted on min change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })

    vi.useFakeTimers()
    wrapper.find('[data-testid="param-min-input"]').setValue('-10')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ min_value: -10 })
    )
  })

  it('update:param emitted on max change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })

    vi.useFakeTimers()
    wrapper.find('[data-testid="param-max-input"]').setValue('30')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ max_value: 30 })
    )
  })

  it('update:param emitted on default change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })

    vi.useFakeTimers()
    wrapper.find('[data-testid="param-default-input"]').setValue('5')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ default_value: 5 })
    )
  })

  it('update:param emitted on mapping change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    const mappingRadios = wrapper.findAll('[data-testid="param-mapping-select"]')
    const logRadio = mappingRadios.filter(el => el.attributes('value') === 'log')[0]
    expect(logRadio.exists()).toBe(true)

    vi.useFakeTimers()
    logRadio.setValue('log')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ mapping: 'log' })
    )
  })

  it('update:param emitted on unit change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    const unitInput = wrapper.find('[data-testid="param-unit-input"]')

    vi.useFakeTimers()
    await unitInput.setValue('oct')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ unit_hint: 'oct' })
    )
  })

  it('update:param emitted on group change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    const groupInput = wrapper.find('[data-testid="param-group-input"]')

    vi.useFakeTimers()
    await groupInput.setValue('Custom Group')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ group: 'Custom Group' })
    )
  })

  it('update:param emitted on type change', async () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    const typeRadios = wrapper.findAll('[data-testid="param-type-radio"]')
    const categoricalRadio = typeRadios.filter(el => el.attributes('value') === 'categorical')[0]
    expect(categoricalRadio.exists()).toBe(true)

    vi.useFakeTimers()
    categoricalRadio.setValue('categorical')
    vi.runAllTimers()
    vi.useRealTimers()

    expect(wrapper.emitted('update:param')).toBeTruthy()
    expect(wrapper.emitted('update:param')[0][0]).toEqual(
      expect.objectContaining({ param_type: 'categorical' })
    )
  })

  it('remove emitted on Remove click', async () => {
    const wrapper = mountParamCard({ index: 2, isNeutoneAssigned: false })
    await wrapper.find('[data-testid="param-remove-btn"]').trigger('click')
    expect(wrapper.emitted('remove')).toBeTruthy()
    expect(wrapper.emitted('remove')[0][0]).toBe(2)
  })

  it('readonly=true → no Remove button, fields disabled', async () => {
    const wrapper = mountParamCard({ readonly: true })
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(wrapper.find('[data-testid="param-remove-btn"]').exists()).toBe(false)

    const nameInput = wrapper.find('[data-testid="param-name-input"]')
    expect(nameInput.exists()).toBe(true)
    expect(nameInput.attributes('disabled')).toBe('')

    const descInput = wrapper.find('[data-testid="param-description-input"]')
    expect(descInput.exists()).toBe(true)
    expect(descInput.attributes('disabled')).toBe('')

    const minInput = wrapper.find('[data-testid="param-min-input"]')
    expect(minInput.exists()).toBe(true)
    expect(minInput.attributes('disabled')).toBe('')

    const maxInput = wrapper.find('[data-testid="param-max-input"]')
    expect(maxInput.exists()).toBe(true)
    expect(maxInput.attributes('disabled')).toBe('')

    const defaultInput = wrapper.find('[data-testid="param-default-input"]')
    expect(defaultInput.exists()).toBe(true)
    expect(defaultInput.attributes('disabled')).toBe('')

    const unitInput = wrapper.find('[data-testid="param-unit-input"]')
    expect(unitInput.exists()).toBe(true)
    expect(unitInput.attributes('disabled')).toBe('')

    const groupInput = wrapper.find('[data-testid="param-group-input"]')
    expect(groupInput.exists()).toBe(true)
    expect(groupInput.attributes('disabled')).toBe('')

    const typeRadios = wrapper.findAll('[data-testid="param-type-radio"]')
    for (const radio of typeRadios) {
      expect(radio.exists()).toBe(true)
      expect(radio.attributes('disabled')).toBe('')
    }

    const mappingRadios = wrapper.findAll('[data-testid="param-mapping-select"]')
    for (const radio of mappingRadios) {
      expect(radio.exists()).toBe(true)
      expect(radio.attributes('disabled')).toBe('')
    }
  })

  it('isNeutoneAssigned=false → no neutone badge', () => {
    const wrapper = mountParamCard({ isNeutoneAssigned: false })
    expect(wrapper.find('[data-testid="neutone-badge"]').exists()).toBe(false)
  })

  it('neutone badge shows slot from param when assigned', () => {
    const wrapper = mountParamCard({ param: { ...baseParam, neutone_slot: 3 }, isNeutoneAssigned: true })
    expect(wrapper.find('[data-testid="neutone-badge"]').text()).toBe('NEUTONE S3')
  })

  it('slot label shows param.slot', () => {
    const wrapper = mountParamCard({ param: { ...baseParam, slot: 7 } })
    const slotEl = wrapper.find('.param-card__slot')
    expect(slotEl.text()).toBe('P7')
  })
})
