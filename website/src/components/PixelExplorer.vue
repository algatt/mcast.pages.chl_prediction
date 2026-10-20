<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// One pixel's observed chlorophyll over a few weeks, with a chosen issue day:
// the inputs the forecast receives, and the observed targets it is scored on.
// Inputs and targets are the values the notebook computed, not recomputed here.
const props = defineProps({
  example: { type: Object, required: true },
})

const series = props.example.series
const issues = props.example.issues
const index = ref(Math.min(7, issues.length - 1))
const issue = computed(() => issues[index.value])

const dayIndex = Object.fromEntries(series.map((s, k) => [s.date, k]))
const DAY_MS = 86400000
const shift = (date, days) => new Date(Date.parse(`${date}T00:00:00Z`) + days * DAY_MS).toISOString().slice(0, 10)
const label = (date) => new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const longLabel = (date) => new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'long', timeZone: 'UTC' })
const mg = (v) => `${v < 0.1 ? v.toFixed(3) : v.toFixed(2)} mg/m³`

// Chart geometry, drawn at the displayed width.
const root = ref(null)
const W = ref(640)
let observer = null
onMounted(() => {
  observer = new ResizeObserver(([e]) => { W.value = Math.max(300, Math.round(e.contentRect.width)) })
  observer.observe(root.value)
})
onBeforeUnmount(() => observer?.disconnect())

const H = 230
const M = { top: 22, right: 12, bottom: 28, left: 44 }
const values = series.map((s) => s.chl).filter((v) => v !== null)
const Y_MAX = Math.ceil((Math.max(...values) * 1.15) / 0.05) * 0.05
const yTicks = Array.from({ length: Math.round(Y_MAX / 0.05) + 1 }, (_, k) => +(k * 0.05).toFixed(2))
  .filter((_, k, all) => all.length <= 6 || k % 2 === 0)
const plotW = computed(() => W.value - M.left - M.right)
const plotH = H - M.top - M.bottom
const step = computed(() => plotW.value / series.length)
const x = (k) => M.left + (k + 0.5) * step.value
const y = (v) => M.top + plotH * (1 - v / Y_MAX)

const issueK = computed(() => dayIndex[issue.value.date])
const windowRect = computed(() => ({ x: M.left + (issueK.value - 7) * step.value, width: 7 * step.value }))
const latestK = computed(() => issueK.value - issue.value.chl_age_days)
const targets = computed(() => [1, 4, 7].map((h) => {
  const date = shift(issue.value.date, h)
  return { h, date, k: dayIndex[date], value: issue.value.targets[h] }
}))
const xLabels = computed(() => series
  .map((s, k) => ({ k, date: s.date }))
  .filter(({ date }) => date.endsWith('-01') || date.endsWith('-15')))

const hoverK = ref(null)
function onMove(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  const px = ((event.clientX - rect.left) / rect.width) * W.value
  const k = Math.floor((px - M.left) / step.value)
  hoverK.value = k >= 0 && k < series.length ? k : null
}

function move(delta) {
  index.value = Math.min(issues.length - 1, Math.max(0, index.value + delta))
}
</script>

