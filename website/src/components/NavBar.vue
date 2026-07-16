<script setup>
import { ref } from 'vue'
const open = ref(false)

// Two-tier nav so 10 items don't try to sit on one row.
// Primary = the reading path. Secondary = reference/meta.
const primary = [
  { to: '/',            label: 'Home' },
  { to: '/primer',      label: 'Primer' },
  { to: '/methodology', label: 'Methodology' },
  { to: '/data',        label: 'Data' },
  { to: '/forecast',    label: 'Forecast' },
]
const findings = [
  { to: '/findings/l3-vs-l4',        label: 'L3 vs L4',       short: 'L3/L4' },
  { to: '/findings/group-ablation',  label: 'Ablation',       short: 'Ablate' },
  { to: '/findings/walk-forward',    label: 'Walk-Forward',   short: 'WF' },
  { to: '/findings/bloom-detection', label: 'Blooms',         short: 'Blooms' },
]
const secondary = [
  { to: '/glossary',    label: 'Glossary' },
  { to: '/about',       label: 'About' },
]
</script>

<template>
  <header class="sticky top-0 z-40 backdrop-blur bg-white/90 border-b border-slate-200">
    <div class="container-page flex items-center justify-between h-14 gap-4">
      <!-- Brand -->
      <router-link to="/" class="flex items-center gap-2 font-semibold text-ocean-900 shrink-0 whitespace-nowrap">
        <span class="w-7 h-7 rounded-md bg-grad-hero flex items-center justify-center text-white text-sm shrink-0">🌊</span>
        <span class="hidden sm:inline text-sm md:text-[15px]">Chl-a Forecasting</span>
        <span class="hidden 2xl:inline text-slate-300 font-normal">·</span>
        <span class="hidden 2xl:inline text-slate-500 font-normal text-xs">Malta–Sicily Channel</span>
      </router-link>

      <!-- Desktop nav -->
      <nav class="hidden xl:flex items-center gap-1 text-sm">
        <router-link
          v-for="n in primary" :key="n.to" :to="n.to"
          class="px-2.5 py-1.5 whitespace-nowrap text-slate-600 rounded-md hover:text-ocean-700 hover:bg-ocean-50 transition-colors"
          active-class="text-ocean-700 bg-ocean-50 font-semibold"
        >
          {{ n.label }}
        </router-link>

        <!-- Findings dropdown -->
        <div class="relative group">
          <button class="px-2.5 py-1.5 whitespace-nowrap text-slate-600 rounded-md hover:text-ocean-700 hover:bg-ocean-50 transition-colors inline-flex items-center gap-1">
            Findings
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>
          <div class="absolute right-0 top-full mt-1 w-52 rounded-lg border border-slate-200 bg-white shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity">
            <router-link
              v-for="f in findings" :key="f.to" :to="f.to"
              class="block px-3 py-2 text-slate-700 hover:bg-ocean-50 hover:text-ocean-700 first:rounded-t-lg last:rounded-b-lg"
              active-class="text-ocean-700 bg-ocean-50 font-semibold"
            >
              {{ f.label }}
            </router-link>
          </div>
        </div>

        <router-link
          v-for="n in secondary" :key="n.to" :to="n.to"
          class="px-2.5 py-1.5 whitespace-nowrap text-slate-600 rounded-md hover:text-ocean-700 hover:bg-ocean-50 transition-colors"
          active-class="text-ocean-700 bg-ocean-50 font-semibold"
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
