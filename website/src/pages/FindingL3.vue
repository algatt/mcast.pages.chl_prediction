<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import CoverageChart from '../components/CoverageChart.vue'
import FigureCard from '../components/FigureCard.vue'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 01 · Observation contract"
      title="The target remains observed, even when clouds hide the sea"
      lead="The pipeline keeps Level-3 chlorophyll gaps as missing values, defines coverage against an observable domain, and never creates synthetic chlorophyll targets."
    />

    <section class="grid md:grid-cols-3 gap-4 mb-10">
      <article class="card">
        <div class="label-caps">Observable domain</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-ink-950">46,158</div>
        <p class="mt-2 text-sm text-slate-600">Target-domain pixels identified from the chlorophyll product.</p>
      </article>
      <article class="card">
        <div class="label-caps">DJF coverage</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-ink-950">50.47%</div>
        <p class="mt-2 text-sm text-slate-600">Above the predeclared 25% threshold, so the daily target was retained.</p>
      </article>
      <article class="card">
        <div class="label-caps">Zero-coverage days</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-ink-950">87</div>
        <p class="mt-2 text-sm text-slate-600">A visible limitation—not a reason to fill the target artificially.</p>
      </article>
    </section>

    <section class="chart-panel mb-10">
      <div class="section-intro mb-5">
        <div>
          <div class="label-caps">Coverage decision</div>
          <h2>Monthly coverage clears the feasibility floor</h2>
        </div>
        <p>The orange bars mark winter months; the dashed line is the 25% decision threshold declared before modelling.</p>
      </div>
      <CoverageChart />
      <p class="mt-4 pt-4 border-t border-slate-200 text-xs leading-relaxed text-slate-500">
        Monthly summaries are descriptive. The formal decision used winter daily coverage: 50.47%. Across the complete period, 302 days fell below 25% coverage.
      </p>
    </section>

    <section class="grid lg:grid-cols-[1fr_.9fr] gap-6 mb-10">
      <div class="card">
        <div class="label-caps">Row-level logic</div>
        <ol class="mt-4 space-y-5">
          <li class="grid grid-cols-[2rem_1fr] gap-3">
            <span class="font-mono text-teal-700">01</span>
            <div><strong class="text-ink-950">Issue the forecast.</strong><p class="mt-1 text-sm text-slate-600">Missing issue-time CHL predictors are allowed; XGBoost routes missing values natively.</p></div>
          </li>
          <li class="grid grid-cols-[2rem_1fr] gap-3">
            <span class="font-mono text-teal-700">02</span>
            <div><strong class="text-ink-950">Keep the target untouched.</strong><p class="mt-1 text-sm text-slate-600">Cloud-obscured future chlorophyll is not interpolated or scored.</p></div>
          </li>
          <li class="grid grid-cols-[2rem_1fr] gap-3">
            <span class="font-mono text-teal-700">03</span>
            <div><strong class="text-ink-950">Evaluate observed pairs only.</strong><p class="mt-1 text-sm text-slate-600">Each horizon is verified where the corresponding future target exists.</p></div>
          </li>
        </ol>
      </div>
      <FigureCard
        src="01_chl_sample_day.png"
        title="A real Level-3 chlorophyll day"
        caption="Gaps encode where no valid satellite target was available. They are part of the observation process, not zero chlorophyll."
      />
    </section>

    <section class="rounded-2xl border border-amber-200 bg-amber-50/60 p-6 md:p-8 mb-10">
      <div class="label-caps !text-amber-800">What this does—and does not—establish</div>
      <p class="mt-3 leading-relaxed text-slate-700">
        It establishes a reproducible observation contract and a feasible daily experiment. It does <strong>not</strong> establish superiority to an L4 system, because this study did not run a matched L4 target experiment. Any such comparison would need the same dates, domain, predictors, splits, and scoring rows.
      </p>
    </section>

    <div class="flex flex-wrap justify-between gap-3">
      <router-link to="/data" class="button-light">Data evidence</router-link>
      <router-link to="/findings/group-ablation" class="button-dark">Next: feature evidence</router-link>
    </div>
  </div>
</template>

