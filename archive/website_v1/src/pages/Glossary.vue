<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { glossary, byCategory, categoryLabels } from '../data/glossary.js'
import SectionHeader from '../components/SectionHeader.vue'

const route = useRoute()
const grouped = byCategory()
const catOrder = ['ocean', 'data', 'ml', 'stats']
const alphabetical = computed(() => [...glossary].sort((a, b) => a.term.localeCompare(b.term)))

function scrollToHash() {
  if (!route.hash) return
  document.getElementById(route.hash.slice(1))?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(() => setTimeout(scrollToHash, 100))
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Reference"
      title="Glossary"
      lead="The terms needed to audit the observation contract, forecast design, and evaluation results. Definitions use the project’s current numbers and limitations."
    />

    <nav class="card mb-10" aria-label="Glossary index">
      <div class="label-caps mb-3">All terms A–Z</div>
      <div class="flex flex-wrap gap-2 text-sm">
        <a v-for="g in alphabetical" :key="g.slug" :href="`#${g.slug}`"
          class="px-3 py-1.5 rounded-full bg-slate-100 hover:bg-teal-50 hover:text-teal-800 text-slate-700 transition-colors">
          {{ g.term }}
        </a>
      </div>
    </nav>

    <section v-for="cat in catOrder" :key="cat" class="mb-12">
      <div class="label-caps">{{ categoryLabels[cat] }}</div>
      <div class="mt-4 space-y-4">
        <article v-for="g in grouped[cat]" :key="g.slug" :id="g.slug"
          class="card scroll-mt-24" :class="route.hash === `#${g.slug}` ? 'ring-2 ring-teal-400' : ''">
          <div class="flex flex-wrap items-baseline justify-between gap-2">
            <h2 class="text-xl font-semibold text-ink-950">{{ g.term }}</h2>
            <div v-if="g.aliases?.length" class="text-xs text-slate-500">
              Also: <span class="font-mono">{{ g.aliases.join(', ') }}</span>
            </div>
          </div>
          <p class="mt-3 leading-relaxed text-slate-700">{{ g.long }}</p>
          <div v-if="g.seeAlso?.length" class="mt-4 text-sm">
            <span class="text-slate-500">See also:</span>
            <a v-for="s in g.seeAlso" :key="s" :href="`#${s}`" class="ml-2 text-teal-800 hover:underline">{{ s }}</a>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

