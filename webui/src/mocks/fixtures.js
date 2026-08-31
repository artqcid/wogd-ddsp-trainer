/**
 * Mock-data fixtures (mock-data seam).
 *
 * Deterministic sample data used by `MockApiClient` so every view can render
 * offline / in Vitest without a running backend.
 */

export const healthFixture = {
  status: 'ok',
  backend: 'mock',
  version: '0.1.0',
}
