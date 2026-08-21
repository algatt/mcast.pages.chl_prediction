<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import FigureCard from '../components/FigureCard.vue'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Plain-language primer"
      title="What is being predicted—and how should the evidence be read?"
      lead="A short guide for readers who do not work with ocean colour or forecast verification every day."
    />

    <section class="grid gap-6 lg:grid-cols-[1.1fr_.9fr] mb-12">
      <div class="card">
        <div class="label-caps">The scientific question</div>
        <h2 class="mt-3 text-2xl font-semibold text-ink-950">Can observed satellite chlorophyll be forecast one to seven days ahead?</h2>
        <p class="mt-4 leading-relaxed text-slate-700">
          Chlorophyll-a is the green pigment used by phytoplankton. Satellite ocean-colour products estimate its concentration near the sea surface, so it is a practical—but imperfect—indicator of biological activity.
        </p>
        <p class="mt-3 leading-relaxed text-slate-700">
          This project forecasts daily log-chlorophyll across the Malta–Sicily Channel. A label such as <strong>H+3</strong> means “three days after the issue date.”
        </p>
      </div>
      <FigureCard
        src="02_coverage_map.png"
        title="The observable chlorophyll domain"
        caption="Scores are calculated only where the satellite product can genuinely observe chlorophyll—not over land or permanently invalid pixels."
      />
    </section>

    <section class="mb-12">
      <div class="section-intro">
        <div>
          <div class="label-caps">The central design choice</div>
          <h2>Missing observations stay missing</h2>
        </div>
        <p>
          Clouds hide large parts of the sea. The pipeline preserves those gaps instead of manufacturing gap-filled chlorophyll targets.
        </p>
      </div>
      <div class="mt-6 grid md:grid-cols-3 gap-4">
        <article class="card">
          <div class="label-caps">L3 observation</div>
          <h3 class="mt-2 font-semibold text-ink-950">What the satellite saw</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">A gridded observation with cloud and quality-control gaps retained as missing values.</p>
        </article>
        <article class="card">
          <div class="label-caps">Model input</div>
          <h3 class="mt-2 font-semibold text-ink-950">Missing issue-time CHL is allowed</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">XGBoost learns branches for missing predictor values. No synthetic CHL continuity is required.</p>
        </article>
        <article class="card">
          <div class="label-caps">Scoring rule</div>
          <h3 class="mt-2 font-semibold text-ink-950">Verify only observed targets</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">A forecast contributes to a score only when chlorophyll is observed at its target time.</p>
        </article>
      </div>
    </section>

    <section class="mb-12">
      <div class="label-caps">How to read the scores</div>
      <div class="mt-4 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <article class="card">
          <h3 class="font-semibold text-ink-950">R²</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">Variance explained relative to a mean prediction. Higher is better; values can be negative.</p>
        </article>
        <article class="card">
          <h3 class="font-semibold text-ink-950">Persistence</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">A demanding baseline: forecast the latest available chlorophyll forward unchanged.</p>
        </article>
        <article class="card">
          <h3 class="font-semibold text-ink-950">Walk-forward</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">Train on the past, validate on the next quarter, and test on the quarter after that—repeated eight times.</p>
        </article>
        <article class="card">
          <h3 class="font-semibold text-ink-950">Mean ± SD</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">The average across quarters plus their spread. The SD band is not a confidence interval.</p>
        </article>
      </div>
    </section>

    <section class="card mb-12">
      <div class="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
        <div>
          <div class="label-caps">Event forecasts</div>
          <h2 class="mt-2 text-2xl font-semibold text-ink-950">A “bloom” depends on its definition</h2>
          <p class="mt-3 text-slate-700 leading-relaxed">
            The rare-event headline uses a validation-calibrated monthly 90th percentile threshold. At H+3 it reaches F1 = 0.508, but 54.5% of raised alarms are false alarms.
          </p>
        </div>
        <dl class="grid sm:grid-cols-3 gap-4">
          <div class="rounded-xl bg-slate-50 border border-slate-200 p-4">
            <dt class="label-caps">F1</dt>
            <dd class="mt-2 text-sm text-slate-700">Balances event precision and recall. Higher is better.</dd>
          </div>
          <div class="rounded-xl bg-slate-50 border border-slate-200 p-4">
            <dt class="label-caps">POD</dt>
            <dd class="mt-2 text-sm text-slate-700">Fraction of observed blooms detected. Higher is better.</dd>
          </div>
          <div class="rounded-xl bg-slate-50 border border-slate-200 p-4">
            <dt class="label-caps">FAR</dt>
            <dd class="mt-2 text-sm text-slate-700">Fraction of alarms that were false. Lower is better.</dd>
          </div>
        </dl>
      </div>
    </section>

    <div class="flex flex-wrap gap-3">
      <router-link to="/methodology" class="button-dark">Follow the 13-stage pipeline</router-link>
      <router-link to="/glossary" class="button-light">Open the glossary</router-link>
    </div>
  </div>
</template>

