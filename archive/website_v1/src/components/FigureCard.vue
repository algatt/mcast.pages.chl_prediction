<script setup>
defineProps({
  src: { type: String, required: true },
  title: { type: String, required: true },
  caption: { type: String, default: '' },
  note: { type: String, default: '' },
})
</script>

<template>
  <figure class="card overflow-hidden p-4 md:p-5">
    <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <img :src="`figs/${src}`" :alt="title" class="w-full h-auto" loading="lazy" />
    </div>
    <figcaption class="mt-4">
      <div class="label-caps">Notebook output</div>
      <div class="mt-1 text-sm font-semibold text-slate-900">{{ title }}</div>
      <p v-if="caption" class="mt-1.5 text-sm leading-relaxed text-slate-600">{{ caption }}</p>
      <p v-if="note" class="mt-2 text-xs text-amber-800">{{ note }}</p>
    </figcaption>
  </figure>
</template>

