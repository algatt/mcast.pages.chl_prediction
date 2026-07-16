<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import PredictionPlayer from '../components/PredictionPlayer.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import Term from '../components/Term.vue'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Forecast explorer"
      title="Actual vs. predicted, day by day"
      lead="Scrub through the test period and watch the model's forecast track the real satellite chlorophyll field — and where it goes wrong. Every pixel of the Malta–Sicily Channel is predicted; the error map on the right is the honest scorecard."
    />

    <ExplainerBox title="How to read this" tone="primer" :open="true">
      <p>
        Each frame shows one day of the held-out <Term slug="train-val-test">test set</Term>. The
        <strong>left</strong> panel is the actual satellite <Term slug="chl-a">chlorophyll</Term>
        field (blank pixels are cloud gaps). The <strong>middle</strong> panel is what the model
        predicted that far ahead (<Term slug="forecast-horizon">horizon</Term> H+1 to H+7). The
        <strong>right</strong> panel is the error — predicted minus
        actual — so you can see not just <em>how</em> accurate the forecast is, but <em>where</em>.
      </p>
      <p>
        Use <strong>Play</strong> to animate through time, drag the <strong>Day</strong> slider to
        jump to a date, and switch <strong>Horizon</strong> to compare a one-day-ahead forecast (H+1)
        against a week-ahead forecast (H+7). Longer horizons blur and drift — that's forecast skill
        decaying with lead time, made visible.
      </p>
      <p>
        The <strong>Reference</strong> toggle switches what the forecast is measured against.
        <strong>L3 obs</strong> is the real satellite field with cloud gaps — the honest error, but
        full of holes. <strong>L4 gap-free</strong> is the conventional
        <Term slug="dineof">DINEOF</Term>-interpolated product: it fills the gaps so the error map is
        complete, but it is <em>itself</em> a model, so treat it as a comparison, not truth. Watching
        the forecast track L4 — when it was only ever trained on gappy L3 — is
        <router-link to="/findings/l3-vs-l4" class="text-ocean-600 underline">Finding 01</router-link>
        made visible.
      </p>
    </ExplainerBox>

    <PredictionPlayer class="mb-10" />

    <div class="prose prose-slate max-w-none">
      <h3>Why the forecast looks smoother than reality</h3>
      <p>
        The model predicts the conditional mean, so it naturally damps the sharpest filaments and
        eddies — a well-known trait of least-squares forecasts. The error map makes the trade-off
        explicit: broad basin-scale structure is captured well (pale error), while narrow frontal
        features are where residuals concentrate.
      </p>
      <p>
        These are dense, every-pixel forecasts rebuilt over the test period in
        <span class="kbd">experiment/07-Interpretability.ipynb</span> (section 7.7) and exported to
        static frames — the same maps as the notebook's interactive player, made portable.
      </p>
    </div>
  </div>
</template>
