<script setup>
// How the damped-persistence rule mixes the latest observation with the
// monthly normal, per horizon (weights on the log scale).
defineProps({
  coefficients: { type: Object, required: true }, // { "1": [a, b, c], ... }
})

const LATEST = '#0d9488'
const NORMAL = '#2a78d6'
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-600 mb-3">
      <span class="flex items-center gap-2"><span class="inline-block w-3 h-3 rounded-sm" :style="{ background: LATEST }"></span>Weight on the latest observation</span>
      <span class="flex items-center gap-2"><span class="inline-block w-3 h-3 rounded-sm" :style="{ background: NORMAL }"></span>Weight on the usual value for the month</span>
    </div>
    <div class="space-y-3">
      <div v-for="(c, h) in coefficients" :key="h" class="grid grid-cols-[4rem_1fr] items-center gap-3">
        <span class="text-sm font-semibold text-ink-950">+{{ h }} day{{ h > 1 ? 's' : '' }}</span>
        <div>
          <div class="flex gap-[2px] h-7">
            <div class="rounded-l flex items-center px-2 text-[11px] font-semibold text-white"
                 :style="{ width: `${(100 * c[1]) / (c[1] + c[2])}%`, background: LATEST }">{{ Math.round(100 * c[1] / (c[1] + c[2])) }}%</div>
            <div class="rounded-r flex items-center justify-end px-2 text-[11px] font-semibold text-white"
                 :style="{ width: `${(100 * c[2]) / (c[1] + c[2])}%`, background: NORMAL }">{{ Math.round(100 * c[2] / (c[1] + c[2])) }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
