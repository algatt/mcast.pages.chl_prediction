<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  detail: { type: String, default: '' },
})
</script>

<template>
  <div class="rounded-xl border border-slate-200 bg-white p-4">
    <div class="label-caps">{{ label }}</div>
    <div class="mt-2 text-3xl font-semibold tracking-[-0.03em] text-ink-950">{{ value }}</div>
    <div v-if="detail" class="mt-1 text-xs leading-relaxed text-slate-500">{{ detail }}</div>
  </div>
</template>
