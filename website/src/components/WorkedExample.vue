<script setup>
defineProps({
  title:  { type: String, default: 'Worked example' },
  intro:  { type: String, default: '' },
})
</script>

<template>
  <div class="rounded-2xl overflow-hidden border border-slate-200 bg-white shadow-sm my-6">
    <div class="bg-gradient-to-r from-slate-900 to-slate-700 text-white px-5 py-3 flex items-center gap-2">
      <span class="text-lg">🧪</span>
      <span class="font-semibold">{{ title }}</span>
    </div>
    <div class="p-5">
      <p v-if="intro" class="text-slate-700 mb-4 leading-relaxed">{{ intro }}</p>
      <ol class="space-y-4">
        <slot />
      </ol>
    </div>
  </div>
</template>
