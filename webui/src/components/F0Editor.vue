<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  f0Data: { type: Array, default: () => [] },
  sampleRate: { type: Number, default: 16000 },
  frameRate: { type: Number, default: 100 },
})

const emit = defineEmits(['update'])

const canvasRef = ref(null)
const isDrawing = ref(false)

const WIDTH = 600
const HEIGHT = 200

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, WIDTH, HEIGHT)
  
  // Background
  ctx.fillStyle = '#161b22'
  ctx.fillRect(0, 0, WIDTH, HEIGHT)
  
  // Grid lines
  ctx.strokeStyle = '#30363d'
  ctx.lineWidth = 0.5
  for (let x = 0; x < WIDTH; x += 40) {
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, HEIGHT)
    ctx.stroke()
  }
  for (let y = 0; y < HEIGHT; y += 40) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(WIDTH, y)
    ctx.stroke()
  }
  
  // F0 curve
  if (props.f0Data.length > 0) {
    const maxFreq = Math.max(...props.f0Data, 1)
    ctx.strokeStyle = '#58a6ff'
    ctx.lineWidth = 2
    ctx.beginPath()
    for (let i = 0; i < props.f0Data.length; i++) {
      const x = (i / props.f0Data.length) * WIDTH
      const y = HEIGHT - (props.f0Data[i] / maxFreq) * (HEIGHT - 10) - 5
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.stroke()
  }
}

function handleMouseMove(e) {
  if (!isDrawing.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const idx = Math.floor((x / WIDTH) * props.f0Data.length)
  const maxFreq = Math.max(...props.f0Data, 440)
  const freq = (1 - y / HEIGHT) * maxFreq
  if (idx >= 0 && idx < props.f0Data.length && freq >= 0) {
    const newData = [...props.f0Data]
    newData[idx] = freq
    emit('update', newData)
  }
}

onMounted(() => { draw() })
watch(() => props.f0Data, () => { nextTick(draw) }, { deep: true })
</script>

<template>
  <div class="f0-editor">
    <canvas
      ref="canvasRef"
      :width="WIDTH"
      :height="HEIGHT"
      class="f0-canvas"
      @mousedown="isDrawing = true"
      @mouseup="isDrawing = false"
      @mouseleave="isDrawing = false"
      @mousemove="handleMouseMove"
    />
    <div class="f0-editor-tools">
      <button class="btn-small" @click="$emit('update', f0Data.map(() => 0))">Clear</button>
      <button class="btn-small" @click="$emit('update', f0Data.map(() => 440))">Flat 440Hz</button>
    </div>
  </div>
</template>

<style scoped>
.f0-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.f0-canvas {
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: crosshair;
  width: 100%;
  height: auto;
}
.f0-editor-tools {
  display: flex;
  gap: 0.5rem;
}
.btn-small {
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
}
.btn-small:hover {
  background: var(--bg-secondary);
}
</style>
