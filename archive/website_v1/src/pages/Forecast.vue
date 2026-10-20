<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import FigureCard from '../components/FigureCard.vue'
import PredictionSlider from '../components/PredictionSlider.vue'

const diagnostics = [
  {
    src: '07_residual_diagnostics_h3.png',
    title: 'H+3 residual diagnostics',
    caption: 'Distribution and calibration checks for sampled, observed targets. The all-target diagnostic set contains 71,709 rows; MAE is 0.0858 log10 mg m⁻³ and mean bias is −0.0062.',
  },
  {
    src: '07_error_map_h3.png',
    title: 'Spatial error at H+3',
    caption: 'Errors are aggregated into 602 spatial bins. This reveals geography in the residuals without pretending that missing target pixels were observed.',
  },
  {
    src: '07_error_by_month.png',
    title: 'Seasonal error profile',
    caption: 'Winter MAE is 0.1264 versus 0.0628 in summer—a 2.01× ratio that helps explain quarter-to-quarter variation.',
  },
  {
    src: '07_shap_bar_h1_h7.png',
    title: 'Drivers change with forecast lead',
    caption: 'CHL history dominates short leads; calendar and environmental context gain relative influence at longer leads. SHAP is diagnostic association, not causation.',
  },
]
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Visual diagnostics"
      title="See what the aggregate score hides"
      lead="Notebook figures connect headline skill to residual shape, geography, season, and model dependence. These are diagnostics—not a dense operational forecast product."
    />

    <div class="rounded-2xl border border-cyan-200 bg-cyan-50/60 p-6 mb-10 grid gap-4 md:grid-cols-[auto_1fr]">
      <div class="w-10 h-10 rounded-full bg-white border border-cyan-200 grid place-items-center font-mono text-cyan-800">i</div>
      <div>
        <h2 class="font-semibold text-ink-950">How these visuals were produced</h2>
        <p class="mt-1 text-sm leading-relaxed text-slate-700">
          They come from the validated notebook outputs and use sampled rows or aggregated bins. Blank satellite targets remain unscored; no map on this page should be read as proof of gap-free coverage.
        </p>
      </div>
    </div>

    <PredictionSlider class="mb-12" />

    <FigureCard
      class="mb-6"
      src="11_headline.png"
      title="The complete evidence summary"
      caption="Read the walk-forward mean and spread as the primary forecasting result. The single-split score remains a useful diagnostic, but it is not the generalisation estimate."
    />

    <div class="grid gap-6 lg:grid-cols-2">
      <FigureCard v-for="figure in diagnostics" :key="figure.src" v-bind="figure" />
    </div>

    <section class="mt-12 grid md:grid-cols-3 gap-4">
      <article class="card">
        <div class="label-caps">Residual correlation</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-ink-950">−0.127</div>
        <p class="mt-2 text-sm text-slate-600">Small remaining association with the target at H+3; inspect alongside bias and error distribution.</p>
      </article>
      <article class="card">
        <div class="label-caps">Top H+1 feature</div>
        <div class="mt-2 font-mono text-sm font-semibold text-teal-800">log_chl_roll7_mean</div>
        <p class="mt-2 text-sm text-slate-600">Recent chlorophyll history is the strongest short-lead signal.</p>
      </article>
      <article class="card">
        <div class="label-caps">Calendar SHAP share</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-ink-950">0.142</div>
        <p class="mt-2 text-sm text-slate-600">Seasonal timing matters, but this number does not imply a causal effect.</p>
      </article>
    </section>

    <div class="mt-10 flex flex-wrap gap-3">
      <router-link to="/findings/walk-forward" class="button-dark">Inspect temporal robustness</router-link>
      <router-link to="/about" class="button-light">Read limitations</router-link>
    </div>
  </div>
</template>
