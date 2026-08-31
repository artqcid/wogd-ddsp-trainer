import { healthFixture } from './fixtures.js'

/**
 * Mock implementation of the API-client abstraction.
 *
 * Returns deterministic fixtures instead of calling the backend. Used for
 * offline dev mode and Vitest rendering tests (mock-data seam).
 */
export class MockApiClient {
  async health() {
    return { ...healthFixture }
  }
}
