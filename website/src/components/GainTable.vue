<script setup>
import { computed } from 'vue'

// A table of percentage gains, one column per forecast horizon, each cell
// with a small bar from zero: right and teal when positive, left and grey
// when negative.
const props = defineProps({
  rows: { type: Array, required: true },        // [{ label, note?, values: { 1: x, 4: y, 7: z }, emphasis? }]
  horizons: { type: Array, default: () => [1, 4, 7] },
  unit: { type: String, default: '%' },
  caption: { type: String, default: '' },
})

const maxAbs = computed(() =>
  Math.max(1, ...props.rows.flatMap((r) => props.horizons.map((h) => Math.abs(r.values[h] ?? 0)))),
)
const fmt = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}${props.unit}`
</script>

<template>
  <div class="overflow-x-auto">
    <table class="data-table">
      <thead>
        <tr>
          <th></th>
          <th v-for="h in horizons" :key="h" class="!text-center">+{{ h }} day{{ h > 1 ? 's' : '' }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r.label" :class="r.emphasis ? 'bg-teal-50/60' : ''">
          <td class="min-w-[11rem]">
            <span class="font-semibold text-ink-950">{{ r.label }}</span>
            <span v-if="r.note" class="block text-[11px] text-slate-500">{{ r.note }}</span>
          </td>
          <td v-for="h in horizons" :key="h" class="min-w-[7.5rem]">
            <div v-if="r.values[h] !== undefined && r.values[h] !== null" class="grid grid-cols-2 items-center gap-0">
              <span class="h-2.5 flex justify-end">
                <span v-if="r.values[h] < 0" class="h-full rounded-l bg-[#9e9b93]"
                      :style="{ width: `${(100 * -r.values[h]) / maxAbs}%` }"></span>
              </span>
              <span class="h-2.5 flex border-l border-slate-300">
                <span v-if="r.values[h] > 0" class="h-full rounded-r bg-[#0d9488]"
                      :style="{ width: `${(100 * r.values[h]) / maxAbs}%` }"></span>
              </span>
              <span class="col-span-2 mt-1 text-center tabular-nums text-xs"
                    :class="r.values[h] > 0 ? 'text-ink-950 font-semibold' : 'text-slate-500'">{{ fmt(r.values[h]) }}</span>
            </div>
            <div v-else class="text-center text-slate-400">—</div>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="caption" class="mt-2 text-xs text-slate-500">{{ caption }}</p>
  </div>
</template>
