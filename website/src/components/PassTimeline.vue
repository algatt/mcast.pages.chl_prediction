<script setup>
import { ref } from 'vue'

// When in the UTC day the two wind passes over the study area happen.
const props = defineProps({
  passes: { type: Object, required: true }, // { descending: [min, median, max], ascending: [...] } in hours
  issueHour: { type: Number, default: 20.5 },
})

const rows = [
  { key: 'descending', label: 'Morning pass', detail: 'satellite heading south' },
  { key: 'ascending', label: 'Evening pass', detail: 'satellite heading north' },
]

const pct = (h) => `${(100 * h) / 24}%`
const clock = (h) => {
  const minutes = Math.round(h * 60)
  return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`
}
const hover = ref(null)
</script>

<template>
  <div>
    <div class="grid grid-cols-[5.5rem_1fr] sm:grid-cols-[8.5rem_1fr] gap-x-3 sm:gap-x-4">
      <div></div>
      <div class="relative h-5 font-mono text-[10px] text-slate-500 tabular-nums">
        <span v-for="h in [0, 6, 12, 18, 24]" :key="h" class="absolute"
              :class="h === 0 ? '' : h === 24 ? '-translate-x-full' : '-translate-x-1/2'"
              :style="{ left: pct(h) }">{{ String(h).padStart(2, '0') }}<span class="hidden sm:inline">:00</span></span>
      </div>

      <template v-for="r in rows" :key="r.key">
        <div class="py-3">
          <div class="text-sm font-semibold text-ink-950 leading-tight">{{ r.label }}</div>
          <div class="text-[11px] text-slate-500 leading-tight">{{ r.detail }}</div>
        </div>
        <div class="relative border-t border-[var(--gridline)]">
          <!-- Hour gridlines -->
          <span v-for="h in [6, 12, 18]" :key="h" class="absolute inset-y-0 w-px bg-[var(--gridline)]"
                :style="{ left: pct(h) }"></span>
          <!-- Forecast issue time -->
          <span class="absolute inset-y-0 border-l-2 border-dashed border-ink-900/70" :style="{ left: pct(issueHour) }"></span>
          <span
            class="absolute top-1/2 -translate-y-1/2 h-4 rounded bg-[#5f51c9]"
            :style="{ left: pct(passes[r.key][0]), width: pct(passes[r.key][2] - passes[r.key][0]) }"
            @mouseenter="hover = r.key"
            @mouseleave="hover = null"
          ></span>
          <div v-if="hover === r.key" class="tooltip top-full -mt-1"
               :style="{ left: pct(passes[r.key][0]), transform: r.key === 'ascending' ? 'translateX(-60%)' : 'none' }">
            <div class="font-semibold text-ink-950">{{ r.label }}</div>
            <div class="text-slate-600 tabular-nums">
              {{ clock(passes[r.key][0]) }}–{{ clock(passes[r.key][2]) }} UTC · typically {{ clock(passes[r.key][1]) }}
            </div>
          </div>
        </div>
      </template>

      <div></div>
      <div class="relative h-6 text-[11px] text-ink-900">
        <span class="absolute top-1 -translate-x-1/2 whitespace-nowrap font-semibold" :style="{ left: pct(issueHour) }">
          Forecast issued {{ clock(issueHour) }}
        </span>
      </div>
    </div>
  </div>
</template>
