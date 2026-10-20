<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title:   { type: String, required: true },
  lead:    { type: String, default: '' },
})
</script>

<template>
  <div class="mb-10 md:mb-12 max-w-4xl">
    <div v-if="eyebrow" class="label-caps text-teal-700 mb-3">
      {{ eyebrow }}
    </div>
    <h1 class="text-4xl md:text-5xl font-semibold tracking-[-0.045em] text-ink-950 leading-[1.06]">{{ title }}</h1>
    <p v-if="lead" class="mt-5 text-lg text-slate-600 max-w-3xl leading-relaxed">{{ lead }}</p>
  </div>
</template>
