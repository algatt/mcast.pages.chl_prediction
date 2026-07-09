<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import FigureCard from '../components/FigureCard.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import Term from '../components/Term.vue'
import { stages } from '../data/stages.js'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Pipeline walkthrough"
      title="Twelve stages, twelve validation gates"
      lead="Each notebook ends with a programmatic check that must pass before moving on. Gates are scientific assertions, not unit tests — a gate that fails is a finding, not an inconvenience."
    />

    <!-- Reader onboarding -->
    <ExplainerBox title="What is a 'validation gate' and why do we care?" tone="primer" :open="true">
      <p>
        A <Term slug="gate">validation gate</Term> is a small, automated check we run at the end of each
        notebook. It asks a question like <em>"did the model actually beat persistence at H+3?"</em> or
        <em>"are the target values aligned in time so we do not have leakage?"</em> — and either says
        <span class="badge badge-pass ml-1">PASS</span> or <span class="badge badge-warn ml-1">FAIL</span>.
      </p>
      <p>
        Gates are the scientific contract. If a gate fails, the pipeline stops until we understand why.
        A failed gate is not embarrassing — it is diagnostic. Every gate in this pipeline is designed to
        catch a specific kind of mistake that would otherwise pass silently and inflate our numbers.
      </p>
      <p>
        All 12 gates below passed. Some of them almost failed and taught us something (see especially
        Gate 8b and Gate 10).
      </p>
    </ExplainerBox>

    <!-- Legend -->
    <div class="flex flex-wrap gap-3 items-center mb-8 text-sm">
      <span class="badge badge-pass">PASS = gate satisfied</span>
      <span class="badge badge-info">📊 has a figure</span>
      <span class="badge badge-warn">🎯 methodological decision</span>
    </div>

    <!-- Vertical timeline of stages -->
    <ol class="relative border-l-2 border-ocean-200 space-y-8 ml-4">
      <li v-for="s in stages" :key="s.n" class="ml-8 relative">
        <!-- Node -->
        <div class="absolute -left-[46px] top-1 flex items-center justify-center w-9 h-9 rounded-full bg-white border-2 border-ocean-500 text-ocean-700 font-bold text-sm">
          {{ s.n }}
        </div>

        <article class="card card-hover">
          <!-- Header: title + goal subtitle + notebook code chip -->
          <header class="mb-5">
            <div class="flex flex-wrap items-baseline justify-between gap-2">
              <h3 class="text-xl md:text-2xl font-bold text-slate-900">
                Stage {{ s.n }} — {{ s.title }}
              </h3>
              <code class="text-xs text-slate-500 font-mono bg-slate-50 px-2 py-1 rounded border border-slate-200 whitespace-nowrap">
                {{ s.notebook }}
              </code>
            </div>
            <p class="text-slate-500 italic mt-1 text-sm md:text-base">{{ s.goal }}</p>
          </header>

          <div class="grid md:grid-cols-5 gap-6">
            <!-- Left: elaborate "What we did" prose gets the room -->
            <div class="md:col-span-3">
              <div class="text-xs uppercase tracking-widest font-semibold text-ocean-600 mb-2">What we did</div>
              <p class="text-slate-700 leading-relaxed">{{ s.what }}</p>

              <!-- Compact Gate + Result strip -->
              <div class="mt-5 rounded-xl bg-slate-50 border border-slate-200 p-4 space-y-3">
                <div class="flex items-start gap-3">
                  <span class="badge badge-info shrink-0 mt-0.5">Gate</span>
                  <p class="text-slate-700 text-sm leading-relaxed"
                     v-html="s.gate.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')"></p>
                </div>
                <div class="flex items-start gap-3 pt-3 border-t border-slate-200">
                  <span class="badge badge-pass shrink-0 mt-0.5">PASS</span>
                  <p class="text-slate-800 text-sm leading-relaxed">
                    {{ s.result.replace(/^PASS\.?\s*/, '') }}
                  </p>
                </div>
                <div v-if="s.keyMetric" class="flex items-center gap-3 pt-3 border-t border-slate-200">
                  <span class="text-xs uppercase tracking-widest font-semibold text-ocean-600 shrink-0">Key metric</span>
                  <span class="text-base font-bold text-ocean-900 tabular-nums">{{ s.keyMetric }}</span>
                </div>
              </div>
            </div>

            <!-- Right: figure or placeholder -->
            <div v-if="s.figure" class="md:col-span-2 flex items-start">
              <figure class="w-full">
                <img :src="`figs/${s.figure}`" :alt="s.title"
                     class="rounded-lg border border-slate-200 shadow-sm w-full h-auto"
                     loading="lazy" />
                <figcaption class="text-xs text-slate-500 mt-2 text-center">
                  From {{ s.notebook }}
                </figcaption>
              </figure>
            </div>
            <div v-else class="md:col-span-2 hidden md:flex items-center justify-center text-slate-300 text-sm italic bg-slate-50 rounded-lg border border-dashed border-slate-200 min-h-[150px]">
              (no figure — text-only stage)
            </div>
          </div>
        </article>
      </li>
    </ol>

    <!-- Bottom navigation -->
    <div class="mt-12 flex flex-wrap gap-3 justify-center">
      <router-link to="/findings/l3-vs-l4"
        class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
        Read Finding 01 — L3 vs L4 →
      </router-link>
      <router-link to="/data"
        class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
        See the data sources
      </router-link>
    </div>
  </div>
</template>
