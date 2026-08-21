<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const manifest = ref(null)
const loadError = ref('')
const horizon = ref(3)
const frameIndex = ref(0)
const playing = ref(false)
let timer = null

const pad = (value) => String(value).padStart(3, '0')
const frameSrc = computed(() => manifest.value
  ? `figs/pred_frames/h${horizon.value}/frame_${pad(frameIndex.value)}.webp`
  : '')

const issueDate = computed(() => manifest.value?.issue_dates?.[frameIndex.value] ?? '')
const targetDate = computed(() => {
  if (!issueDate.value) return ''
  const date = new Date(`${issueDate.value}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + horizon.value)
  return date.toISOString().slice(0, 10)
})
const mae = computed(() => manifest.value?.mae_by_horizon?.[String(horizon.value)]?.[frameIndex.value])
const rowCount = computed(() => manifest.value?.rows_by_horizon?.[String(horizon.value)]?.[frameIndex.value])

function stop() {
  playing.value = false
  if (timer) window.clearInterval(timer)
  timer = null
}

function togglePlay() {
  if (playing.value) {
    stop()
    return
  }
  playing.value = true
  timer = window.setInterval(() => {
    if (!manifest.value) return
    frameIndex.value = (frameIndex.value + 1) % manifest.value.n_frames
  }, 900)
}

function step(amount) {
  if (!manifest.value) return
  stop()
  frameIndex.value = (frameIndex.value + amount + manifest.value.n_frames) % manifest.value.n_frames
}

onMounted(async () => {
  try {
    const response = await fetch('figs/pred_frames/manifest.json')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    manifest.value = await response.json()
    frameIndex.value = Math.floor(manifest.value.n_frames / 2)
  } catch (error) {
    loadError.value = `The diagnostic frames could not be loaded (${error.message}).`
  }
})

watch([frameIndex, horizon], () => {
  if (!manifest.value) return
  const next = (frameIndex.value + 1) % manifest.value.n_frames
  const image = new Image()
  image.src = `figs/pred_frames/h${horizon.value}/frame_${pad(next)}.webp`
})

onBeforeUnmount(stop)
</script>

<template>
  <section class="card overflow-hidden">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <div class="label-caps">Interactive forecast viewer</div>
        <h2 class="mt-2 text-2xl font-semibold text-ink-950">Observed, predicted, and residual</h2>
        <p class="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
          Explore 48 representative issue dates from the 2023 single-split test year. Every horizon uses the final 32-feature v2 model.
        </p>
      </div>
      <div v-if="manifest" class="flex flex-wrap gap-2 text-xs">
        <span class="badge badge-info">Issue {{ issueDate }}</span>
        <span class="badge badge-pass">Target {{ targetDate }}</span>
        <span class="badge badge-warn">Sample MAE {{ mae?.toFixed(3) }}</span>
      </div>
    </div>

    <div v-if="loadError" class="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
      {{ loadError }}
    </div>

    <template v-else-if="manifest">
      <div class="mt-6 rounded-xl border border-slate-200 bg-slate-100 overflow-x-auto">
        <img
          :src="frameSrc"
          :alt="`Observed target, H+${horizon} prediction, and residual for issue date ${issueDate}`"
          class="block w-full min-w-[820px] h-auto"
        />
      </div>

      <div class="mt-5 grid gap-5 lg:grid-cols-[auto_1fr] lg:items-end">
        <div>
          <div class="label-caps mb-2">Forecast horizon</div>
          <div class="flex flex-wrap gap-1.5" role="group" aria-label="Forecast horizon">
            <button
              v-for="h in manifest.horizons"
              :key="h"
              type="button"
              @click="horizon = h"
              :class="['min-w-12 rounded-lg px-3 py-2 text-sm font-semibold transition-colors',
                horizon === h ? 'bg-ink-950 text-white' : 'border border-slate-200 bg-white text-slate-600 hover:border-teal-300']"
            >
              H+{{ h }}
            </button>
          </div>
        </div>

        <div>
          <div class="flex items-center justify-between gap-3">
            <label for="prediction-day" class="label-caps">Issue date · {{ issueDate }}</label>
            <span class="font-mono text-xs text-slate-500">{{ frameIndex + 1 }} / {{ manifest.n_frames }}</span>
          </div>
          <input
            id="prediction-day"
            v-model.number="frameIndex"
            type="range"
            min="0"
            :max="manifest.n_frames - 1"
            step="1"
            class="mt-3 w-full accent-teal-700"
            @input="stop"
          />
        </div>
      </div>

      <div class="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-slate-200 pt-5">
        <div class="flex items-center gap-2">
          <button type="button" class="button-light !min-h-10 !px-3 !py-2" @click="step(-1)" aria-label="Previous date">←</button>
          <button type="button" class="button-dark !min-h-10 !px-4 !py-2" @click="togglePlay">
            {{ playing ? 'Pause' : 'Play' }}
          </button>
          <button type="button" class="button-light !min-h-10 !px-3 !py-2" @click="step(1)" aria-label="Next date">→</button>
        </div>
        <p class="text-xs text-slate-500">
          {{ rowCount?.toLocaleString() }} observed target rows · colour limits stay fixed across dates
        </p>
      </div>

      <div class="mt-5 rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-xs leading-relaxed text-slate-700">
        The smooth rasters are linear interpolations of sampled rows for visual continuity and are masked outside the sample’s convex hull. Training and metrics use the original rows only; raster pixels are not extra observations.
      </div>
    </template>

    <div v-else class="mt-6 h-72 rounded-xl bg-slate-100 animate-pulse" aria-label="Loading forecast viewer"></div>
  </section>
</template>

