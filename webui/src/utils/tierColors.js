/* ===== Tier Identity Color System ===== */

export const TIER_META = {
  standard: { label: 'Standard', icon: '●', color: 'var(--tier-standard)' },
  component: { label: 'Component', icon: '◆', color: 'var(--tier-component)' },
  hacks: { label: 'Hacks', icon: '⚡', color: 'var(--tier-hacks)' },
  engine: { label: 'Engine', icon: '◈', color: 'var(--tier-engine)' },
  advanced: { label: 'Advanced', icon: '✦', color: 'var(--tier-advanced)' },
}

export const TIER_ORDER = ['standard', 'component', 'hacks', 'engine', 'advanced']

export function tierColor(tier) {
  return TIER_META[tier]?.color ?? 'var(--text-secondary)'
}

export function tierLabel(tier) {
  return TIER_META[tier]?.label ?? tier
}

export function tierIcon(tier) {
  return TIER_META[tier]?.icon ?? '?'
}

export function tierAtLeast(tier, minimum) {
  const idx = TIER_ORDER.indexOf(tier)
  const minIdx = TIER_ORDER.indexOf(minimum)
  if (idx === -1 || minIdx === -1) return false
  return idx >= minIdx
}