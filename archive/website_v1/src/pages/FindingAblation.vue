<script setup>
import { ref } from 'vue'
import SectionHeader from '../components/SectionHeader.vue'
import AblationChart from '../components/AblationChart.vue'
import { groupImportance } from '../data/results.js'

const view = ref('abl')
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 02 · Feature evidence"
      title="All eight feature groups survived two different tests"
      lead="Grouped permutation measures what the fitted model uses. Grouped ablation retrains without a group to measure what the pipeline needs. Correlated predictors make both views necessary."
    />

    <section class="grid md:grid-cols-3 gap-4 mb-10">
      <article class="card">
        <div class="label-caps">Final feature set</div>
        <div class="mt-2 text-3xl font-semibold text-ink-950">32 features</div>
        <p class="mt-2 text-sm text-slate-600">Organised into eight scientifically interpretable groups.</p>
      </article>
      <article class="card">
        <div class="label-caps">Single-split H+3</div>
        <div class="mt-2 text-3xl font-semibold text-ink-950">+0.005 R²</div>
        <p class="mt-2 text-sm text-slate-600">v2 = 0.811 versus v1 = 0.806; a modest incremental gain.</p>
      </article>
      <article class="card">
        <div class="label-caps">Retention rule</div>
        <div class="mt-2 text-xl font-semibold text-ink-950">Two checks per group</div>
        <p class="mt-2 text-sm text-slate-600">Negative ablation ΔR² plus permutation ΔRMSE greater than two permutation SDs.</p>
      </article>
    </section>

    <section class="chart-panel mb-10">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-5">
        <div>
          <div class="label-caps">Interactive evidence</div>
          <h2 class="mt-2 text-2xl font-semibold text-ink-950">Group importance at H+3</h2>
        </div>
        <div class="inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm" role="group" aria-label="Importance view">
          <button v-for="option in ['abl', 'perm', 'both']" :key="option" @click="view = option"
            :class="['px-3 py-2 rounded-md', view === option ? 'bg-ink-950 text-white' : 'text-slate-600 hover:bg-slate-50']">
            {{ option === 'abl' ? 'Ablation' : option === 'perm' ? 'Permutation' : 'Both' }}
          </button>
        </div>
      </div>
      <AblationChart :view="view" />
      <p class="mt-4 pt-4 border-t border-slate-200 text-xs leading-relaxed text-slate-500">
        ΔRMSE and |ΔR²| have different units. In the combined view, compare bars within each coloured series—not the absolute height of one series against the other.
      </p>
    </section>

    <section class="card mb-10 overflow-hidden">
      <div class="flex flex-wrap justify-between gap-3 mb-5">
        <div>
          <div class="label-caps">Exact values</div>
          <h2 class="mt-2 text-xl font-semibold text-ink-950">The complete 32-feature ledger</h2>
        </div>
        <p class="max-w-lg text-sm text-slate-600">Ablation values below zero mean performance fell after the group was removed and the model retrained.</p>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[720px] text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
              <th class="py-3 pr-4">Group</th><th class="py-3 px-4 text-right">Columns</th><th class="py-3 px-4 text-right">Permutation ΔRMSE</th><th class="py-3 pl-4 text-right">Ablation ΔR²</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in [...groupImportance].sort((a,b) => a.abl - b.abl)" :key="g.group" class="border-b border-slate-100 last:border-0">
              <td class="py-3 pr-4 font-mono text-ink-950">{{ g.group }}</td>
              <td class="py-3 px-4 text-right tabular-nums text-slate-600">{{ g.cols }}</td>
              <td class="py-3 px-4 text-right tabular-nums text-cyan-800">+{{ g.perm.toFixed(4) }} ± {{ g.permStd.toFixed(4) }}</td>
              <td class="py-3 pl-4 text-right tabular-nums" :class="g.abl <= -0.005 ? 'font-semibold text-rose-700' : 'text-slate-700'">{{ g.abl.toFixed(4) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="rounded-2xl border border-slate-200 bg-white p-6 md:p-8 mb-10">
      <h2 class="text-xl font-semibold text-ink-950">Interpretation</h2>
      <p class="mt-3 text-slate-700 leading-relaxed">
        CHL history has the largest permutation signal, while static/time has the largest ablation penalty. That is not contradictory: the fitted model relies heavily on recent chlorophyll, while depth and seasonal position are harder for other groups to replace. Importance is evidence of predictive dependence—not proof of physical causation.
      </p>
    </section>

    <div class="flex flex-wrap justify-between gap-3">
      <router-link to="/findings/observation-contract" class="button-light">Previous: observation contract</router-link>
      <router-link to="/findings/walk-forward" class="button-dark">Next: temporal robustness</router-link>
    </div>
  </div>
</template>

