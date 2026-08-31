import { describe, it, expect } from 'vitest'
import { MockApiClient } from '../mocks/mockApiClient.js'
import { healthFixture } from '../mocks/fixtures.js'

describe('MockApiClient', () => {
  it('returns the health fixture', async () => {
    const client = new MockApiClient()
    await expect(client.health()).resolves.toEqual(healthFixture)
  })
})
