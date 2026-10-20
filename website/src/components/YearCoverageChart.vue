<script setup>
import { computed, ref } from 'vue'

// Share of sea pixel-days with a valid L3 chlorophyll value, per year.
const props = defineProps({
  coverage: { type: Object, required: true }, // { "2008": 41.2, ... }
  highlightFrom: { type: Number, default: 2017 },
})

const bars = computed(() =>
  Object.entries(props.coverage).map(([year, pct]) => ({ year: Number(year), pct })),
)

const W = 640
const H = 240
const M = { top: 16, right: 8, bottom: 26, left: 34 }
const plotW = W - M.left - M.right
const plotH = H - M.top - M.bottom
const Y_MAX = 70
const yTicks = [0, 20, 40, 60]

const step = computed(() => plotW / bars.value.length)
const barW = computed(() => Math.max(4, step.value - 4))
const x = (i) => M.left + i * step.value + (step.value - barW.value) / 2
const y = (pct) => M.top + plotH * (1 - pct / Y_MAX)

// Top-rounded bar anchored to the baseline.
function barPath(i, pct) {
  const x0 = x(i)
  const x1 = x0 + barW.value
  const y0 = y(pct)
  const yb = M.top + plotH
  const r = Math.min(4, barW.value / 2, yb - y0)
  return `M${x0},${yb} V${y0 + r} Q${x0},${y0} ${x0 + r},${y0} H${x1 - r} Q${x1},${y0} ${x1},${y0 + r} V${yb} Z`
}

const hover = ref(null)

const earlyMean = computed(() => mean(bars.value.filter((b) => b.year < props.highlightFrom)))
const lateMean = computed(() => mean(bars.value.filter((b) => b.year >= props.highlightFrom)))
function mean(list) {
  return list.reduce((s, b) => s + b.pct, 0) / list.length
}
</script>

<template>
  <div class="relative">
    <div class="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-600 mb-2">
      <span class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-sm bg-[#b9b7af]"></span>
        2008–{{ highlightFrom - 1 }} · average {{ earlyMean.toFixed(0) }}%
      </span>
      <span class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-sm bg-observed"></span>
        {{ highlightFrom }}–2025 · average {{ lateMean.toFixed(0) }}%
      </span>
    </div>

    <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img"
         aria-label="Bar chart of the share of the sea with a valid chlorophyll observation, per year from 2008 to 2025">
      <g>
        <template v-for="t in yTicks" :key="t">
          <line :x1="M.left" :x2="W - M.right" :y1="y(t)" :y2="y(t)"
                :stroke="t === 0 ? 'var(--baseline)' : 'var(--gridline)'" stroke-width="1" />
          <text :x="M.left - 6" :y="y(t)" dy="0.32em" text-anchor="end"
                class="fill-[var(--ink-muted)] font-mono text-[10px] tabular-nums">{{ t }}%</text>
        </template>
      </g>

      <g>
        <g v-for="(b, i) in bars" :key="b.year">
          <path :d="barPath(i, b.pct)" :fill="b.year >= highlightFrom ? '#0d9488' : '#b9b7af'"
                :opacity="hover && hover.year !== b.year ? 0.55 : 1" />
          <!-- Hit target taller and wider than the bar. -->
          <rect :x="M.left + i * step" :y="M.top" :width="step" :height="plotH" fill="transparent"
                @mouseenter="hover = { ...b, i }" @mouseleave="hover = null" />
          <text v-if="b.year % 2 === 0 || b.year === 2025" :x="x(i) + barW / 2" :y="H - 8" text-anchor="middle"
                class="fill-[var(--ink-muted)] font-mono text-[10px] tabular-nums">{{ b.year }}</text>
        </g>
      </g>
    </svg>

    <div v-if="hover" class="tooltip"
         :style="{ left: `${(100 * (x(hover.i) + barW / 2)) / W}%`, top: `${(100 * y(hover.pct)) / H}%`,
                   transform: 'translate(-50%, calc(-100% - 8px))' }">
      <div class="font-semibold text-ink-950">{{ hover.year }}</div>
      <div class="text-slate-600 tabular-nums">{{ hover.pct.toFixed(1) }}% of sea pixel-days observed</div>
    </div>
  </div>
</template>
