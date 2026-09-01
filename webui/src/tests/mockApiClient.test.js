import { describe, it, expect } from 'vitest'
import { MockApiClient } from '../mocks/mockApiClient.js'
import { healthFixture, PARAM_MANIFEST_FIXTURES } from '../mocks/fixtures.js'

describe('MockApiClient', () => {
  it('returns the health fixture', async () => {
    const client = new MockApiClient()
    await expect(client.health()).resolves.toEqual(healthFixture)
  })
})

describe('MockApiClient getCheckpointParams', () => {
  it('returns a fixture with correct shape', async () => {
    const client = new MockApiClient()
    const manifest = await client.getCheckpointParams('run_abc123', 'step-100.pt')
    expect(manifest).toHaveProperty('format', 'wogd-vst-params')
    expect(manifest).toHaveProperty('version', '1.0')
    expect(manifest.params).toBeInstanceOf(Array)
    expect(manifest.params.length).toBeGreaterThanOrEqual(4)
    for (const p of manifest.params) {
      expect(p).toHaveProperty('slot')
      expect(p).toHaveProperty('name')
      expect(p).toHaveProperty('param_type')
      expect(p).toHaveProperty('min_value')
      expect(p).toHaveProperty('max_value')
      expect(p).toHaveProperty('default_value')
    }
  })

  it('returns standard-tier fixture for run_abc123', async () => {
    const client = new MockApiClient()
    const manifest = await client.getCheckpointParams('run_abc123', 'step-100.pt')
    expect(manifest.params.length).toBe(PARAM_MANIFEST_FIXTURES.standard.params.length)
    expect(manifest.params.every(p => p.neutone_slot !== null)).toBe(true)
  })

  it('returns updateCheckpointParams stored value on re-fetch', async () => {
    const client = new MockApiClient()
    const runId = 'run_abc123'
    const ckpt = 'step-100.pt'
    const original = await client.getCheckpointParams(runId, ckpt)
    const updated = { ...original, params: original.params.map(p => ({ ...p, name: p.name + ' (edited)' })) }
    await client.updateCheckpointParams(runId, ckpt, updated)
    const refetched = await client.getCheckpointParams(runId, ckpt)
    expect(refetched.params[0].name).toBe(updated.params[0].name)
  })
})

describe('MockApiClient export methods', () => {
  it('exportNeutone returns a Blob', async () => {
    const client = new MockApiClient()
    const blob = await client.exportNeutone('run_abc123', 'step-100.pt')
    expect(blob).toBeInstanceOf(Blob)
  })

  it('exportCustomVST returns a Blob', async () => {
    const client = new MockApiClient()
    const blob = await client.exportCustomVST('run_abc123', 'step-100.pt')
    expect(blob).toBeInstanceOf(Blob)
  })
})
