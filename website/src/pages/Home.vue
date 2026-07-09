<script setup>
import StatCard from '../components/StatCard.vue'
import FindingCard from '../components/FindingCard.vue'
import SkillChart from '../components/SkillChart.vue'
import Term from '../components/Term.vue'
import { headlineStats } from '../data/results.js'
import { findings } from '../data/findings.js'
</script>

<template>
  <div>
  <!-- ── Hero ────────────────────────────────────────────────── -->
  <section class="bg-grad-hero text-white overflow-hidden relative">
    <div class="absolute inset-0 opacity-20 pointer-events-none"
         style="background-image: radial-gradient(circle at 20% 30%, white 0.5px, transparent 1px), radial-gradient(circle at 80% 60%, white 0.5px, transparent 1px); background-size: 40px 40px;"/>
    <div class="container-page py-16 md:py-24 relative">
      <div class="max-w-3xl fade-up">
        <span class="badge bg-white/15 text-white border border-white/25 backdrop-blur">
          Malta–Sicily Channel · 2021–2023 · L3 methodology
        </span>
        <h1 class="mt-4 text-4xl md:text-6xl font-bold leading-tight">
          Forecasting chlorophyll-a<br />
          <span class="text-ocean-200">without gap-filling.</span>
        </h1>
        <p class="mt-6 text-xl text-ocean-100 max-w-2xl leading-relaxed">
          A daily 1&nbsp;km ocean-colour forecasting system built on
          non-interpolated L3 observations. Honest cloud gaps preserved as
          NaN, native tree-based handling, twelve validation gates.
        </p>

        <div class="mt-8 flex flex-wrap gap-3">
          <router-link to="/primer"
            class="px-5 py-2.5 rounded-lg bg-white text-ocean-900 font-semibold hover:bg-ocean-50 transition-colors">
            🌱 New here? Start with the primer
          </router-link>
          <router-link to="/methodology"
            class="px-5 py-2.5 rounded-lg bg-white/10 border border-white/30 backdrop-blur text-white font-medium hover:bg-white/20 transition-colors">
            See the methodology
          </router-link>
        </div>
        <p class="mt-3 text-sm text-ocean-100/70">
          Not familiar with terms like L3, XGBoost, or R²? The primer explains everything from scratch.
        </p>
      </div>

      <!-- headline stats grid -->
      <div class="mt-14 grid grid-cols-2 md:grid-cols-4 gap-4 fade-up-delay-2">
        <StatCard v-for="(s, i) in headlineStats" :key="i"
          :label="s.label" :value="s.value" :detail="s.detail" />
      </div>
    </div>
  </section>

  <!-- ── Findings section ────────────────────────────────────── -->
  <section class="container-page py-16 md:py-20">
    <div class="mb-10 max-w-3xl fade-up">
      <div class="text-xs uppercase tracking-widest font-semibold text-ocean-600 mb-2">Four key findings</div>
      <h2 class="text-3xl md:text-4xl font-bold text-slate-900">What we actually learned</h2>
      <p class="mt-3 text-lg text-slate-600 leading-relaxed">
        The four things worth putting in an abstract. Click any card for the full analysis, interactive charts,
        and the honest limitations.
      </p>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <div v-for="(f, i) in findings" :key="f.slug" :class="`fade-up-delay-${i+1}`">
        <FindingCard :finding="f" />
      </div>
    </div>
  </section>

  <!-- ── Live chart teaser ────────────────────────────────────── -->
  <section class="bg-slate-100 py-16 md:py-20 border-y border-slate-200">
    <div class="container-page">
      <div class="grid lg:grid-cols-5 gap-10 items-center">
        <div class="lg:col-span-2">
          <div class="text-xs uppercase tracking-widest font-semibold text-ocean-600 mb-2">Forecast skill</div>
          <h2 class="text-3xl font-bold text-slate-900 leading-tight">
            R² decays gracefully across the 7-day window.
          </h2>
          <p class="mt-4 text-slate-600 leading-relaxed">
            The shaded band is the walk-forward standard deviation across 8 quarterly folds — the honest
            error bar. The blue line is the single-split test (optimistic). The gap between them is the
            <router-link to="/findings/walk-forward" class="text-ocean-700 font-semibold underline">Walk-Forward finding</router-link>.
          </p>
          <ul class="mt-6 space-y-2 text-sm text-slate-700">
            <li class="flex items-start gap-2">
              <span class="text-emerald-600 mt-0.5">✓</span> Beats persistence at every horizon
            </li>
            <li class="flex items-start gap-2">
              <span class="text-emerald-600 mt-0.5">✓</span> Beats climatology at every horizon
            </li>
            <li class="flex items-start gap-2">
              <span class="text-emerald-600 mt-0.5">✓</span> Publication-grade error bars from 8 folds
            </li>
          </ul>
        </div>
        <div class="lg:col-span-3 card">
          <SkillChart metric="r2" :showWF="true" />
        </div>
      </div>
    </div>
  </section>

  <!-- ── The bet, in short ──────────────────────────────────── -->
  <section class="container-page py-16 md:py-20">
    <div class="max-w-4xl mx-auto">
      <div class="text-xs uppercase tracking-widest font-semibold text-ocean-600 mb-2">The methodological bet</div>
      <h2 class="text-3xl md:text-4xl font-bold text-slate-900 leading-tight">
        L3 + native NaN, not L4 + interpolation.
      </h2>

      <div class="prose prose-slate max-w-none mt-6">
        <p>
          Most published <Term slug="chl-a">chl-a</Term> forecasting uses <Term slug="l4"><strong>L4</strong></Term> ocean-colour products — where the data
          producer has already filled cloud gaps with <Term slug="dineof">DINEOF</Term> or optimal interpolation. Training on L4 means
          the model is partly being scored on <em>reproducing the gap-filler</em>. Its skill at predicting
          cloudy days is its skill at agreeing with DINEOF.
        </p>
        <p>
          Our bet: use <Term slug="l3"><strong>L3</strong></Term> — non-interpolated, gappy observations — as the target and let
          cloud gaps stay as <Term slug="nan"><span class="kbd">NaN</span></Term>. Pair it with <Term slug="xgboost">XGBoost</Term>, which learns a default split
          direction for missing values at every tree node. Missing observations become a <em>feature</em>
          of the data, not something to fabricate.
        </p>
        <p>
          <strong>The result:</strong> <Term slug="r-squared">R²</Term> of 0.86 at <Term slug="forecast-horizon">H+1</Term> on a single split — matching L4-based systems —
          and R² = 0.78 ± 0.08 across 8 <Term slug="walk-forward">walk-forward</Term> folds. All the honesty, none of the skill loss.
        </p>
      </div>

      <div class="mt-8 flex flex-wrap gap-3">
        <router-link to="/findings/l3-vs-l4"
          class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
          Full L3 vs L4 analysis →
        </router-link>
        <router-link to="/data"
          class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
          Data sources
        </router-link>
      </div>
    </div>
  </section>
  </div>
</template>
