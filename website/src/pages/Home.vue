<script setup>
import { steps, stepPath } from '../data/steps.js'

const rules = [
  {
    title: 'Only real observations',
    text: 'Satellites cannot see through cloud, so the chlorophyll record has holes. We keep the holes rather than fill them with estimates, and we only ever score forecasts against days the satellite actually saw.',
  },
  {
    title: 'Only what a forecaster would know',
    text: 'Satellite data arrives with a delay. Every forecast uses only the data that would already have been published at 20:30 UTC on the day it is issued.',
  },
  {
    title: 'Beat the simple rules, or say so',
    text: '“Tomorrow will look like today” is hard to beat. The model is always compared with simple rules like this, and the gap is reported with its uncertainty.',
  },
]
</script>

<template>
  <div>
    <section class="hero-shell">
      <div class="hero-grid" aria-hidden="true"></div>
      <div class="container-page relative py-14 md:py-20">
        <div class="flex flex-wrap items-center gap-2.5">
          <span class="hero-kicker">Experiment v2</span>
          <span class="hero-meta">Malta–Sicily Channel · satellite data 2008–2025</span>
        </div>
        <h1 class="mt-6 max-w-4xl text-[2.4rem] sm:text-5xl lg:text-[3.9rem] leading-[1.02] font-semibold tracking-[-0.045em]">
          Forecasting chlorophyll around Malta, <span class="text-cyan-200">one step at a time.</span>
        </h1>
        <p class="mt-6 max-w-3xl text-lg leading-relaxed text-slate-300">
          Chlorophyll is the green pigment of phytoplankton, the microscopic algae at the base of the marine
          food web. Satellites measure it every day. This experiment asks how well we can forecast it
          1, 4 and 7 days ahead — and this site walks through how the answer was reached, step by
          step, including the parts that did not work.
        </p>
        <div class="mt-8 flex flex-wrap gap-3">
          <router-link :to="stepPath(steps[0])" class="button-primary">
            Start with step 01 <span aria-hidden="true">→</span>
          </router-link>
          <a href="#steps" class="button-ghost" @click.prevent="$router.push({ hash: '#steps' })">See all steps</a>
        </div>
      </div>
    </section>

    <section class="container-page py-14 md:py-20">
      <div class="label-caps">Ground rules</div>
      <h2 class="mt-3 text-3xl font-semibold tracking-[-0.03em] text-ink-950 max-w-2xl">
        Three rules that shape every step
      </h2>
      <div class="mt-8 grid gap-5 md:grid-cols-3">
        <div v-for="(r, i) in rules" :key="r.title" class="card">
          <div class="section-number">0{{ i + 1 }}</div>
          <h3 class="mt-2 text-lg font-semibold text-ink-950">{{ r.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ r.text }}</p>
        </div>
      </div>
    </section>

    <section id="steps" class="border-y border-slate-200 bg-white">
      <div class="container-page py-14 md:py-20">
        <div class="label-caps">The steps</div>
        <h2 class="mt-3 text-3xl font-semibold tracking-[-0.03em] text-ink-950">Eight steps, each answering one question</h2>
        <p class="mt-3 max-w-2xl text-slate-600">
          Each page explains what one step did, why, and what it found. Every step is one Jupyter notebook in the experiment. Live scores will be added to steps 07–08 once enough live data has been collected.
        </p>

        <ol class="mt-8 divide-y divide-slate-200 border-y border-slate-200">
          <li v-for="n in steps" :key="n.slug">
            <component
              :is="n.ready ? 'router-link' : 'div'"
              :to="n.ready ? stepPath(n) : undefined"
              class="grid grid-cols-[3rem_1fr_auto] gap-4 items-baseline py-5"
              :class="n.ready ? 'group hover:bg-slate-50 -mx-3 px-3 rounded-lg' : ''"
            >
              <span class="font-mono text-sm" :class="n.ready ? 'text-teal-700' : 'text-slate-400'">{{ n.number }}</span>
              <span>
                <span class="block font-semibold" :class="n.ready ? 'text-ink-950 group-hover:text-teal-800' : 'text-slate-500'">{{ n.title }}</span>
                <span class="block mt-1 text-sm" :class="n.ready ? 'text-slate-600' : 'text-slate-400'">{{ n.question }}</span>
              </span>
              <span v-if="n.ready" class="text-sm font-semibold text-teal-800">Read <span aria-hidden="true">→</span></span>
              <span v-else class="font-mono text-[10px] uppercase tracking-[0.12em] text-slate-400">Coming soon</span>
            </component>
          </li>
        </ol>
      </div>
    </section>

    <section class="container-page py-14 md:py-20">
      <div class="grid gap-8 lg:grid-cols-[1fr_1.1fr] items-start">
        <div>
          <div class="label-caps">Where the story ends up</div>
          <h2 class="mt-3 text-3xl font-semibold tracking-[-0.03em] text-ink-950">A short preview of the results</h2>
          <p class="mt-3 text-slate-600 leading-relaxed">
            The details belong to steps 05–07, but a reader may want to know the destination first.
            All figures are for 2025, a year the model never saw while it was being built.
          </p>
        </div>
        <ul class="space-y-4">
          <li class="card">
            <div class="font-semibold text-ink-950">Clearly better than “no change”</div>
            <p class="mt-1 text-sm text-slate-600 leading-relaxed">
              Forecast errors are 13–17% smaller than simply repeating the latest observation, at every lead time.
            </p>
          </li>
          <li class="card">
            <div class="font-semibold text-ink-950">Only a little better than a smarter simple rule</div>
            <p class="mt-1 text-sm text-slate-600 leading-relaxed">
              Against a rule that blends the latest observation with the usual value for the time of year, the
              model gains about 5% at 1 day and 3% at 4 days. At 7 days the difference is within the uncertainty.
            </p>
          </li>
          <li class="card">
            <div class="font-semibold text-ink-950">Blooms are still missed</div>
            <p class="mt-1 text-sm text-slate-600 leading-relaxed">
              On days when chlorophyll is well above normal, every method — the model included — underestimates it by around 40–50%.
            </p>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>
