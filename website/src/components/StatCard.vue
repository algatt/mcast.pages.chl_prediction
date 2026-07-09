<script setup>
defineProps({
  label:  { type: String, required: true },
  value:  { type: String, required: true },
  detail: { type: String, default: '' },
})
</script>

<template>
  <div class="rounded-xl bg-white/10 backdrop-blur border border-white/20 p-4 text-white">
    <div class="text-xs uppercase tracking-wide text-ocean-100/80 font-semibold">{{ label }}</div>
    <div class="mt-1 text-3xl font-bold tabular-nums">{{ value }}</div>
    <div v-if="detail" class="text-xs text-ocean-100/70 mt-1">{{ detail }}</div>
  </div>
</template>
