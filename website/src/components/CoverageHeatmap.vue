<script setup>
import { computed, ref } from 'vue'

// Year × month grid of average daily observation coverage, with a switch
// between sources. One sequential ramp (coverage %), light → dark.
const props = defineProps({
  sources: { type: Array, required: true }, // [{ id, label, matrix: { "2008": [12 values] } }]
})

const RAMP = ['#e6f0fc', '#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
const MONTHS = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December']

const active = ref(props.sources[0].id)
const source = computed(() => props.sources.find((s) => s.id === active.value))
const years = computed(() => Object.keys(source.value.matrix))

function color(pct) {
  const i = Math.min(RAMP.length - 1, Math.floor((pct / 100) * RAMP.length))
  return RAMP[i]
}
const inkFor = (pct) => (pct >= 50 ? '#ffffff' : '#0b0b0b')

const hover = ref(null)
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="segmented" role="group" aria-label="Data source">
        <button v-for="s in sources" :key="s.id" type="button" :aria-pressed="active === s.id" @click="active = s.id">
          {{ s.label }}
        </button>
      </div>
      <div class="flex items-center gap-2 text-[11px] text-slate-500">
        <span>0%</span>
        <span class="flex">
          <span v-for="c in RAMP" :key="c" class="w-5 h-3 first:rounded-l last:rounded-r" :style="{ background: c }"></span>
        </span>
        <span>100% of the sea observed</span>
      </div>
    </div>

    <div class="relative mt-4" role="img" :aria-label="`Average daily coverage by year and month, ${source.label}`">
      <div class="grid grid-cols-[2.6rem_repeat(12,minmax(0,1fr))] gap-[2px] text-[10px]">
        <span></span>
        <span v-for="(m, i) in MONTHS" :key="i" class="text-center font-mono text-slate-500 pb-1">{{ m }}</span>
        <template v-for="year in years" :key="year">
          <span class="font-mono text-slate-500 tabular-nums pr-1 self-center text-right">{{ year }}</span>
          <span
            v-for="(pct, i) in source.matrix[year]"
            :key="i"
            class="h-6 rounded-[3px] grid place-items-center tabular-nums font-semibold cursor-default"
            :style="{ background: color(pct), color: inkFor(pct), outline: hover && hover.year === year && hover.month === i ? '2px solid #07171e' : 'none' }"
            @mouseenter="hover = { year, month: i, pct }"
            @mouseleave="hover = null"
          >
            <span class="hidden sm:inline">{{ Math.round(pct) }}</span>
          </span>
        </template>
      </div>
      <div v-if="hover" class="tooltip -top-2 right-0 -translate-y-full">
        <div class="font-semibold text-ink-950">{{ MONTH_NAMES[hover.month] }} {{ hover.year }}</div>
        <div class="text-slate-600 tabular-nums">{{ hover.pct.toFixed(0) }}% of the sea observed on an average day</div>
      </div>
    </div>
  </div>
</template>
