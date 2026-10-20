<script setup>
import { ref } from 'vue'

// What a forecaster has in hand at 20:30 UTC on issue day D, day by day.
const days = ['D−2', 'D−1', 'D', 'D+1', 'D+2', 'D+3', 'D+4', 'D+5', 'D+6', 'D+7']
const ISSUE = 2

// Cell states: known, pending (measured but not yet published), target, empty.
const rows = [
  {
    name: 'Chlorophyll',
    cells: ['known', 'known', 'pending'],
    notes: [
      'Published the day after, by 20:00 UTC',
      'Arrived at 20:00 UTC today — the newest chlorophyll available',
      'Today’s satellite passes are not published until 20:00 UTC tomorrow',
    ],
  },
  {
    name: 'Sea temperature',
    cells: ['known', 'known', 'known'],
    notes: [
      'Night-time measurement, published the same day',
      'Night-time measurement, published the same day',
      'Last night’s measurement, published at 12:00 UTC today',
    ],
  },
  {
    name: 'Wind',
    cells: ['known', 'known', 'pending'],
    notes: [
      'Published the next morning',
      'Both of yesterday’s passes, published at about 07:00 UTC today',
      'Today’s passes are not published until about 07:00 UTC tomorrow',
    ],
  },
  {
    name: 'Forecast targets',
    cells: ['', '', '', 'target', '', '', 'target', '', '', 'target'],
    notes: ['', '', '', '+1 day', '', '', '+4 days', '', '', '+7 days'],
  },
]

const hover = ref(null)
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-600 mb-4">
      <span class="flex items-center gap-2"><span class="cell-swatch cell--known"></span>Available to the forecast</span>
      <span class="flex items-center gap-2"><span class="cell-swatch cell--pending"></span>Measured, but not yet published</span>
      <span class="flex items-center gap-2"><span class="cell-swatch cell--target"></span>Forecast for this day</span>
    </div>

    <div class="diagram">
      <div class="relative grid grid-cols-[var(--label)_repeat(10,minmax(0,1fr))] gap-[3px] text-[11px]">
        <span></span>
        <span v-for="(d, k) in days" :key="d" class="text-center font-mono pb-1"
              :class="k === ISSUE ? 'text-ink-950 font-semibold' : 'text-slate-500'">{{ d }}</span>

        <template v-for="row in rows" :key="row.name">
          <span class="self-center pr-2 font-semibold text-ink-950 leading-tight text-[10px] sm:text-[11px]">{{ row.name }}</span>
          <span
            v-for="(d, k) in days"
            :key="d"
            class="h-9 rounded grid place-items-center"
            :class="row.cells[k] ? `cell--${row.cells[k]}` : 'cell--empty'"
            @mouseenter="hover = row.notes[k] ? { row: row.name, day: d, note: row.notes[k] } : null"
            @mouseleave="hover = null"
          >
            <span v-if="row.cells[k] === 'known'" aria-hidden="true">✓</span>
            <span v-else-if="row.cells[k] === 'target'" class="font-mono font-semibold">
              <span class="sm:hidden">{{ row.notes[k].split(' ')[0] }}</span><span class="hidden sm:inline">{{ row.notes[k] }}</span>
            </span>
          </span>
        </template>

        <!-- Issue time: 20:30 UTC sits near the end of day D. -->
        <span class="issue-line" :style="{ left: `calc(var(--label) + (100% - var(--label)) * ${(ISSUE + 20.5 / 24) / 10})` }"></span>
      </div>
      <div class="relative h-6 text-[11px] font-semibold text-ink-900">
        <span class="absolute top-1 whitespace-nowrap"
              :style="{ left: `calc(var(--label) + (100% - var(--label)) * ${(ISSUE + 20.5 / 24) / 10} - 0.5rem)` }">
          <span class="sm:hidden">Issued 20:30 UTC</span><span class="hidden sm:inline">Forecast issued, 20:30 UTC on day D</span>
        </span>
      </div>
    </div>

    <p class="mt-2 min-h-[1.25rem] text-xs text-slate-600">
      <template v-if="hover"><strong class="text-ink-950">{{ hover.row }}, {{ hover.day }}:</strong> {{ hover.note }}</template>
      <template v-else>Hover over a cell for details.</template>
    </p>
  </div>
</template>

<style scoped>
.diagram { --label: 5.5rem; }
@media (min-width: 640px) { .diagram { --label: 7.5rem; } }
.cell--known { background: #0d9488; color: #fff; }
.cell--pending { background: repeating-linear-gradient(135deg, var(--gap-hatch) 0 1px, var(--gap) 1px 5px); }
.cell--target { background: #fff; box-shadow: inset 0 0 0 2px #07171e; color: #07171e; }
.cell--empty { background: #f3f3f0; }
.cell-swatch { @apply inline-block w-4 h-4 rounded-sm shrink-0; }
.issue-line {
  position: absolute;
  top: 1.25rem;
  bottom: 0;
  width: 0;
  border-left: 2px dashed rgba(7, 23, 30, 0.75);
  pointer-events: none;
}
</style>
