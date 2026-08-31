/**
 * API-client abstraction (mock-data seam).
 *
 * The web UI must never import backend code directly. All data access flows
 * through an object implementing the methods declared here. In development and
 * tests we inject `MockApiClient` from `../mocks/mockApiClient.js`; against a
 * running backend we inject a REST implementation.
 */

const healthKey = 'ApiClient.health'

export class ApiClient {
  /** @returns {Promise<{status: string, backend: string, version: string}>} */
  async health() {
    throw new Error(`${healthKey} not implemented`)
  }
}
