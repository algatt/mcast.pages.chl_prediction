<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { steps, stepPath } from '../data/steps.js'

// Shared frame for every step page: header, on-page contents, and links to
// the previous and next steps.
const props = defineProps({
  number: { type: String, required: true },
  sections: { type: Array, required: true }, // [{ id, label }]
})

const router = useRouter()
const index = computed(() => steps.findIndex((s) => s.number === props.number))
const step = computed(() => steps[index.value])
const previous = computed(() => steps[index.value - 1] ?? null)
const next = computed(() => steps[index.value + 1] ?? null)

function jump(id) {
  router.push({ hash: `#${id}` })
}
</script>

<template>
  <article>
    <header class="hero-shell">
      <div class="hero-grid" aria-hidden="true"></div>
      <div class="container-page relative py-12 md:py-16">
        <div class="flex flex-wrap items-center gap-2.5">
          <span class="hero-kicker">Step {{ step.number }}</span>
          <span class="hero-meta">Notebook · {{ step.notebook }}</span>
        </div>
        <h1 class="mt-5 max-w-4xl text-4xl sm:text-5xl font-semibold tracking-[-0.04em] leading-[1.05]">
          {{ step.title }}
        </h1>
        <div class="mt-4 max-w-3xl text-lg leading-relaxed text-slate-300">
          <slot name="lead" />
        </div>
      </div>
    </header>

    <div class="container-page py-10 md:py-14 grid gap-10 lg:grid-cols-[12rem_minmax(0,1fr)]">
      <nav class="hidden lg:block" aria-label="On this page">
        <div class="sticky top-24">
          <div class="label-caps">On this page</div>
          <ol class="mt-3 space-y-2 text-sm">
            <li v-for="(s, i) in sections" :key="s.id">
              <a :href="`#${stepPath(step)}#${s.id}`" class="text-slate-600 hover:text-teal-800"
                 @click.prevent="jump(s.id)">
                <span class="font-mono text-[11px] text-slate-400 mr-1">{{ i + 1 }}</span>{{ s.label }}
              </a>
            </li>
          </ol>
        </div>
      </nav>

      <div class="min-w-0 max-w-3xl">
        <slot />

        <nav class="mt-16 grid gap-4 sm:grid-cols-2" aria-label="Step navigation">
          <router-link :to="previous ? stepPath(previous) : '/'" class="card hover:border-teal-300 transition-colors">
            <div class="label-caps">Back</div>
            <div class="mt-1 font-semibold text-ink-950">
              {{ previous ? `${previous.number} · ${previous.title}` : 'Overview' }}
            </div>
          </router-link>
          <template v-if="next">
            <router-link v-if="next.ready" :to="stepPath(next)" class="card hover:border-teal-300 transition-colors">
              <div class="label-caps">Next</div>
              <div class="mt-1 font-semibold text-ink-950">{{ next.number }} · {{ next.title }}</div>
              <div class="mt-1 text-sm text-slate-600">{{ next.question }}</div>
            </router-link>
            <div v-else class="card opacity-70">
              <div class="label-caps">Next · coming soon</div>
              <div class="mt-1 font-semibold text-ink-950">{{ next.number }} · {{ next.title }}</div>
              <div class="mt-1 text-sm text-slate-600">{{ next.question }}</div>
            </div>
          </template>
        </nav>
      </div>
    </div>
  </article>
</template>
