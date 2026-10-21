<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// Reliability diagram: forecast probability (x) against how often the event
// then happened (y), one line per series. On the diagonal, a forecast of 20%
// came true 20% of the time. Both axes use a square-root scale so the many
// small probabilities stay readable next to the few large ones.
//   series: [{ name, color, points: [{ x, y, n }] }]
const props = defineProps({
  series: { type: Array, required: true },
  max: { type: Number, default: 0.8 },
  ticks: { type: Array, default: () => [0, 0.02, 0.05, 0.1, 0.2, 0.4, 0.8] },
  height: { type: Number, default: 320 },
  ariaLabel: { type: String, required: true },
})

const root = ref(null)
const W = ref(560)
let observer = null
onMounted(() => {
  observer = new ResizeObserver(([entry]) => { W.value = Math.max(280, Math.round(entry.contentRect.width)) })
  observer.observe(root.value)
})
onBeforeUnmount(() => observer?.disconnect())

const M = { top: 12, right: 16, bottom: 40, left: 48 }
const size = computed(() => Math.min(W.value - M.left - M.right, props.height - M.top - M.bottom))
const s = (v) => Math.sqrt(Math.max(0, Math.min(v, props.max)) / props.max) * size.value
const x = (v) => M.left + s(v)
const y = (v) => M.top + size.value - s(v)
const pct = (v) => `${v < 0.1 ? (100 * v).toFixed(v < 0.01 ? 1 : 0) : Math.round(100 * v)}%`
const path = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.x).toFixed(1)},${y(p.y).toFixed(1)}`).join(' ')
const maxN = computed(() => Math.max(...props.series.flatMap((l) => l.points.map((p) => p.n))))
const radius = (n) => 2.5 + 5 * Math.sqrt(n / maxN.value)

const hover = ref(null)
</script>

<template>
  <div ref="root" class="relative">
    <div class="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-600 mb-2">
      <span v-for="l in series" :key="l.name" class="flex items-center gap-2">
        <span class="inline-block w-4 h-[3px] rounded" :style="{ background: l.color }"></span>{{ l.name }}
      </span>
      <span class="flex items-center gap-2">
        <span class="inline-block w-4 border-t border-dashed border-slate-500"></span>Perfectly reliable
      </span>
    </div>
    <svg :viewBox="`0 0 ${W} ${size + M.top + M.bottom}`" class="w-full h-auto overflow-visible" role="img" :aria-label="ariaLabel">
      <template v-for="t in ticks" :key="t">
        <line :x1="x(0)" :x2="x(max)" :y1="y(t)" :y2="y(t)" :stroke="t === 0 ? 'var(--baseline)' : 'var(--gridline)'" />
        <line :x1="x(t)" :x2="x(t)" :y1="y(0)" :y2="y(max)" stroke="var(--gridline)" />
        <text :x="x(0) - 6" :y="y(t)" dy="0.32em" text-anchor="end" class="fill-[var(--ink-muted)] font-mono text-[10px]">{{ pct(t) }}</text>
        <text :x="x(t)" :y="y(0) + 15" text-anchor="middle" class="fill-[var(--ink-muted)] font-mono text-[10px]">{{ pct(t) }}</text>
      </template>
      <text :x="x(0) + size / 2" :y="y(0) + 33" text-anchor="middle" class="fill-[var(--ink-secondary)] text-[11px]">Forecast probability</text>
      <line :x1="x(0)" :y1="y(0)" :x2="x(max)" :y2="y(max)" stroke="#64748b" stroke-dasharray="4 4" />
      <g v-for="l in series" :key="l.name">
        <path :d="path(l.points)" fill="none" :stroke="l.color" stroke-width="2" stroke-linejoin="round" />
        <circle v-for="p in l.points" :key="p.x" :cx="x(p.x)" :cy="y(p.y)" :r="radius(p.n)" :fill="l.color"
                stroke="#fff" stroke-width="1.5" @mouseenter="hover = { ...p, name: l.name, color: l.color }" @mouseleave="hover = null" />
      </g>
    </svg>
    <div class="mt-1 min-h-[1.25rem] text-xs text-slate-600 tabular-nums">
      <template v-if="hover">
        <span class="font-semibold" :style="{ color: hover.color }">{{ hover.name }}</span>:
        forecasts averaging {{ pct(hover.x) }} came true {{ pct(hover.y) }} of the time ({{ hover.n.toLocaleString('en-GB') }} forecasts)
      </template>
      <template v-else>Hover a dot for its values. Dot size shows how many forecasts it stands for.</template>
    </div>
  </div>
</template>
