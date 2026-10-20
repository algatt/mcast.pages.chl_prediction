<script setup>
import { computed, ref } from 'vue'

// Composition of every L4 value in 2022–2025: copied from an L3 observation,
// or filled in where L3 had none.
const props = defineProps({
  observed: { type: Number, required: true },
  filled: { type: Number, required: true },
})

const total = computed(() => props.observed + props.filled)
const segments = computed(() => [
  { key: 'observed', label: 'From a satellite observation', value: props.observed, color: '#0d9488' },
  { key: 'filled', label: 'Filled in where L3 had a gap', value: props.filled, color: '#eb6834' },
])

const millions = (v) => `${(v / 1e6).toFixed(1)} million`
const pct = (v) => (100 * v) / total.value

const hover = ref(null)
</script>

<template>
  <div class="relative">
    <div class="flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-600 mb-3">
      <span v-for="s in segments" :key="s.key" class="flex items-center gap-2">
        <span class="inline-block w-3 h-3 rounded-sm" :style="{ background: s.color }"></span>
        {{ s.label }}
      </span>
    </div>

    <!-- 2px surface gap between the two fills; rounded outer ends. -->
    <div class="flex gap-[2px] h-8" role="img"
         :aria-label="`${pct(observed).toFixed(0)}% of L4 values come from observations, ${pct(filled).toFixed(0)}% are filled in`">
      <div
        v-for="(s, i) in segments"
        :key="s.key"
        class="h-full"
        :class="i === 0 ? 'rounded-l' : 'rounded-r'"
        :style="{ width: `${pct(s.value)}%`, background: s.color, opacity: hover && hover !== s ? 0.6 : 1 }"
        @mouseenter="hover = s"
        @mouseleave="hover = null"
      ></div>
    </div>

    <div class="flex gap-[2px] mt-2 text-sm">
      <div v-for="s in segments" :key="s.key" :style="{ width: `${pct(s.value)}%` }">
        <div class="font-semibold text-ink-950 tabular-nums">{{ pct(s.value).toFixed(0) }}%</div>
        <div class="text-xs text-slate-500 tabular-nums">{{ millions(s.value) }} pixel-days</div>
      </div>
    </div>

    <div v-if="hover" class="tooltip -top-2 -translate-y-full"
         :style="{ left: hover.key === 'observed' ? '8%' : `${pct(observed) + 4}%` }">
      <div class="font-semibold text-ink-950">{{ hover.label }}</div>
      <div class="text-slate-600 tabular-nums">{{ hover.value.toLocaleString('en-GB') }} pixel-days · {{ pct(hover.value).toFixed(1) }}%</div>
    </div>
  </div>
</template>
