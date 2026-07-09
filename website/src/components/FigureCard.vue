<script setup>
defineProps({
  src:     { type: String, required: true },
  title:   { type: String, required: true },
  caption: { type: String, default: '' },
})
</script>

<template>
  <figure class="card overflow-hidden">
    <img :src="`figs/${src}`" :alt="title" class="w-full h-auto rounded-lg" loading="lazy" />
    <figcaption class="mt-3">
      <div class="text-sm font-semibold text-slate-900">{{ title }}</div>
      <p v-if="caption" class="text-sm text-slate-600 mt-1 leading-relaxed">{{ caption }}</p>
    </figcaption>
  </figure>
</template>
