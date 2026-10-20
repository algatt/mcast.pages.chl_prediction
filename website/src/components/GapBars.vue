<script setup>
import { ref } from 'vue'

// Gap lengths shown two ways, as two small single-series bar charts: how many
// gaps have each length, and how many missing days they account for.
defineProps({
  gaps: { type: Array, required: true }, // [{ label, events_pct, missing_days_pct }]
})

const panels = [
  { key: 'events_pct', title: 'Share of gaps', note: 'Each gap counted once' },
  { key: 'missing_days_pct', title: 'Share of missing days', note: 'Each gap weighted by its length' },
]
const hover = ref(null)
</script>

<template>
  <div class="grid gap-8 sm:grid-cols-2">
    <div v-for="panel in panels" :key="panel.key">
      <div class="text-sm font-semibold text-ink-950">{{ panel.title }}</div>
      <div class="text-[11px] text-slate-500 mb-3">{{ panel.note }}</div>
      <ul class="space-y-2">
        <li v-for="g in gaps" :key="g.label" class="grid grid-cols-[5.5rem_1fr_3rem] items-center gap-2 text-xs"
            @mouseenter="hover = g.label" @mouseleave="hover = null">
          <span :class="hover === g.label ? 'text-ink-950 font-semibold' : 'text-slate-600'">{{ g.label }}</span>
          <span class="relative h-3">
            <span class="absolute inset-y-0 left-0 rounded-r bg-[#256abf]"
                  :style="{ width: `${Math.max((g[panel.key] / 50) * 100, 0.8)}%`, opacity: hover && hover !== g.label ? 0.5 : 1 }"></span>
          </span>
          <span class="text-right tabular-nums text-slate-700">{{ g[panel.key] < 0.5 ? '<0.5' : g[panel.key].toFixed(0) }}%</span>
        </li>
      </ul>
    </div>
  </div>
</template>
