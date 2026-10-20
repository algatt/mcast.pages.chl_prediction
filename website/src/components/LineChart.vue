<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

// A small line chart with optional range bands, direct end labels and a
// crosshair read-out. One y axis only.
//   series: [{ name, color, points: [{ x, y, lo?, hi? }] }]
const props = defineProps({
  series: { type: Array, required: true },
  xDomain: { type: Array, required: true },
  yDomain: { type: Array, required: true },
  xTicks: { type: Array, required: true },      // [{ value, label }]
  yTicks: { type: Array, required: true },      // [value]
  yFormat: { type: Function, default: (v) => `${v}` },
  xFormat: { type: Function, default: (v) => `${v}` },
  valueFormat: { type: Function, default: null }, // tooltip values; defaults to yFormat
  yTitle: { type: String, default: '' },
  xTitle: { type: String, default: '' },
  height: { type: Number, default: 260 },
  // Drawing width before the container is measured; afterwards the chart is
  // drawn at its displayed width, so text keeps the same size on any screen.
  width: { type: Number, default: 640 },
  showLegend: { type: Boolean, default: true },
  showEndLabels: { type: Boolean, default: true },
  ariaLabel: { type: String, required: true },
})

const root = ref(null)
const W = ref(props.width)
let observer = null
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    W.value = Math.max(280, Math.round(entry.contentRect.width))
  })
  observer.observe(root.value)
})
onBeforeUnmount(() => observer?.disconnect())

const M = computed(() => ({ top: 14, right: props.showEndLabels ? 92 : 14, bottom: props.xTitle ? 42 : 26, left: 46 }))
const plotW = computed(() => W.value - M.value.left - M.value.right)
const plotH = computed(() => props.height - M.value.top - M.value.bottom)

const x = (v) => M.value.left + ((v - props.xDomain[0]) / (props.xDomain[1] - props.xDomain[0])) * plotW.value
const y = (v) => M.value.top + plotH.value * (1 - (v - props.yDomain[0]) / (props.yDomain[1] - props.yDomain[0]))

const linePath = (pts) => pts.map((p, i) => `${i ? 'L' : 'M'}${x(p.x).toFixed(1)},${y(p.y).toFixed(1)}`).join(' ')
const bandPath = (pts) => {
  const withBand = pts.filter((p) => p.lo !== undefined && p.hi !== undefined)
  if (!withBand.length) return ''
  const top = withBand.map((p, i) => `${i ? 'L' : 'M'}${x(p.x).toFixed(1)},${y(p.hi).toFixed(1)}`).join(' ')
  const bottom = [...withBand].reverse().map((p) => `L${x(p.x).toFixed(1)},${y(p.lo).toFixed(1)}`).join(' ')
  return `${top} ${bottom} Z`
}

// End labels, nudged apart so they never overlap.
const endLabels = computed(() => {
  const labels = props.series.map((s) => {
    const last = s.points[s.points.length - 1]
    return { name: s.name, color: s.color, x: x(last.x) + 8, y: y(last.y) }
  }).sort((a, b) => a.y - b.y)
  for (let i = 1; i < labels.length; i++) {
    if (labels[i].y - labels[i - 1].y < 13) labels[i].y = labels[i - 1].y + 13
  }
  return labels
})

// Thin the x labels when there is too little room for all of them.
const visibleXTicks = computed(() => {
  const room = plotW.value / props.xTicks.length
  const every = room < 34 ? Math.ceil(34 / room) : 1
  return props.xTicks.filter((_, i) => i % every === 0)
})

const xs = computed(() => [...new Set(props.series.flatMap((s) => s.points.map((p) => p.x)))].sort((a, b) => a - b))
const hover = ref(null)
const svg = ref(null)

function onMove(event) {
  const rect = svg.value.getBoundingClientRect()
  const px = ((event.clientX - rect.left) / rect.width) * W.value
  let best = null
  for (const v of xs.value) {
    if (best === null || Math.abs(x(v) - px) < Math.abs(x(best) - px)) best = v
  }
  hover.value = best
}

