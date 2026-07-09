<script setup>
import { HORIZONS } from '../data/results.js'
const props = defineProps({ modelValue: { type: Number, default: 1 } })
const emit  = defineEmits(['update:modelValue'])

function onInput(e) {
  emit('update:modelValue', Number(e.target.value))
}
</script>

<template>
  <div class="flex items-center gap-4">
    <label class="text-sm font-semibold text-slate-700 shrink-0">Horizon</label>
    <input
      type="range"
      :min="HORIZONS[0]" :max="HORIZONS[HORIZONS.length - 1]"
      step="1" :value="modelValue" @input="onInput"
      class="flex-1 accent-ocean-600"
    />
    <span class="badge badge-info tabular-nums shrink-0">H+{{ modelValue }}</span>
  </div>
</template>
