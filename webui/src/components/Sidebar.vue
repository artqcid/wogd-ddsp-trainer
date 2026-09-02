<template>
  <nav class="sidebar">
    <div class="sidebar-brand">
      <svg class="sidebar-brand-icon" viewBox="0 0 24 24" width="20" height="20" fill="none">
        <defs>
          <linearGradient id="brand-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="var(--accent)" />
            <stop offset="100%" stop-color="var(--accent-2)" />
          </linearGradient>
        </defs>
        <path d="M12 2L2 7v10l10 5 10-5V7l-10-5z" fill="url(#brand-grad)" opacity="0.9" />
        <path d="M12 12l-6-3v6l6 3 6-3V9l-6 3z" fill="var(--bg-primary)" opacity="0.5" />
      </svg>
      <span class="gradient-text">wogd-ddsp</span>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">📦 Datasets &amp; Preprocessing</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/datasets" class="sidebar-link">📤 Upload &amp; Ingestion</RouterLink>
        </li>
        <li>
          <RouterLink to="/datasets/manager" class="sidebar-link">🗂️ Dataset Manager</RouterLink>
        </li>
        <li>
          <RouterLink to="/datasets/preprocess" class="sidebar-link">⚙️ Preprocessing</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">🧠 Training</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/model" class="sidebar-link">🎛️ Training Config</RouterLink>
        </li>
        <li>
          <RouterLink to="/training" class="sidebar-link">📈 Training Dashboard</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">📋 Presets</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/presets" class="sidebar-link">📋 Preset Manager</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">🔊 Inference &amp; Export</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/inference" class="sidebar-link">🎵 Inference Playground</RouterLink>
        </li>
        <li>
          <RouterLink to="/export" class="sidebar-link">💾 Model Export</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">🚀 Advanced Features</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/voice-conversion" class="sidebar-link">🎤 Voice Conversion</RouterLink>
        </li>
        <li>
          <RouterLink to="/experimental/morphing" class="sidebar-link">🔄 Morphing</RouterLink>
        </li>
        <li>
          <RouterLink to="/experimental/latent-explore" class="sidebar-link">🌌 Latent Explorer</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-group">
      <div class="sidebar-group-label">🧪 Experimental</div>
      <ul class="sidebar-links">
        <li>
          <RouterLink to="/experimental/reverb" class="sidebar-link">🔊 Reverb IR</RouterLink>
        </li>
        <li>
          <RouterLink to="/experimental/f0-editor" class="sidebar-link">🎼 F0 Editor</RouterLink>
        </li>
        <li>
          <RouterLink to="/experimental/mixer" class="sidebar-link">🔀 Component Mixer</RouterLink>
        </li>
        <li>
          <RouterLink to="/experimental/synth-hacks" class="sidebar-link">⚡ Synth Hacks</RouterLink>
        </li>
      </ul>
    </div>

    <div class="sidebar-footer">
      <RouterLink to="/settings" class="sidebar-link sidebar-link--footer">⚙️ Settings</RouterLink>
    </div>
  </nav>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  border-bottom: 1px solid var(--border);
}

.sidebar-brand-icon {
  flex-shrink: 0;
}

.sidebar-group {
  padding: var(--space-2) 0;
}

.sidebar-group-label {
  padding: var(--space-1) var(--space-4);
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-secondary);
}

.sidebar-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.sidebar-link {
  display: block;
  padding: var(--space-2) var(--space-4);
  color: var(--text-primary);
  text-decoration: none;
  font-size: 0.875rem;
  border-left: 3px solid transparent;
  transition: background var(--transition-fast), border-color var(--transition-fast);
}

.sidebar-link:hover {
  background: var(--bg-tertiary);
}

.sidebar-link.router-link-active {
  background: var(--bg-tertiary);
  border-left-color: var(--accent);
  color: var(--accent);
  box-shadow: inset 2px 0 8px var(--accent-glow);
}

.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid var(--border);
  padding: var(--space-2) 0;
}

.sidebar-link--footer {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
</style>
