<script setup>
import { ref } from 'vue'

// Share of wind measurements carrying each quality flag, marking which flags
// cause a measurement to be removed. One measurement can carry several flags,
// so the bars do not add up to 100%.
defineProps({
  flags: { type: Array, required: true }, // [{ label, pct, rejected }]
})

const KEPT = '#0d9488'
const REMOVED = '#52514e'
const hover = ref(null)
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-600 mb-4">
      <span class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-sm" :style="{ background: REMOVED }"></span>
        Flag removes the measurement
      </span>
      <span class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-sm" :style="{ background: KEPT }"></span>
        Flag noted, measurement kept
      </span>
    </div>

    <ul class="space-y-2.5">
      <li
        v-for="f in flags"
        :key="f.label"
        class="grid grid-cols-[1fr_3.5rem] sm:grid-cols-[13rem_1fr_3.5rem] items-center gap-x-3 gap-y-1 text-sm"
        @mouseenter="hover = f"
        @mouseleave="hover = null"
      >
        <span class="leading-tight" :class="hover === f ? 'text-ink-950 font-semibold' : 'text-slate-700'">
          {{ f.label }}
          <span class="block font-mono text-[10px] uppercase tracking-[0.1em]"
                :class="f.rejected ? 'text-slate-600' : 'text-teal-700'">
            {{ f.rejected ? 'removed' : 'kept' }}
          </span>
        </span>
        <!-- On small screens the bar moves to its own full-width row under the label. -->
        <span class="text-right tabular-nums text-slate-700 sm:order-last">{{ f.pct < 0.1 ? '<0.1' : f.pct.toFixed(1) }}%</span>
        <span class="relative h-3 col-span-2 sm:col-span-1">
          <span class="absolute inset-y-0 left-0 rounded-r"
                :style="{ width: `${Math.max(f.pct, 0.4)}%`, background: f.rejected ? REMOVED : KEPT,
                          opacity: hover && hover !== f ? 0.55 : 1 }"></span>
        </span>
      </li>
    </ul>
  </div>
</template>
