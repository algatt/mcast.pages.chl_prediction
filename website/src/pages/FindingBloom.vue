<script setup>
import { computed, ref } from 'vue'
import SectionHeader from '../components/SectionHeader.vue'
import BloomChart from '../components/BloomChart.vue'
import HorizonSlider from '../components/HorizonSlider.vue'
import FigureCard from '../components/FigureCard.vue'
import { HORIZONS, bloomSkill, bloomPOD, bloomFAR, bloomRates } from '../data/results.js'

const metric = ref('F1')
const horizon = ref(3)
const index = computed(() => HORIZONS.indexOf(horizon.value))
const value = (series) => series[index.value]
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 04 · Bloom events"
      title="Rare-event skill clears H+3 narrowly, with too many false alarms"
      lead="The monthly P90 definition reaches F1 = 0.508 at H+3, but its false-alarm ratio is 0.545. That is useful research evidence—not an operational warning service."
    />

    <section class="grid md:grid-cols-3 gap-4 mb-10">
      <article class="card">
        <div class="label-caps">P90 H+3 F1</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-teal-800">0.508</div>
        <p class="mt-2 text-sm text-slate-600">Just above the predeclared 0.50 validation gate.</p>
      </article>
      <article class="card">
        <div class="label-caps">P90 H+3 FAR</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-rose-700">0.545</div>
        <p class="mt-2 text-sm text-slate-600">More than half of raised alarms are false.</p>
      </article>
      <article class="card">
        <div class="label-caps">Observed event rate</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-ink-950">17.6%</div>
        <p class="mt-2 text-sm text-slate-600">P90 H+3 scoring rows; genuinely imbalanced, though not exactly 10% after transfer.</p>
      </article>
    </section>

    <section class="chart-panel mb-10">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-5">
        <div><div class="label-caps">Threshold definitions</div><h2 class="mt-2 text-2xl font-semibold text-ink-950">Event skill by lead time</h2></div>
        <div class="inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm" role="group" aria-label="Bloom metric">
          <button v-for="m in ['F1', 'POD', 'FAR']" :key="m" @click="metric = m"
            :class="['px-3 py-2 rounded-md', metric === m ? 'bg-ink-950 text-white' : 'text-slate-600 hover:bg-slate-50']">{{ m }}</button>
        </div>
      </div>
      <BloomChart :metric="metric" />
      <p class="mt-4 pt-4 border-t border-slate-200 text-xs leading-relaxed text-slate-500">
        Higher is better for F1 and POD; lower is better for FAR. The grey median+5% series has an approximately 50% event rate and is therefore an auxiliary regime diagnostic, not a rare-bloom result.
      </p>
    </section>

    <section class="card mb-10">
      <div class="grid gap-6 lg:grid-cols-[.7fr_1.3fr] lg:items-end">
        <div>
          <div class="label-caps">Inspect a horizon</div>
          <HorizonSlider v-model="horizon" class="mt-4" />
        </div>
        <div class="grid sm:grid-cols-3 gap-3">
          <article class="rounded-xl border border-slate-200 p-4">
            <div class="label-caps">Median + 5% · auxiliary</div>
            <div class="mt-2 text-2xl font-semibold tabular-nums">{{ value(bloomSkill.median5).toFixed(3) }}</div>
            <p class="mt-1 text-xs text-slate-500">F1 · rate {{ (value(bloomRates.median5) * 100).toFixed(1) }}%</p>
          </article>
          <article class="rounded-xl border border-teal-200 bg-teal-50/40 p-4">
            <div class="label-caps !text-teal-800">Monthly P90 · rare</div>
            <div class="mt-2 text-2xl font-semibold tabular-nums text-teal-950">{{ value(bloomSkill.percentile).toFixed(3) }}</div>
            <p class="mt-1 text-xs text-teal-800">F1 · FAR {{ value(bloomFAR.percentile).toFixed(3) }}</p>
          </article>
          <article class="rounded-xl border border-rose-200 bg-rose-50/40 p-4">
            <div class="label-caps !text-rose-700">Z-score · rare</div>
            <div class="mt-2 text-2xl font-semibold tabular-nums text-rose-900">{{ value(bloomSkill.zscore).toFixed(3) }}</div>
            <p class="mt-1 text-xs text-rose-700">F1 · POD {{ value(bloomPOD.zscore).toFixed(3) }}</p>
          </article>
        </div>
      </div>
    </section>

    <section class="grid lg:grid-cols-[1fr_.9fr] gap-6 mb-10">
      <div class="card">
        <div class="label-caps">Three definitions, two roles</div>
        <div class="mt-4 space-y-5">
          <div><h3 class="font-semibold text-ink-950">Monthly P90</h3><p class="mt-1 text-sm leading-relaxed text-slate-600">Primary rare-event definition. It clears F1 = 0.50 through H+3, then falls below from H+4 onward.</p></div>
          <div><h3 class="font-semibold text-ink-950">Z-score &gt; 1.5σ</h3><p class="mt-1 text-sm leading-relaxed text-slate-600">A second rare-event definition. At H+3, F1 = 0.486, so it does not clear the gate.</p></div>
          <div><h3 class="font-semibold text-ink-950">Median + 5%</h3><p class="mt-1 text-sm leading-relaxed text-slate-600">High scores reflect a common regime occupying roughly half the rows. It is reported for context, not presented as rare-bloom detection.</p></div>
        </div>
      </div>
      <FigureCard
        src="09_bloom_skill.png"
        title="Bloom metrics from the validation-calibrated thresholds"
        caption="The rare-event curves decay quickly with lead time. F1 alone is insufficient; POD and FAR show the missed-event and false-alarm trade-off."
      />
    </section>

    <div class="rounded-2xl border border-rose-200 bg-rose-50/60 p-6 md:p-8 mb-10">
      <div class="label-caps !text-rose-700">Deployment boundary</div>
      <p class="mt-3 leading-relaxed text-slate-700">
        A fisheries or aquaculture warning product would require explicit utility costs, threshold calibration on a longer record, probability calibration, uncertainty reporting, and prospective testing. Those steps have not been completed here.
      </p>
    </div>

    <div class="flex flex-wrap justify-between gap-3">
      <router-link to="/findings/walk-forward" class="button-light">Previous: temporal robustness</router-link>
      <router-link to="/about" class="button-dark">Limitations and reproducibility</router-link>
    </div>
  </div>
</template>

