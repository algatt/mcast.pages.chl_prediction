<script setup>
import { ref } from 'vue'
const open = ref(false)

const primary = [
  { to: '/',            label: 'Overview' },
  { to: '/primer',      label: 'Primer' },
  { to: '/methodology', label: 'Pipeline' },
  { to: '/data',        label: 'Data & evidence' },
  { to: '/forecast',    label: 'Visual diagnostics' },
]
const findings = [
  { to: '/findings/observation-contract', label: 'Observation contract' },
  { to: '/findings/group-ablation',  label: 'Feature evidence' },
  { to: '/findings/walk-forward',    label: 'Temporal robustness' },
  { to: '/findings/bloom-detection', label: 'Bloom events' },
]
const secondary = [
  { to: '/glossary',    label: 'Glossary' },
  { to: '/about',       label: 'About' },
]
</script>

<template>
  <header class="sticky top-0 z-40 backdrop-blur bg-[#f6f8f7]/95 border-b border-slate-200/90">
    <div class="container-page flex items-center justify-between h-16 gap-4">
      <!-- Brand -->
      <router-link to="/" class="flex items-center gap-3 text-ink-950 shrink-0 whitespace-nowrap">
        <span class="relative w-8 h-8 rounded-full border border-teal-700 grid place-items-center shrink-0" aria-hidden="true">
          <span class="w-2.5 h-2.5 rounded-full bg-lime-400"></span>
        </span>
        <span>
          <span class="block text-sm font-semibold leading-none">Observed Ocean</span>
          <span class="hidden sm:block mt-1 font-mono text-[9px] uppercase tracking-[0.12em] text-slate-500">Chlorophyll forecasting</span>
        </span>
      </router-link>

      <!-- Desktop nav -->
      <nav class="hidden xl:flex items-center gap-1 text-[13px]">
        <router-link
          v-for="n in primary" :key="n.to" :to="n.to"
          class="px-2.5 py-2 whitespace-nowrap text-slate-600 rounded-md hover:text-teal-800 hover:bg-white transition-colors"
          active-class="text-teal-800 bg-white font-semibold"
        >
          {{ n.label }}
        </router-link>

        <!-- Findings dropdown -->
        <div class="relative group">
          <button class="px-2.5 py-2 whitespace-nowrap text-slate-600 rounded-md hover:text-teal-800 hover:bg-white transition-colors inline-flex items-center gap-1">
            Findings & limits
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <div class="absolute right-0 top-full mt-1 w-52 rounded-lg border border-slate-200 bg-white shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity">
            <router-link
              v-for="f in findings" :key="f.to" :to="f.to"
              class="block px-3 py-2.5 text-slate-700 hover:bg-teal-50 hover:text-teal-800 first:rounded-t-lg last:rounded-b-lg"
              active-class="text-teal-800 bg-teal-50 font-semibold"
            >
              {{ f.label }}
            </router-link>
          </div>
        </div>

        <router-link
          v-for="n in secondary" :key="n.to" :to="n.to"
          class="px-2.5 py-2 whitespace-nowrap text-slate-600 rounded-md hover:text-teal-800 hover:bg-white transition-colors"
          active-class="text-teal-800 bg-white font-semibold"
        >
          {{ n.label }}
        </router-link>
      </nav>

      <!-- Mobile / medium toggle -->
      <button class="xl:hidden text-slate-600 p-2 shrink-0" @click="open = !open" aria-label="menu">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="6"  x2="21" y2="6"  v-if="!open"/>
          <line x1="3" y1="12" x2="21" y2="12" v-if="!open"/>
          <line x1="3" y1="18" x2="21" y2="18" v-if="!open"/>
          <line x1="6" y1="6"  x2="18" y2="18" v-if="open"/>
          <line x1="6" y1="18" x2="18" y2="6"  v-if="open"/>
        </svg>
      </button>
    </div>

    <!-- Mobile drawer -->
    <div v-if="open" class="xl:hidden border-t border-slate-200 bg-white">
      <nav class="container-page py-3 flex flex-col text-sm">
        <router-link
          v-for="n in primary" :key="n.to" :to="n.to" @click="open = false"
          class="px-2 py-2 text-slate-700 rounded-md hover:bg-ocean-50"
          active-class="text-ocean-700 bg-ocean-50 font-semibold"
        >
          {{ n.label }}
        </router-link>
        <div class="px-2 pt-3 pb-1 text-[10px] uppercase tracking-widest font-semibold text-slate-400">Findings</div>
        <router-link
          v-for="f in findings" :key="f.to" :to="f.to" @click="open = false"
          class="px-4 py-2 text-slate-700 rounded-md hover:bg-ocean-50"
          active-class="text-ocean-700 bg-ocean-50 font-semibold"
        >
          {{ f.label }}
        </router-link>
        <div class="pt-2 mt-2 border-t border-slate-100"></div>
        <router-link
          v-for="n in secondary" :key="n.to" :to="n.to" @click="open = false"
          class="px-2 py-2 text-slate-700 rounded-md hover:bg-ocean-50"
          active-class="text-ocean-700 bg-ocean-50 font-semibold"
        >
          {{ n.label }}
        </router-link>
      </nav>
    </div>
  </header>
</template>
