<script setup>
import { ref, computed } from 'vue'
import { findTerm } from '../data/glossary.js'

// Usage: <Term slug="l3">L3</Term>
//   slug — glossary slug OR alias/term (findTerm handles both)
//   default slot — display text (falls back to term)
const props = defineProps({
  slug: { type: String, required: true },
})

const entry = computed(() => findTerm(props.slug))
const open = ref(false)

function toggle(e) {
  // On touch devices, tapping toggles instead of hovering
  open.value = !open.value
  e.stopPropagation()
}

// Close on any outside click
if (typeof window !== 'undefined') {
  window.addEventListener('click', () => { open.value = false })
}
</script>

<template>
  <span v-if="entry" class="term inline-block relative" @mouseenter="open = true" @mouseleave="open = false" @click="toggle">
    <span class="border-b-2 border-dotted border-ocean-400 cursor-help hover:text-ocean-700 transition-colors">
      <slot>{{ entry.term }}</slot>
    </span>
    <!-- popover -->
    <span
      v-show="open"
      class="term-popover absolute z-30 top-full left-1/2 -translate-x-1/2 mt-1 w-72 md:w-80 p-3 rounded-lg bg-slate-900 text-white text-sm shadow-xl leading-relaxed"
      @click.stop
    >
      <span class="block font-semibold text-ocean-200 mb-1">{{ entry.term }}</span>
      <span class="block text-slate-100">{{ entry.short }}</span>
      <router-link
        :to="`/glossary#${entry.slug}`"
        class="block mt-2 text-xs text-ocean-300 hover:text-ocean-200 underline"
      >Full definition →</router-link>
    </span>
  </span>
  <span v-else><slot>{{ slug }}</slot></span>
</template>

<style scoped>
.term-popover::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-bottom-color: #0f172a; /* slate-900 */
}
</style>
