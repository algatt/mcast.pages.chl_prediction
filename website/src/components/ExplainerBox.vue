<script setup>
import { ref } from 'vue'

const props = defineProps({
  title:  { type: String, default: 'What does this mean?' },
  tone:   { type: String, default: 'info' }, // 'info' | 'primer' | 'warn'
  open:   { type: Boolean, default: false },
})

const isOpen = ref(props.open)
const toneClasses = {
  info:   { box: 'bg-ocean-50 border-ocean-200',   icon: '💡', head: 'text-ocean-800' },
  primer: { box: 'bg-emerald-50 border-emerald-200', icon: '📖', head: 'text-emerald-800' },
  warn:   { box: 'bg-amber-50 border-amber-200',   icon: '⚠️', head: 'text-amber-800' },
}
</script>

<template>
  <div
    :class="['rounded-xl border p-4 my-4 transition-colors', toneClasses[tone].box]"
  >
    <button
      @click="isOpen = !isOpen"
      class="w-full flex items-center justify-between text-left"
      :aria-expanded="isOpen"
    >
      <span class="flex items-center gap-2 font-semibold" :class="toneClasses[tone].head">
        <span class="text-xl">{{ toneClasses[tone].icon }}</span>
        <span>{{ title }}</span>
      </span>
      <svg
        :class="['w-5 h-5 transition-transform', isOpen ? 'rotate-180' : '']"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
      </svg>
    </button>

    <div v-if="isOpen" class="mt-3 prose prose-slate prose-sm max-w-none">
      <slot />
    </div>
  </div>
</template>