const hoverRows = computed(() => {
  if (hover.value === null) return []
  const fmt = props.valueFormat || props.yFormat
  return props.series
    .map((s) => ({ s, p: s.points.find((p) => p.x === hover.value) }))
    .filter((r) => r.p)
    .map(({ s, p }) => ({ name: s.name, color: s.color, value: fmt(p.y), y: p.y,
                          range: p.lo !== undefined ? `${fmt(p.lo)}–${fmt(p.hi)}` : null }))
    .sort((a, b) => b.y - a.y)
})
</script>

<template>
  <div ref="root" class="relative">
    <div v-if="showLegend && series.length > 1" class="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-600 mb-2">
      <span v-for="s in series" :key="s.name" class="flex items-center gap-2">
        <span class="inline-block w-4 h-[3px] rounded" :style="{ background: s.color }"></span>{{ s.name }}
      </span>
    </div>
    <div v-if="yTitle" class="text-[11px] text-slate-500 mb-1">{{ yTitle }}</div>

    <svg ref="svg" :viewBox="`0 0 ${W} ${height}`" class="w-full h-auto overflow-visible" role="img" :aria-label="ariaLabel"
         @mousemove="onMove" @mouseleave="hover = null">
      <g>
        <template v-for="t in yTicks" :key="t">
          <line :x1="M.left" :x2="W - M.right" :y1="y(t)" :y2="y(t)"
                :stroke="t === yDomain[0] ? 'var(--baseline)' : 'var(--gridline)'" stroke-width="1" />
          <text :x="M.left - 6" :y="y(t)" dy="0.32em" text-anchor="end"
                class="fill-[var(--ink-muted)] font-mono text-[10px] tabular-nums">{{ yFormat(t) }}</text>
        </template>
        <text v-for="t in visibleXTicks" :key="t.value" :x="x(t.value)" :y="M.top + plotH + 16" text-anchor="middle"
              class="fill-[var(--ink-muted)] font-mono text-[10px] tabular-nums">{{ t.label }}</text>
        <text v-if="xTitle" :x="M.left + plotW / 2" :y="height - 6" text-anchor="middle"
              class="fill-[var(--ink-secondary)] text-[11px]">{{ xTitle }}</text>
      </g>

      <path v-for="s in series" :key="`band-${s.name}`" :d="bandPath(s.points)" :fill="s.color" fill-opacity="0.14" />

      <g v-for="s in series" :key="s.name">
        <path :d="linePath(s.points)" fill="none" :stroke="s.color" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
      </g>

      <g v-if="hover !== null">
        <line :x1="x(hover)" :x2="x(hover)" :y1="M.top" :y2="M.top + plotH" stroke="var(--ink-muted)" stroke-width="1" stroke-dasharray="3 3" />
        <template v-for="s in series" :key="`pt-${s.name}`">
          <circle v-for="p in s.points.filter((q) => q.x === hover)" :key="p.x"
                  :cx="x(p.x)" :cy="y(p.y)" r="4" :fill="s.color" stroke="#fff" stroke-width="2" />
        </template>
      </g>

      <g v-if="showEndLabels">
        <text v-for="l in endLabels" :key="`lbl-${l.name}`" :x="l.x" :y="l.y" dy="0.32em"
              class="fill-[var(--ink-secondary)] text-[11px] font-semibold">{{ l.name }}</text>
      </g>

      <rect :x="M.left" :y="M.top" :width="plotW" :height="plotH" fill="transparent" />
    </svg>

    <div v-if="hover !== null && hoverRows.length" class="tooltip"
         :style="{ left: `${(100 * x(hover)) / W}%`, top: '2.5rem',
                   transform: x(hover) > W * 0.55 ? 'translateX(calc(-100% - 12px))' : 'translateX(12px)' }">
      <div class="font-semibold text-ink-950 mb-1">{{ xFormat(hover) }}</div>
      <div v-for="r in hoverRows" :key="r.name" class="flex items-center gap-2 tabular-nums">
        <span class="inline-block w-2.5 h-2.5 rounded-full" :style="{ background: r.color }"></span>
        <span class="text-slate-600">{{ r.name }}</span>
        <span class="ml-auto pl-3 font-semibold text-ink-950">{{ r.value }}</span>
        <span v-if="r.range" class="text-slate-500">({{ r.range }})</span>
      </div>
    </div>
  </div>
</template>
