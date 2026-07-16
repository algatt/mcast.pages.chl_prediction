<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

// Loads the manifest written by experiment/export_prediction_frames.py and
// scrubs through pre-rendered Actual | Predicted | Error map frames. No compute
// happens in the browser — we just swap a pre-rendered <img> per day/horizon.

// Assets live in public/figs; reference them the same way FigureCard does —
// a plain relative path resolves correctly under both `vite dev` and the
// relative-`base` production build (and the hash-history routes).
const manifest = ref(null)
const loadError = ref(false)
const errorDetail = ref('')

const horizon = ref(3)
const dayIdx = ref(0)
const playing = ref(false)
const reference = ref('l3')   // 'l3' = observed (honest error); 'l4' = gap-free comparison
let timer = null
const SPEED_MS = 500

const hasL4 = computed(() => manifest.value?.has_l4 === true)

onMounted(async () => {
  const url = new URL('figs/pred_frames/manifest.json', document.baseURI).href
  try {
    const res = await fetch(url, { cache: 'no-store' })
    if (!res.ok) throw new Error(`HTTP ${res.status} at ${res.url}`)
    manifest.value = await res.json()
    if (!manifest.value.horizons.includes(horizon.value)) {
      horizon.value = manifest.value.horizons[0]
    }
    preloadHorizon(horizon.value)
  } catch (e) {
    errorDetail.value = `${e.message} (requested: ${url})`
    loadError.value = true
  }
})

onBeforeUnmount(() => stop())

const nFrames = computed(() => manifest.value?.n_frames ?? 0)
const dates = computed(() => manifest.value?.dates ?? [])
const currentDate = computed(() => dates.value[dayIdx.value] ?? '')
const currentMae = computed(() => {
  const key = reference.value === 'l4' ? 'mae_l4_by_horizon' : 'mae_by_horizon'
  const arr = manifest.value?.[key]?.[String(horizon.value)]
  return arr ? arr[dayIdx.value] : null
})

function framePath(h, idx, ref = reference.value) {
  const pad = String(idx).padStart(3, '0')
  const sub = ref === 'l4' ? 'l4/' : ''
  return `figs/pred_frames/h${h}/${sub}frame_${pad}.webp`
}
const currentFrame = computed(() => framePath(horizon.value, dayIdx.value))

// Preload every frame of a horizon/reference so playback/scrubbing is smooth.
const preloaded = new Set()
function preloadHorizon(h, ref = reference.value) {
  if (!manifest.value) return
  for (let i = 0; i < manifest.value.n_frames; i++) {
    const key = `${ref}:${h}:${i}`
    if (preloaded.has(key)) continue
    const img = new Image()
    img.src = framePath(h, i, ref)
    preloaded.add(key)
  }
}

watch([horizon, reference], ([h, r]) => preloadHorizon(h, r))

function step() {
  if (nFrames.value === 0) return
  dayIdx.value = (dayIdx.value + 1) % nFrames.value
}
function play() {
  if (playing.value || nFrames.value === 0) return
  playing.value = true
  timer = setInterval(step, SPEED_MS)
}
function stop() {
  playing.value = false
  if (timer) { clearInterval(timer); timer = null }
}
function toggle() { playing.value ? stop() : play() }
</script>

<template>
  <div class="card">
    <div v-if="loadError" class="text-sm text-slate-500 py-8 text-center">
      <p>Forecast frames not found. Run
      <span class="kbd">experiment/export_prediction_frames.py</span> and restart the dev server.</p>
      <p v-if="errorDetail" class="mt-2 text-xs text-rose-500 break-all font-mono">{{ errorDetail }}</p>
    </div>

    <template v-else-if="manifest">
      <!-- Controls -->
      <div class="flex flex-wrap items-center gap-4 mb-4">
        <button
          @click="toggle"
          class="px-4 py-2 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors inline-flex items-center gap-2 shrink-0"
        >
          <span v-if="playing">❚❚ Pause</span>
          <span v-else>▶ Play</span>
        </button>

        <div class="flex items-center gap-2 text-sm">
          <span class="font-semibold text-slate-700">Horizon</span>
          <div class="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
            <button
              v-for="h in manifest.horizons" :key="h" @click="horizon = h"
              :class="['px-3 py-1 rounded-md transition-colors tabular-nums',
                       horizon === h ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']"
            >
              H+{{ h }}
            </button>
          </div>
        </div>

        <div v-if="hasL4" class="flex items-center gap-2 text-sm">
          <span class="font-semibold text-slate-700">Reference</span>
          <div class="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
            <button @click="reference = 'l3'"
              :class="['px-3 py-1 rounded-md transition-colors',
                       reference === 'l3' ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']"
              title="L3 observed satellite field — the honest error (cloud gaps left blank)">
              L3 obs
            </button>
            <button @click="reference = 'l4'"
              :class="['px-3 py-1 rounded-md transition-colors',
                       reference === 'l4' ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']"
              title="L4 gap-free (DINEOF) product — a comparison reference, not ground truth">
              L4 gap-free
            </button>
          </div>
        </div>

        <div class="ml-auto flex items-center gap-4 text-sm tabular-nums">
          <span class="badge badge-info">{{ currentDate }}</span>
          <span v-if="currentMae !== null" class="text-slate-600">
            MAE<span class="text-slate-400">{{ reference === 'l4' ? ' vs L4' : ' vs L3' }}</span>
            <span class="font-semibold text-slate-900 ml-1">{{ currentMae.toFixed(3) }}</span>
          </span>
        </div>
      </div>

      <!-- Day slider -->
      <div class="flex items-center gap-4 mb-4">
        <label class="text-sm font-semibold text-slate-700 shrink-0">Day</label>
        <input
          type="range" min="0" :max="nFrames - 1" step="1"
          :value="dayIdx" @input="dayIdx = Number($event.target.value); stop()"
          class="flex-1 accent-ocean-600"
        />
        <span class="text-xs text-slate-500 tabular-nums shrink-0">
          {{ dayIdx + 1 }} / {{ nFrames }}
        </span>
      </div>

      <!-- Frame -->
      <figure class="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <img :src="currentFrame" :alt="`Forecast maps for ${currentDate}, H+${horizon}`"
             class="w-full h-auto" />
      </figure>
      <figcaption class="mt-3 text-sm text-slate-600 leading-relaxed">
        <template v-if="reference === 'l4'">
          <strong>Left:</strong> the conventional <em>gap-free L4</em> product (cloud gaps filled by
          DINEOF interpolation; only land is blank).
          <strong>Middle:</strong> the model's H+{{ horizon }} forecast — trained only on gappy L3.
          <strong>Right:</strong> error vs. L4 (predicted − L4). This is a <em>comparison</em>, not the
          honest score: L4 is itself interpolated, so this shows how closely our L3-trained forecast
          agrees with the standard product.
        </template>
        <template v-else>
          <strong>Left:</strong> actual L3 satellite chlorophyll (log₁₀ mg m⁻³, gaps = cloud/no data).
          <strong>Middle:</strong> the model's H+{{ horizon }} forecast for every pixel.
          <strong>Right:</strong> the honest error (predicted − observed); white ≈ zero, red =
          over-predict, blue = under-predict.
        </template>
      </figcaption>
    </template>

    <div v-else class="text-sm text-slate-500 py-8 text-center">Loading forecast frames…</div>
  </div>
</template>
