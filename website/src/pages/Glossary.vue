<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { glossary, byCategory, categoryLabels } from '../data/glossary.js'
import SectionHeader from '../components/SectionHeader.vue'

const route = useRoute()
const grouped = byCategory()
const catOrder = ['ocean', 'region', 'data', 'ml', 'stats']

// Alphabetical index of all terms
const alphabetical = computed(() =>
  [...glossary].sort((a, b) => a.term.localeCompare(b.term))
)

// Scroll to hash on load / hash change
function scrollToHash() {
  if (route.hash) {
    const el = document.getElementById(route.hash.slice(1))
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
onMounted(() => setTimeout(scrollToHash, 100))
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Reference"
      title="Glossary"
      lead="Every technical term used across the site, grouped by category and cross-referenced. Anywhere on the site, dotted underlines mark terms — hover to see the short definition, or come here for the full version."
    />

    <!-- Quick alphabetical index -->
    <div class="card mb-8">
      <div class="text-xs uppercase tracking-wide font-semibold text-slate-500 mb-3">All terms A → Z</div>
      <div class="flex flex-wrap gap-2 text-sm">
        <a v-for="g in alphabetical" :key="g.slug"
           :href="`#${g.slug}`"
           class="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-ocean-100 hover:text-ocean-800 text-slate-700 transition-colors">
          {{ g.term }}
        </a>
      </div>
    </div>

    <!-- Entries by category -->
    <div v-for="cat in catOrder" :key="cat" class="mb-10">
      <h2 class="text-2xl font-bold text-slate-900 mb-4">{{ categoryLabels[cat] }}</h2>
      <div class="space-y-4">
        <article
          v-for="g in grouped[cat]" :key="g.slug"
          :id="g.slug"
          class="card scroll-mt-20"
          :class="route.hash === `#${g.slug}` ? 'ring-2 ring-ocean-400' : ''"
        >
          <div class="flex flex-wrap items-baseline justify-between gap-2 mb-2">
            <h3 class="text-xl font-bold text-slate-900">{{ g.term }}</h3>
            <div v-if="g.aliases && g.aliases.length" class="text-xs text-slate-500">
              also: <span class="font-mono">{{ g.aliases.join(', ') }}</span>
            </div>
          </div>
          <p class="text-slate-700 leading-relaxed mb-3">{{ g.long }}</p>
          <div v-if="g.example" class="rounded-lg bg-slate-50 border border-slate-200 p-3 text-sm text-slate-700 leading-relaxed">
            <span class="font-semibold text-slate-500 uppercase tracking-wide text-xs">Example</span>
            <div class="mt-1">{{ g.example }}</div>
          </div>
          <div v-if="g.seeAlso && g.seeAlso.length" class="mt-3 text-sm">
            <span class="text-slate-500">See also:</span>
            <a v-for="s in g.seeAlso" :key="s" :href="`#${s}`"
               class="ml-2 text-ocean-700 hover:underline">
              {{ s }}
            </a>
          </div>
        </article>
      </div>
    </div>
  </div>
</template>
