<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title:   { type: String, required: true },
  lead:    { type: String, default: '' },
})
</script>

<template>
  <div class="mb-8">
    <div v-if="eyebrow" class="text-xs uppercase tracking-widest font-semibold text-ocean-600 mb-2">
      {{ eyebrow }}
    </div>
    <h1 class="text-3xl md:text-4xl font-bold text-slate-900 leading-tight">{{ title }}</h1>
    <p v-if="lead" class="mt-3 text-lg text-slate-600 max-w-3xl leading-relaxed">{{ lead }}</p>
  </div>
</template>
