<script setup>
import SectionHeader from '../components/SectionHeader.vue'

const limitations = [
  { title: 'Three years cannot sample climate regimes', body: 'The 2021–2023 record supports seasonal stress tests, but not multi-year or decadal generalisation.' },
  { title: 'Fold SD is descriptive', body: 'Eight folds overlap in training data. Mean ± SD shows quarter-to-quarter spread; it is not a confidence interval.' },
  { title: 'Evaluation is sampled', body: 'The supervised table contains 360,000 sampled pixel-days. Diagnostic maps use aggregation and are not dense operational forecast fields.' },
  { title: 'One region only', body: 'The model has not been transferred beyond the Malta–Sicily Channel.' },
  { title: 'Rare-event false alarms are high', body: 'At H+3 the P90 detector has FAR = 0.545, which prevents an operational warning claim.' },
  { title: 'Some physical drivers are absent', body: 'Waves, PAR, nutrients, and a deep-learning baseline were not evaluated.' },
  { title: 'Predictor resolution and gaps remain', body: 'ERA5 is coarser than the target grid; KD490 representative domain coverage is 46.16%, while salinity, currents, SSH, and MLD reach 96.97%.' },
  { title: 'No full-record extension was run', body: 'Scaling beyond 2021–2023 requires a separate preflight for availability, versions, cost, storage, and compute.' },
]
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Limitations & reproducibility"
      title="What the evidence supports—and where it stops"
      lead="The pipeline is complete for its 2021–2023 methodology experiment. It is not an operational forecast service and it has not been validated as a multi-decadal or cross-region model."
    />

    <section class="card mb-10">
      <div class="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
        <div>
          <div class="label-caps">Reproducibility unit</div>
          <h2 class="mt-2 text-2xl font-semibold text-ink-950">Thirteen ordered notebooks</h2>
          <p class="mt-3 text-sm leading-relaxed text-slate-600">Stages 00–11 include separate 08a and 08b notebooks. Each stage declares an artifact and a validation gate before downstream work proceeds.</p>
        </div>
        <dl class="grid sm:grid-cols-3 gap-4">
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4"><dt class="label-caps">Rows</dt><dd class="mt-2 text-2xl font-semibold tabular-nums">360,000</dd></div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4"><dt class="label-caps">Features</dt><dd class="mt-2 text-2xl font-semibold tabular-nums">32</dd></div>
          <div class="rounded-xl border border-slate-200 bg-slate-50 p-4"><dt class="label-caps">Horizons</dt><dd class="mt-2 text-2xl font-semibold tabular-nums">7</dd></div>
        </dl>
      </div>
    </section>

    <section class="mb-12">
      <div class="section-intro">
        <div><div class="label-caps">Candid boundary conditions</div><h2>Limitations we own</h2></div>
        <p>These are not footnotes to hide. They determine what a reviewer—and a future user—should do with the results.</p>
      </div>
      <div class="mt-6 grid md:grid-cols-2 gap-4">
        <article v-for="item in limitations" :key="item.title" class="card">
          <h3 class="font-semibold text-ink-950">{{ item.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-600">{{ item.body }}</p>
        </article>
      </div>
    </section>

    <section class="grid lg:grid-cols-2 gap-6 mb-10">
      <article class="card">
        <div class="label-caps">What is frozen</div>
        <h2 class="mt-2 text-xl font-semibold text-ink-950">Methodology record</h2>
        <ul class="mt-4 space-y-3 text-sm leading-relaxed text-slate-700">
          <li>• Product identifiers and versions are recorded in the data ledger.</li>
          <li>• Coverage, leakage, feature-set, model-set, and evaluation gates are explicit.</li>
          <li>• Walk-forward persistence is recomputed on exactly matched test rows.</li>
          <li>• Single-split and walk-forward results are labelled separately.</li>
        </ul>
      </article>
      <article class="card">
        <div class="label-caps">What comes next</div>
        <h2 class="mt-2 text-xl font-semibold text-ink-950">Scale-up is a new experiment</h2>
        <p class="mt-4 text-sm leading-relaxed text-slate-700">
          Extending the record is not a direct rerun. It needs a preflight for historical product continuity, version drift, target-domain comparability, download limits, storage, and compute. The same validation gates should remain, but their thresholds may need prospective justification.
        </p>
      </article>
    </section>

    <div class="flex flex-wrap gap-3">
      <router-link to="/methodology" class="button-dark">Inspect every pipeline gate</router-link>
      <router-link to="/data" class="button-light">Review the source ledger</router-link>
    </div>
  </div>
</template>

