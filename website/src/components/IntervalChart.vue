<script setup>
import { computed } from 'vue'

// Estimates with 95% intervals against a zero line. An interval that stays
// right of zero is a gain we can be confident about. Each group has its own
// scale, so small differences stay readable next to large ones.
const props = defineProps({
  groups: { type: Array, required: true }, // [{ title, rows: [{ label, value, low, high }] }]
  unit: { type: String, default: '%' },
})

function niceStep(span) {
  for (const s of [1, 2, 5, 10, 20]) if (span / s <= 6) return s
  return 50
}

const scaled = computed(() => props.groups.map((g) => {
  const lows = g.rows.map((r) => r.low)
  const highs = g.rows.map((r) => r.high)
  const step = niceStep(Math.max(...highs) - Math.min(0, ...lows))
  const lo = Math.min(-step, Math.floor(Math.min(0, ...lows) / step) * step)
  const hi = Math.ceil(Math.max(...highs) / step) * step
  const ticks = []
  for (let v = lo; v <= hi + 1e-9; v += step) ticks.push(+v.toFixed(6))
  return { ...g, lo, hi, ticks, pos: (v) => `${(100 * (v - lo)) / (hi - lo)}%` }
}))

const fmt = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}`
const tone = (r) => (r.low > 0 ? 'bg-[#0d9488]' : 'bg-[#9e9b93]')
</script>

<template>
  <div class="space-y-7">
    <div v-for="g in scaled" :key="g.title">
      <div class="text-sm font-semibold text-ink-950 mb-2">{{ g.title }}</div>
      <div class="grid grid-cols-[3.5rem_1fr_6.5rem] sm:grid-cols-[5rem_1fr_9rem] gap-x-3 items-center">
        <template v-for="r in g.rows" :key="r.label">
          <span class="text-xs text-slate-600 py-2">{{ r.label }}</span>
          <span class="relative h-6">
            <span class="absolute inset-y-0 w-px bg-slate-400" :style="{ left: g.pos(0) }"></span>
            <span class="absolute top-1/2 h-[2px] -translate-y-1/2" :class="tone(r)"
                  :style="{ left: g.pos(r.low), width: `calc(${g.pos(r.high)} - ${g.pos(r.low)})` }"></span>
            <span class="absolute top-1/2 h-3 w-[2px] -translate-y-1/2" :class="tone(r)" :style="{ left: g.pos(r.low) }"></span>
            <span class="absolute top-1/2 h-3 w-[2px] -translate-y-1/2" :class="tone(r)" :style="{ left: g.pos(r.high) }"></span>
            <span class="absolute top-1/2 w-3 h-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white"
                  :class="tone(r)" :style="{ left: g.pos(r.value) }"></span>
          </span>
          <span class="text-xs tabular-nums">
            <span class="font-semibold" :class="r.low > 0 ? 'text-ink-950' : 'text-slate-500'">{{ fmt(r.value) }}{{ unit }}</span>
            <span class="block sm:inline text-slate-500 text-[10px] sm:text-xs"> ({{ fmt(r.low) }} to {{ fmt(r.high) }})</span>
          </span>
        </template>
        <span></span>
        <span class="relative h-4 font-mono text-[10px] text-slate-500">
          <!-- On small screens only the ends and zero are labelled. -->
          <span v-for="(t, k) in g.ticks" :key="t" class="absolute -translate-x-1/2"
                :class="t === 0 || k === 0 || k === g.ticks.length - 1 ? '' : 'hidden sm:inline'"
                :style="{ left: g.pos(t) }">{{ t > 0 ? '+' : '' }}{{ t }}%</span>
        </span>
        <span></span>
      </div>
    </div>
  </div>
</template>
