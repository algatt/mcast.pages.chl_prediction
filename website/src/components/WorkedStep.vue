<script setup>
defineProps({
  n:     { type: [Number, String], required: true },
  title: { type: String, required: true },
})
</script>

<template>
  <li class="flex gap-4">
    <div class="shrink-0 w-8 h-8 rounded-full bg-ocean-100 text-ocean-700 font-bold flex items-center justify-center text-sm">
      {{ n }}
    </div>
    <div class="flex-1">
      <div class="font-semibold text-slate-900 mb-1">{{ title }}</div>
      <div class="text-slate-700 leading-relaxed text-sm"><slot /></div>
    </div>
  </li>
</template>
