<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import SkillChart from '../components/SkillChart.vue'
import PerFoldChart from '../components/PerFoldChart.vue'
import FigureCard from '../components/FigureCard.vue'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 03 · Temporal robustness"
      title="The single-split score is optimistic"
      lead="Eight expanding-window quarterly folds replace one convenient test year with repeated tests across seasons. The model remains better than matched persistence, but performance varies materially over time."
    />

    <section class="grid md:grid-cols-3 gap-4 mb-10">
      <article class="card">
        <div class="label-caps">H+3 single split</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-cyan-800">0.811</div>
        <p class="mt-2 text-sm text-slate-600">Full 2023 diagnostic test split.</p>
      </article>
      <article class="card">
        <div class="label-caps">H+3 walk-forward</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-teal-800">0.654 ± 0.121</div>
        <p class="mt-2 text-sm text-slate-600">Mean ± fold SD across eight quarterly tests.</p>
      </article>
      <article class="card">
        <div class="label-caps">Matched persistence</div>
        <div class="mt-2 text-3xl font-semibold tabular-nums text-slate-700">0.545 ± 0.146</div>
        <p class="mt-2 text-sm text-slate-600">Same rows and quarters; model lift = +0.109 R².</p>
      </article>
    </section>

    <section class="chart-panel mb-10">
      <div class="section-intro mb-5">
        <div><div class="label-caps">Primary result</div><h2>Skill across all seven horizons</h2></div>
        <p>The teal mean and SD band are the primary estimate. The cyan single split is retained as a diagnostic comparison.</p>
      </div>
      <SkillChart metric="r2" :showWF="true" />
      <p class="mt-4 pt-4 border-t border-slate-200 text-xs leading-relaxed text-slate-500">
        The shaded region is ±1 standard deviation across folds. Because folds overlap in training data and are not independent random samples, it must not be read as a confidence interval.
      </p>
    </section>

    <section class="chart-panel mb-10">
      <div class="section-intro mb-5">
        <div><div class="label-caps">Quarter-level audit</div><h2>H+3, fold by fold</h2></div>
        <p>Winter quarters are hardest: 2022Q1 reaches R² = 0.451, while 2023Q4 reaches 0.797. The model beats persistence in every quarter shown.</p>
      </div>
      <PerFoldChart />
    </section>

    <section class="grid gap-6 lg:grid-cols-2 mb-10">
      <FigureCard
        src="10_walk_forward.png"
        title="Walk-forward performance by horizon"
        caption="Notebook output for the mean and fold spread. The primary comparison uses persistence recomputed on each fold’s valid test rows."
      />
      <FigureCard
        src="10_walk_forward_per_fold.png"
        title="Quarter-to-quarter variation"
        caption="Season and year matter. Reporting only the 2023 single split would hide this temporal sensitivity."
      />
    </section>

    <section class="rounded-2xl border border-amber-200 bg-amber-50/60 p-6 md:p-8 mb-10">
      <div class="label-caps !text-amber-800">Reviewer takeaway</div>
      <p class="mt-3 text-slate-700 leading-relaxed">
        The defensible headline is <strong>H+3 R² = 0.654 ± 0.121</strong>, not 0.811. The model’s advantage over persistence is consistent at every forecast horizon, but the three-year record is still too short to characterise multi-year regime shifts.
      </p>
    </section>

    <div class="flex flex-wrap justify-between gap-3">
      <router-link to="/findings/group-ablation" class="button-light">Previous: feature evidence</router-link>
      <router-link to="/findings/bloom-detection" class="button-dark">Next: bloom events</router-link>
    </div>
  </div>
</template>

