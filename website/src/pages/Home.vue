<script setup>
import FindingCard from '../components/FindingCard.vue'
import SkillChart from '../components/SkillChart.vue'
import { findings } from '../data/findings.js'
import { headlineStats } from '../data/results.js'

const phases = [
  { n: '01', label: 'Observe', detail: 'L3 CHL target, coverage domain, SST and bathymetry', stages: 'Notebooks 01–03' },
  { n: '02', label: 'Construct', detail: 'Leakage-checked targets, lags and 360k stratified rows', stages: 'Notebook 04' },
  { n: '03', label: 'Compare', detail: 'Persistence, climatology and chronological XGBoost', stages: 'Notebooks 05–07' },
  { n: '04', label: 'Enrich', detail: '32 features; group permutation plus retrained ablation', stages: 'Notebooks 08a–08b' },
  { n: '05', label: 'Stress-test', detail: 'Bloom events, eight walk-forward folds and final freeze', stages: 'Notebooks 09–11' },
]
</script>

<template>
  <div class="home-page">
    <section class="hero-shell">
      <div class="hero-grid" aria-hidden="true"></div>
      <div class="container-page relative py-14 md:py-20 lg:py-24">
        <div class="grid lg:grid-cols-[1.12fr_.88fr] gap-10 lg:gap-16 items-end">
          <div class="fade-up">
            <div class="flex flex-wrap items-center gap-2.5">
              <span class="hero-kicker">Validated research pipeline</span>
              <span class="hero-meta">Malta–Sicily Channel · 2021–2023</span>
            </div>

            <h1 class="hero-title">
              Forecasting chlorophyll<br />
              <span>without inventing the missing ocean.</span>
            </h1>

            <p class="hero-lead">
              A reviewer-facing account of a daily 1 km forecasting experiment built on
              non-gap-filled L3 chlorophyll observations, leakage-aware targets, physical
              covariates and quarterly walk-forward validation.
            </p>

            <div class="mt-8 flex flex-wrap gap-3">
              <router-link to="/methodology" class="button-primary">
                Follow the pipeline <span aria-hidden="true">→</span>
              </router-link>
              <router-link to="/primer" class="button-ghost">
                Read the plain-language primer
              </router-link>
            </div>
          </div>

          <aside class="contract-panel fade-up-delay-2" aria-label="Evaluation contract">
            <div class="contract-panel__header">
              <span>Evaluation contract</span>
              <span class="status-dot"><i></i> frozen run</span>
            </div>
            <dl class="contract-list">
              <div>
                <dt>Target</dt>
                <dd>Observed daily L3 CHL; native gaps retained</dd>
              </div>
              <div>
                <dt>Single split</dt>
                <dd>2021 fit · 2022 validate · 2023 test</dd>
              </div>
              <div>
                <dt>Primary estimate</dt>
                <dd>8 quarterly expanding-window folds</dd>
              </div>
              <div>
                <dt>Comparison</dt>
                <dd>Model and persistence on identical rows</dd>
              </div>
            </dl>
            <p class="contract-note">
              Fold standard deviations show temporal variability; they are not confidence intervals.
            </p>
          </aside>
        </div>

        <div class="metric-rail fade-up-delay-3">
          <div v-for="stat in headlineStats" :key="stat.label" class="metric-rail__item">
            <div class="metric-rail__label">{{ stat.label }}</div>
            <div class="metric-rail__value">{{ stat.value }}</div>
            <div class="metric-rail__detail">{{ stat.detail }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="container-page py-16 md:py-24">
      <div class="section-intro">
        <div>
          <div class="label-caps">Evidence, not a victory lap</div>
          <h2 class="section-title">Four conclusions the pipeline can defend</h2>
        </div>
        <p>
          Each claim is tied to a validation gate and an artifact. The site separates
          single-split diagnostics from the primary walk-forward result and reports the
          bloom detector’s false alarms beside its F1 score.
        </p>
      </div>

      <div class="mt-10 grid lg:grid-cols-2 gap-6">
        <FindingCard v-for="finding in findings" :key="finding.slug" :finding="finding" />
      </div>
    </section>

    <section class="evidence-band">
      <div class="container-page py-16 md:py-24">
        <div class="grid lg:grid-cols-[.78fr_1.22fr] gap-10 lg:gap-14 items-center">
          <div>
            <div class="label-caps text-teal-700">Primary regression result</div>
            <h2 class="section-title mt-3">Skill persists, but the single split was optimistic.</h2>
            <p class="mt-5 text-slate-600 leading-relaxed">
              The solid teal line is the mean XGBoost score across eight test quarters.
              The shaded area is ±1 fold standard deviation. The grey dashed line is
              persistence on exactly the same rows; the cyan dotted line is the 2023
              single-split diagnostic.
            </p>

            <div class="result-callout mt-7">
              <div>
                <span>H+3 lift over persistence</span>
                <strong>+0.109 R²</strong>
              </div>
              <p>0.654 vs 0.545 across matched quarterly folds.</p>
            </div>

            <router-link to="/findings/walk-forward" class="text-link mt-7 inline-flex">
              Inspect fold-level evidence <span aria-hidden="true">→</span>
            </router-link>
          </div>

          <figure class="chart-panel">
            <SkillChart metric="r2" :showWF="true" />
            <figcaption>
              Figure guide: higher R² is better. The widening band at longer horizons
              indicates larger quarter-to-quarter variation, not statistical uncertainty.
            </figcaption>
          </figure>
        </div>
      </div>
    </section>

    <section class="container-page py-16 md:py-24">
      <div class="grid lg:grid-cols-[.72fr_1.28fr] gap-10 lg:gap-16">
        <div>
          <div class="label-caps">Thirteen notebooks, one reading path</div>
          <h2 class="section-title mt-3">From observation to a frozen result</h2>
          <p class="mt-5 text-slate-600 leading-relaxed">
            The notebooks are arranged as a chain of explicit contracts. A failed gate
            stops the next stage; a passed gate leaves a machine-readable artifact for it.
          </p>
          <router-link to="/methodology" class="button-dark mt-7 inline-flex">
            Open the full pipeline
          </router-link>
        </div>

        <ol class="phase-list">
          <li v-for="phase in phases" :key="phase.n">
            <span class="phase-list__number">{{ phase.n }}</span>
            <div>
              <h3>{{ phase.label }}</h3>
              <p>{{ phase.detail }}</p>
            </div>
            <span class="phase-list__stages">{{ phase.stages }}</span>
          </li>
        </ol>
      </div>
    </section>

    <section class="container-page pb-16 md:pb-24">
      <div class="limitations-strip">
        <div class="limitations-strip__mark" aria-hidden="true">!</div>
        <div>
          <div class="label-caps text-amber-800">Boundary of the evidence</div>
          <h2>Validated experiment, not an operational forecasting service.</h2>
          <p>
            The record spans three years; walk-forward folds overlap; predictions are
            evaluated on a stratified sample rather than full-grid operations; and the H+3
            rare-event detector raises more than one false alarm for every true alarm.
          </p>
        </div>
        <router-link to="/about" class="button-light shrink-0">Read limitations</router-link>
      </div>
    </section>
  </div>
</template>
