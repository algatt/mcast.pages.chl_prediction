<script setup>
import { ref, computed } from 'vue'
import SectionHeader from '../components/SectionHeader.vue'
import FigureCard from '../components/FigureCard.vue'
import HorizonSlider from '../components/HorizonSlider.vue'
import SkillChart from '../components/SkillChart.vue'
import Term from '../components/Term.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import WorkedExample from '../components/WorkedExample.vue'
import WorkedStep from '../components/WorkedStep.vue'
import { HORIZONS, persistence, xgbV1, xgbV2Single, xgbV2WalkForward } from '../data/results.js'

const horizon = ref(1)
const idx = computed(() => HORIZONS.indexOf(horizon.value))

// Numbers for the selected horizon
const numbers = computed(() => ({
  pers: persistence.r2[idx.value],
  v1:   xgbV1.r2[idx.value],
  v2:   xgbV2Single.r2[idx.value],
  wf:   xgbV2WalkForward.r2_mean[idx.value],
  wfStd: xgbV2WalkForward.r2_std[idx.value],
}))
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 01"
      title="L3 + native NaN matches the L4 baseline"
      lead="The conventional pipeline uses L4 (gap-filled) ocean-colour data as target. We use L3 (gappy). XGBoost handles the NaN natively. Verdict: we hit the L4 skill number without ever training on interpolation."
    />

    <!-- Reader onboarding box -->
    <ExplainerBox title="Quick refresher — L3, L4, NaN, R²" tone="primer" :open="true">
      <p>Before this page's charts make full sense, four bits of vocabulary:</p>
      <ul>
        <li><Term slug="l3"><strong>L3</strong></Term>: satellite chlorophyll gridded onto a map, with cloud gaps left <strong>missing</strong>. Looks like Swiss cheese.</li>
        <li><Term slug="l4"><strong>L4</strong></Term>: same data with the cloud gaps <strong>filled in</strong> by an algorithm (usually <Term slug="dineof">DINEOF</Term>). Looks smooth and clean.</li>
        <li><Term slug="nan"><strong>NaN</strong></Term>: the code for a missing value. Every cloud-blocked pixel is NaN.</li>
        <li><Term slug="r-squared"><strong>R²</strong></Term>: the standard score for a regression model. Runs 0–1. R² = 0.86 means the model explains 86% of the variation.</li>
      </ul>
    </ExplainerBox>

    <!-- Worked example -->
    <WorkedExample title="Worked example: one pixel, one day, both approaches"
                    intro="Suppose it is January 12, 2023, and we want to predict chlorophyll at a pixel just south of Malta for January 13. Let's walk through what happens in each approach.">
      <WorkedStep n="1" title="Look up today's chlorophyll">
        We check today's L3 chlorophyll for that pixel. Good news: no cloud. The value is <span class="kbd">0.28 mg m⁻³</span> (log10 = -0.55).
      </WorkedStep>
      <WorkedStep n="2" title="Look up yesterday's chlorophyll (lag-1 feature)">
        Bad news: yesterday there was a cloud over that pixel. The value is <span class="kbd">NaN</span>.
        <br /><strong>L4 approach:</strong> DINEOF fills it in with a guess based on nearby data — say 0.31. The model consumes 0.31 as a real observation.
        <br /><strong>Our L3 approach:</strong> we pass NaN straight to XGBoost. The model has learned during training to route NaN in the "yesterday" feature toward a specific tree branch that also considers other lag features and SST.
      </WorkedStep>
      <WorkedStep n="3" title="The rest of the features">
        Today's SST, wind, salinity, day-of-year — all defined; all fed to the model. Some lag features (7 days ago, 14 days ago) may also be NaN — no problem for our approach.
      </WorkedStep>
      <WorkedStep n="4" title="Prediction">
        <strong>L4 model:</strong> outputs (say) 0.30 mg m⁻³. But it was influenced by DINEOF's invented "0.31 yesterday". If DINEOF was wrong (and DINEOF is often wrong at winter blooms), the prediction inherits the mistake.
        <br /><strong>Our model:</strong> outputs (say) 0.32 mg m⁻³, computed from real signals only. When we compare to the actual value on Jan 13 (say 0.34), we can trace exactly where our prediction came from — no hidden gap-filler assumptions.
      </WorkedStep>
      <WorkedStep n="5" title="Score across many days">
        Repeat this over thousands of (pixel, day) pairs. Both approaches score R² ≈ 0.85 at H+1 — the L4 approach in the published literature, ours in this project. But ours never touched interpolated data.
      </WorkedStep>
    </WorkedExample>

    <!-- Interactive horizon-picker card -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-4">Explore the scoreboard</h2>
      <HorizonSlider v-model="horizon" />

      <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
        <div class="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div class="text-xs text-slate-500 font-semibold uppercase tracking-wide">Persistence</div>
          <div class="text-2xl font-bold tabular-nums text-slate-800">{{ numbers.pers.toFixed(3) }}</div>
          <div class="text-xs text-slate-500 mt-1">yesterday's value</div>
        </div>
        <div class="p-4 rounded-lg bg-ocean-50 border border-ocean-200">
          <div class="text-xs text-ocean-700 font-semibold uppercase tracking-wide">XGB v1</div>
          <div class="text-2xl font-bold tabular-nums text-ocean-900">{{ numbers.v1.toFixed(3) }}</div>
          <div class="text-xs text-ocean-700 mt-1">CHL history + SST + depth</div>
        </div>
        <div class="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
          <div class="text-xs text-emerald-700 font-semibold uppercase tracking-wide">XGB v2 (single)</div>
          <div class="text-2xl font-bold tabular-nums text-emerald-900">{{ numbers.v2.toFixed(3) }}</div>
          <div class="text-xs text-emerald-700 mt-1">full covariate stack</div>
        </div>
        <div class="p-4 rounded-lg bg-rose-50 border border-rose-200">
          <div class="text-xs text-rose-700 font-semibold uppercase tracking-wide">XGB v2 (walk-forward)</div>
          <div class="text-2xl font-bold tabular-nums text-rose-900">{{ numbers.wf.toFixed(3) }} ± {{ numbers.wfStd.toFixed(2) }}</div>
          <div class="text-xs text-rose-700 mt-1">honest, 8-fold mean ± std</div>
        </div>
      </div>

      <p class="text-sm text-slate-600 mt-4 leading-relaxed">
        Move the slider to see how R² changes with lead time. At H+1 the model is within rounding distance of
        the reported L4 baseline (0.85); at longer horizons the L3 approach pulls ahead in relative terms
        because persistence degrades faster than the model.
      </p>
    </div>

    <!-- Full skill chart -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-4">Full skill curves — persistence vs climatology vs model</h2>
      <SkillChart metric="r2" :showWF="true" />
      <p class="text-sm text-slate-600 mt-4 leading-relaxed">
        The pink band shows the walk-forward standard deviation across 8 quarterly folds. Where the pink band
        contains the blue line, the single-split number is within one σ of the honest walk-forward estimate.
        Where the blue line sits above the top of the pink band, the single split was systematically lucky.
      </p>
    </div>

    <!-- Explanation -->
    <div class="grid lg:grid-cols-2 gap-8 mb-10">
      <div class="prose prose-slate max-w-none">
        <h3>Why this matters</h3>
        <p>
          <Term slug="l4">L4</Term> products look clean because someone else already filled the cloud gaps. A model trained on L4 is
          learning to <em>agree with the interpolator</em> as much as it's learning ocean physics. That
          inductive bias — spatial and temporal smoothness — is exactly the thing an operational forecaster
          will struggle to match when the gap-filler isn't there.
        </p>
        <p>
          Using <Term slug="l3">L3</Term> as target and letting <Term slug="xgboost">XGBoost</Term> handle <Term slug="nan">NaN</Term> natively means the model is trained on
          <strong>what the operational system will actually see</strong>: gappy days, gappy pixels, and all.
          It learns to make predictions that are useful under those conditions, not idealised ones.
        </p>

        <h3>The predictor rule</h3>
        <p>
          The no-interpolation rule applies only to the <em>target</em>. Predictors are allowed to be
          gap-free model or <Term slug="reanalysis">reanalysis</Term> fields — they have to be, since wind, salinity, currents, <Term slug="mld">MLD</Term>, etc.
          don't exist as daily L3 observations. Using modelled wind as an input creates no circularity
          because the model is never scored on reproducing it. The one line we don't cross: feeding a
          biogeochemical model's <em>own</em> chlorophyll output as a predictor for observed chlorophyll.
          That is circular. We don't do it.
        </p>
      </div>

      <div class="space-y-4">
        <FigureCard
          src="06_xgb_vs_baselines.png"
          title="XGB v1 vs the two baselines (single-split)"
          caption="Model beats persistence at every horizon, climatology at every horizon. The gap widens with horizon as persistence degrades faster."
        />
      </div>
    </div>

    <!-- The numeric result -->
    <div class="card mb-10 bg-gradient-to-br from-ocean-50 to-white border-ocean-200">
      <h2 class="text-xl font-bold text-slate-900 mb-4">The headline claim</h2>
      <div class="prose prose-slate max-w-none">
        <blockquote class="border-l-4 border-ocean-500 pl-4 italic text-slate-700">
          "Using non-interpolated L3 chlorophyll-a as the forecast target — with cloud gaps preserved as
          NaN and handled natively by XGBoost — achieves R² = 0.86 at H+1 on a held-out chronological
          split and R² = 0.78 ± 0.08 across eight quarterly walk-forward folds. This matches the R² ≈ 0.85
          benchmark reported by L4-based systems in the same region, without ever training the model on
          gap-filled targets."
        </blockquote>
      </div>
    </div>

    <div class="mt-10 flex flex-wrap gap-3 justify-between">
      <router-link to="/methodology" class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
        ← Methodology
      </router-link>
      <router-link to="/findings/group-ablation" class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
        Finding 02 — Group Ablation →
      </router-link>
    </div>
  </div>
</template>