<template>
  <div ref="root">
    <div class="flex flex-wrap items-center gap-3">
      <button type="button" class="button-light !min-h-9 !px-3 !py-1.5" aria-label="Previous issue day" @click="move(-1)">←</button>
      <input v-model.number="index" type="range" min="0" :max="issues.length - 1" class="flex-1 min-w-[10rem] accent-teal-700"
             aria-label="Issue day" />
      <button type="button" class="button-light !min-h-9 !px-3 !py-1.5" aria-label="Next issue day" @click="move(1)">→</button>
      <div class="w-full sm:w-auto text-sm">
        <span class="label-caps mr-2">Issue day</span>
        <span class="font-semibold text-ink-950">{{ longLabel(issue.date) }}, 20:30 UTC</span>
      </div>
    </div>

    <div class="relative mt-4">
      <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img"
           :aria-label="`Observed chlorophyll at one pixel, with the forecast issued on ${issue.date}`"
           @mousemove="onMove" @mouseleave="hoverK = null">
        <!-- Past 7 days used for the weekly mean -->
        <rect :x="windowRect.x" :y="M.top" :width="windowRect.width" :height="plotH" fill="#0d9488" fill-opacity="0.08" />
        <text :x="windowRect.x + windowRect.width / 2" :y="M.top - 8" text-anchor="middle" class="fill-teal-800 text-[10px] font-semibold">past 7 days</text>

        <template v-for="t in yTicks" :key="t">
          <line :x1="M.left" :x2="W - M.right" :y1="y(t)" :y2="y(t)" :stroke="t === 0 ? 'var(--baseline)' : 'var(--gridline)'" />
          <text :x="M.left - 6" :y="y(t)" dy="0.32em" text-anchor="end" class="fill-[var(--ink-muted)] font-mono text-[10px]">{{ t.toFixed(2) }}</text>
        </template>
        <text v-for="l in xLabels" :key="l.k" :x="x(l.k)" :y="H - 8" text-anchor="middle" class="fill-[var(--ink-muted)] font-mono text-[10px]">{{ label(l.date) }}</text>

        <!-- Issue moment -->
        <line :x1="x(issueK) + step * 0.35" :x2="x(issueK) + step * 0.35" :y1="M.top" :y2="M.top + plotH" stroke="#07171e" stroke-width="2" stroke-dasharray="4 3" />

        <!-- Days without an observation: a small tick on the baseline -->
        <template v-for="(s, k) in series" :key="s.date">
          <line v-if="s.chl === null" :x1="x(k)" :x2="x(k)" :y1="M.top + plotH" :y2="M.top + plotH - 5" stroke="#b9b7af" stroke-width="2" />
        </template>

        <!-- Observations: past ones in teal, future ones paler -->
        <template v-for="(s, k) in series" :key="`o-${s.date}`">
          <circle v-if="s.chl !== null" :cx="x(k)" :cy="y(s.chl)" r="4"
                  :fill="k < issueK ? '#0d9488' : '#9fd8cf'" stroke="#fff" stroke-width="1.5" />
        </template>

        <!-- The latest observation the forecast receives -->
        <circle :cx="x(latestK)" :cy="y(issue.chl_latest)" r="8" fill="none" stroke="#0d9488" stroke-width="2" />

        <!-- Targets -->
        <g v-for="t in targets" :key="t.h">
          <template v-if="t.k !== undefined">
            <circle v-if="t.value !== null" :cx="x(t.k)" :cy="y(t.value)" r="8" fill="none" stroke="#07171e" stroke-width="2" />
            <rect v-else :x="x(t.k) - 6" :y="M.top + plotH - 18" width="12" height="12" rx="2" fill="none"
                  stroke="#07171e" stroke-width="1.5" stroke-dasharray="2 2" />
            <text :x="x(t.k)" :y="t.value !== null ? y(t.value) - 13 : M.top + plotH - 23" text-anchor="middle"
                  class="fill-ink-950 text-[10px] font-semibold">+{{ t.h }}</text>
          </template>
        </g>

        <line v-if="hoverK !== null" :x1="x(hoverK)" :x2="x(hoverK)" :y1="M.top" :y2="M.top + plotH" stroke="var(--ink-muted)" stroke-dasharray="2 3" />
      </svg>

      <div v-if="hoverK !== null" class="tooltip" style="top: 0.5rem"
           :style="{ left: `${(100 * x(hoverK)) / W}%`, transform: x(hoverK) > W * 0.6 ? 'translateX(calc(-100% - 10px))' : 'translateX(10px)' }">
        <div class="font-semibold text-ink-950">{{ longLabel(series[hoverK].date) }}</div>
        <div class="text-slate-600">{{ series[hoverK].chl === null ? 'Not observed (cloud)' : mg(series[hoverK].chl) }}</div>
      </div>
    </div>

    <div class="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-[11px] text-slate-600">
      <span class="flex items-center gap-1.5"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#0d9488]"></span>Observed, before the issue day</span>
      <span class="flex items-center gap-1.5"><span class="inline-block w-2.5 h-2.5 rounded-full bg-[#9fd8cf]"></span>Observed, after (unknown to the forecast)</span>
      <span class="flex items-center gap-1.5"><span class="inline-block w-0.5 h-2.5 bg-[#b9b7af]"></span>Not observed</span>
      <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-full border-2 border-[#0d9488]"></span>Latest observation</span>
      <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-full border-2 border-[#07171e]"></span>Target</span>
    </div>

    <div class="mt-5 grid gap-4 md:grid-cols-2">
      <div class="rounded-xl border border-slate-200 p-4">
        <div class="label-caps">What the forecast is given</div>
        <dl class="mt-3 space-y-2 text-sm">
          <div class="flex justify-between gap-4">
            <dt class="text-slate-600">Latest observation</dt>
            <dd class="text-right"><span class="font-semibold text-ink-950 tabular-nums">{{ mg(issue.chl_latest) }}</span>
              <span class="block text-[11px] text-slate-500">from {{ label(shift(issue.date, -issue.chl_age_days)) }} · {{ issue.chl_age_days }} day{{ issue.chl_age_days > 1 ? 's' : '' }} old</span></dd>
          </div>
          <div class="flex justify-between gap-4">
            <dt class="text-slate-600">Mean of the past 7 days</dt>
            <dd class="text-right"><span class="font-semibold text-ink-950 tabular-nums">{{ issue.chl_mean_7d === null ? '—' : mg(issue.chl_mean_7d) }}</span>
              <span class="block text-[11px] text-slate-500">from {{ issue.chl_observations_7d }} of 7 days</span></dd>
          </div>
          <div class="flex justify-between gap-4">
            <dt class="text-slate-600">Usual value this month</dt>
            <dd class="font-semibold text-ink-950 tabular-nums">{{ mg(issue.clim) }}</dd>
          </div>
          <div class="flex justify-between gap-4">
            <dt class="text-slate-600">Sea temperature last night</dt>
            <dd class="font-semibold text-ink-950 tabular-nums">{{ issue.sst_c === null ? 'not observed' : `${issue.sst_c.toFixed(1)} °C` }}</dd>
          </div>
          <div class="flex justify-between gap-4 text-[11px] text-slate-500">
            <dt>Also: day of the year, and the pixel’s location</dt>
          </div>
        </dl>
      </div>
      <div class="rounded-xl border border-slate-200 p-4">
        <div class="label-caps">What it is scored against</div>
        <dl class="mt-3 space-y-2 text-sm">
          <div v-for="t in targets" :key="t.h" class="flex justify-between gap-4">
            <dt class="text-slate-600">+{{ t.h }} day{{ t.h > 1 ? 's' : '' }} · {{ label(t.date) }}</dt>
            <dd class="text-right">
              <span v-if="t.value !== null" class="font-semibold text-ink-950 tabular-nums">{{ mg(t.value) }}</span>
              <span v-else class="text-slate-500">not observed — not scored</span>
            </dd>
          </div>
        </dl>
        <p class="mt-3 text-[11px] leading-relaxed text-slate-500">
          A forecast is still made for every horizon. It is only scored when the satellite later observes the pixel.
        </p>
      </div>
    </div>
  </div>
</template>
