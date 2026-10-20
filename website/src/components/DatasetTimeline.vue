<script setup>
import { ref } from 'vue'

// Which years each downloaded dataset covers, and how the experiment uses them.
const FIRST = 2008
const LAST = 2025
const years = Array.from({ length: LAST - FIRST + 1 }, (_, i) => FIRST + i)

const datasets = [
  { name: 'Chlorophyll L3', role: 'Target and main input', start: 2008, end: 2025, detail: 'Daily, 1 km, gaps kept · 353 MB' },
  { name: 'Sea temperature', role: 'Input', start: 2008, end: 2025, detail: 'Daily, ~5 km, night-time · 9 MB' },
  { name: 'Wind (ASCAT)', role: 'Tested, not in final model', start: 2019, end: 2025, detail: 'Two satellite passes a day, ~12 km · 11 MB · archive starts 2019' },
  { name: 'Chlorophyll L4', role: 'Comparison only', start: 2022, end: 2025, detail: 'Daily, 1 km, gap-filled · 78 MB' },
]

const uses = [
  { label: 'Downloaded, not used by the final model', start: 2008, end: 2016, tone: 'unused' },
  { label: 'Training', start: 2017, end: 2023, tone: 'train' },
  { label: 'Validation', start: 2024, end: 2024, tone: 'validate' },
  { label: 'Test', start: 2025, end: 2025, tone: 'test' },
]

function span(start, end) {
  return {
    left: `${(100 * (start - FIRST)) / years.length}%`,
    width: `calc(${(100 * (end - start + 1)) / years.length}% - 2px)`,
  }
}

const period = (u) => (u.start === u.end ? `${u.start}` : `${u.start}–${u.end}`)

const hover = ref(null)
</script>

<template>
  <div class="overflow-x-auto">
    <div class="min-w-[36rem]">
      <div class="grid grid-cols-[9.5rem_1fr] gap-x-4">
        <div></div>
        <div class="relative h-5 font-mono text-[10px] text-slate-500 tabular-nums">
          <span
            v-for="y in years.filter((y) => y % 2 === 0)"
            :key="y"
            class="absolute -translate-x-1/2"
            :style="{ left: `${(100 * (y - FIRST + 0.5)) / years.length}%` }"
          >{{ y }}</span>
        </div>

        <template v-for="d in datasets" :key="d.name">
          <div class="py-2.5 pr-2">
            <div class="text-sm font-semibold text-ink-950 leading-tight">{{ d.name }}</div>
            <div class="text-[11px] text-slate-500 leading-tight">{{ d.role }}</div>
          </div>
          <div class="relative py-2.5 border-t border-[var(--gridline)]">
            <div
              class="absolute top-1/2 -translate-y-1/2 h-3 rounded bg-observed cursor-default"
              :class="{ 'opacity-60': d.role.startsWith('Tested') || d.role === 'Comparison only' }"
              :style="span(d.start, d.end)"
              @mouseenter="hover = d"
              @mouseleave="hover = null"
            ></div>
            <div
              v-if="hover === d"
              class="tooltip top-full mt-1"
              :style="{ left: span(d.start, d.end).left }"
            >
              <div class="font-semibold text-ink-950">{{ d.name }} · {{ d.start }}–{{ d.end }}</div>
              <div class="text-slate-600">{{ d.detail }}</div>
            </div>
          </div>
        </template>

        <div class="pt-4 pr-2">
          <div class="text-sm font-semibold text-ink-950 leading-tight">How the years are used</div>
          <div class="text-[11px] text-slate-500 leading-tight">Decided in step 05</div>
        </div>
        <div class="pt-4 border-t border-slate-300">
          <div class="relative h-9">
            <div
              v-for="u in uses"
              :key="u.label"
              class="use-band absolute top-0 h-9 rounded px-1.5 flex items-center text-[10px] font-semibold leading-tight overflow-hidden"
              :class="`use-band--${u.tone}`"
              :style="span(u.start, u.end)"
              :title="`${u.label}: ${period(u)}`"
            >
              <!-- One-year bands are too narrow for text; the legend below names them. -->
              <template v-if="u.end - u.start >= 2">{{ u.label }}</template>
            </div>
          </div>
          <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-slate-600">
            <span v-for="u in uses" :key="u.label" class="flex items-center gap-1.5">
              <span class="inline-block w-3 h-3 rounded-sm border border-black/5" :class="`use-band--${u.tone}`"></span>
              {{ u.label }} · {{ period(u) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.use-band--unused { background: #eeede8; color: #52514e; }
.use-band--train { background: #ccebe5; color: #0a4842; }
.use-band--validate { background: #6cc2b1; color: #07171e; }
.use-band--test { background: #0b665d; color: #ffffff; }
</style>
