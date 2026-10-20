<script setup>
import { ref } from 'vue'
import { steps, stepPath } from '../data/steps.js'

const open = ref(false)
</script>

<template>
  <header class="sticky top-0 z-40 backdrop-blur bg-[#f6f8f7]/95 border-b border-slate-200/90">
    <div class="container-page flex items-center justify-between h-16 gap-4">
      <router-link to="/" class="flex items-center gap-3 text-ink-950 shrink-0 whitespace-nowrap">
        <span class="relative w-8 h-8 rounded-full border border-teal-700 grid place-items-center shrink-0" aria-hidden="true">
          <span class="w-2.5 h-2.5 rounded-full bg-lime-400"></span>
        </span>
        <span>
          <span class="block text-sm font-semibold leading-none">Observed Ocean</span>
          <span class="hidden sm:block mt-1 font-mono text-[9px] uppercase tracking-[0.12em] text-slate-500">Chlorophyll forecasting · v2</span>
        </span>
      </router-link>

      <nav class="hidden md:flex items-center gap-1 text-[13px]" aria-label="Steps">
        <router-link
          to="/"
          class="px-2.5 py-2 text-slate-600 rounded-md hover:text-teal-800 hover:bg-white"
          exact-active-class="text-teal-800 bg-white font-semibold"
        >
          Overview
        </router-link>
        <span class="mx-1 h-5 w-px bg-slate-300" aria-hidden="true"></span>
        <template v-for="n in steps" :key="n.slug">
          <router-link
            v-if="n.ready"
            :to="stepPath(n)"
            :title="`Step ${n.number} · ${n.title}`"
            class="px-2 py-2 font-mono text-slate-600 rounded-md hover:text-teal-800 hover:bg-white"
            active-class="text-teal-800 bg-white font-semibold"
          >
            {{ n.number }}
          </router-link>
          <span
            v-else
            :title="`${n.title} — coming soon`"
            class="px-2 py-2 font-mono text-slate-300 cursor-default"
          >
            {{ n.number }}
          </span>
        </template>
      </nav>

      <button class="md:hidden text-slate-600 p-2 shrink-0" :aria-expanded="open" aria-label="Menu" @click="open = !open">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <template v-if="!open">
            <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
          </template>
          <template v-else>
            <line x1="6" y1="6" x2="18" y2="18" /><line x1="6" y1="18" x2="18" y2="6" />
          </template>
        </svg>
      </button>
    </div>

    <div v-if="open" class="md:hidden border-t border-slate-200 bg-white">
      <nav class="container-page py-3 flex flex-col text-sm" aria-label="Steps">
        <router-link to="/" class="px-2 py-2 rounded-md text-slate-700" @click="open = false">Overview</router-link>
        <template v-for="n in steps" :key="n.slug">
          <router-link
            v-if="n.ready"
            :to="stepPath(n)"
            class="px-2 py-2 rounded-md text-slate-700"
            active-class="text-teal-800 bg-teal-50 font-semibold"
            @click="open = false"
          >
            <span class="font-mono text-teal-700">{{ n.number }}</span> {{ n.title }}
          </router-link>
          <span v-else class="px-2 py-2 text-slate-400">
            <span class="font-mono">{{ n.number }}</span> {{ n.title }} · coming soon
          </span>
        </template>
      </nav>
    </div>
  </header>
</template>
