<script setup>
import { ref, computed } from 'vue'
import SectionHeader from '../components/SectionHeader.vue'
import FigureCard from '../components/FigureCard.vue'
import BloomChart from '../components/BloomChart.vue'
import HorizonSlider from '../components/HorizonSlider.vue'
import Term from '../components/Term.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import WorkedExample from '../components/WorkedExample.vue'
import WorkedStep from '../components/WorkedStep.vue'
import { HORIZONS, bloomSkill, bloomPOD, bloomFAR } from '../data/results.js'

const metric   = ref('F1')
const horizon  = ref(3)
const idx      = computed(() => HORIZONS.indexOf(horizon.value))

const currentValues = computed(() => ({
  siegel:     { F1: bloomSkill.siegel[idx.value],     POD: bloomPOD.siegel[idx.value],     FAR: bloomFAR.siegel[idx.value] },
  percentile: { F1: bloomSkill.percentile[idx.value], POD: bloomPOD.percentile[idx.value], FAR: bloomFAR.percentile[idx.value] },
  zscore:     { F1: bloomSkill.zscore[idx.value],     POD: bloomPOD.zscore[idx.value],     FAR: bloomFAR.zscore[idx.value] },
}))
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 04"
      title="Bloom detection works across three definitions"
      lead="A continuous chl-a forecast is useful, but operational users want a binary event signal. We tested three independent bloom definitions — all three clear F1 = 0.5 at every horizon."
    />

    <!-- Reader onboarding -->
    <ExplainerBox title="Refresher — what's a 'bloom' and how do we score detection?" tone="primer" :open="true">
      <p>
        A <Term slug="bloom">bloom</Term> is a temporary burst of <Term slug="phytoplankton">phytoplankton</Term> growth. Chlorophyll shoots up over a patch of ocean for a few days, then subsides. Some blooms are seasonal; some are harmful.
      </p>
      <p>
        To score a bloom detector we count four things per prediction:
      </p>
      <ul>
        <li><Term slug="true-positive"><strong>TP</strong></Term> (true positive): predicted bloom, actual bloom. Good — we caught one.</li>
        <li><strong>FP</strong> (false positive): predicted bloom, no bloom. A false alarm.</li>
        <li><strong>FN</strong> (false negative): no prediction, actual bloom. A miss.</li>
        <li><strong>TN</strong> (true negative): no prediction, no bloom. Correct rest.</li>
      </ul>
      <p>
        From these counts:
      </p>
      <ul>
        <li><Term slug="pod"><strong>POD</strong></Term> (probability of detection) = TP / (TP + FN). "Of real blooms, how many did we catch?"</li>
        <li><Term slug="far"><strong>FAR</strong></Term> (false-alarm ratio) = FP / (TP + FP). "Of our alarms, how many were fake?"</li>
        <li><Term slug="csi"><strong>CSI</strong></Term> = TP / (TP + FN + FP). Overlap between predicted and actual.</li>
        <li><Term slug="f1"><strong>F1</strong></Term> = 2·TP / (2·TP + FP + FN). Single-number summary. F1 ≥ 0.5 is the operational bar.</li>
      </ul>
      <p>
        Notice what we do <em>not</em> compute: overall accuracy. Blooms are rare — you can score 90% accuracy by predicting "no bloom" every day. Accuracy is useless here.
      </p>
    </ExplainerBox>

    <!-- Worked example -->
    <WorkedExample title="Worked example: scoring 100 days of forecasts at one pixel"
                   intro="Suppose we forecast 100 days at a specific pixel, of which 20 days had real blooms (a rare event). Here is what each metric would say about a hypothetical result.">
      <WorkedStep n="1" title="What actually happened">
        Over 100 days, the pixel had 20 real bloom days (20%) and 80 non-bloom days.
      </WorkedStep>
      <WorkedStep n="2" title="What our model predicted">
        We flagged 25 days as blooms and 75 as non-blooms.
      </WorkedStep>
      <WorkedStep n="3" title="Counting the four outcomes">
        Of the 25 flagged days: 16 were real (TP), 9 were false alarms (FP).<br />
        Of the 75 non-flagged days: 71 were correctly non-bloom (TN), 4 were missed blooms (FN).<br />
        So <strong>TP = 16, FP = 9, FN = 4, TN = 71</strong>. Sanity check: 16 + 9 + 4 + 71 = 100 ✓.
      </WorkedStep>
      <WorkedStep n="4" title="Computing the metrics">
        POD = 16 / (16 + 4) = <strong>0.80</strong> — we caught 80% of real blooms.<br />
        FAR = 9 / (16 + 9) = <strong>0.36</strong> — 36% of our alarms were wrong.<br />
        CSI = 16 / (16 + 4 + 9) = <strong>0.55</strong> — overlap between predicted and actual sets.<br />
        F1 = (2·16) / (2·16 + 9 + 4) = 32 / 45 = <strong>0.71</strong> — single-number summary.
      </WorkedStep>
      <WorkedStep n="5" title="Why we do not report accuracy">
        Accuracy = (TP + TN) / 100 = 87%. Sounds great, right? But now consider a "lazy" model that predicts "no bloom" every single day. It would score (0 + 80) / 100 = <strong>80% accuracy</strong> — and F1 = 0, POD = 0, useless. Accuracy hides the lazy model; F1 and POD do not.
      </WorkedStep>
      <WorkedStep n="6" title="Our actual result">
        Averaged over the whole test set, our model at H+1 scores F1 = 0.71, POD = 0.72, FAR = 0.30. At H+7, F1 = 0.63, POD = 0.67, FAR = 0.41. Not perfect, but well above the F1 = 0.5 operational bar.
      </WorkedStep>
    </WorkedExample>

    <!-- Definitions -->
    <div class="grid md:grid-cols-3 gap-4 mb-10">
      <div class="card">
        <div class="text-xs uppercase tracking-wide font-semibold text-ocean-600 mb-2">Definition 1</div>
        <h3 class="text-lg font-bold text-slate-900">Siegel (median + 5%)</h3>
        <p class="text-sm text-slate-600 mt-2 leading-relaxed">
          <span class="kbd">CHL > 1.05 × clim_median(DOY, pixel)</span>. Catches the spring-bloom regime in
          oligotrophic basins. A low bar by design.
        </p>
      </div>
      <div class="card">
        <div class="text-xs uppercase tracking-wide font-semibold text-emerald-600 mb-2">Definition 2</div>
        <h3 class="text-lg font-bold text-slate-900">Percentile (P90)</h3>
        <p class="text-sm text-slate-600 mt-2 leading-relaxed">
          <span class="kbd">CHL > clim_p90(DOY, pixel)</span>. Rare-event definition — top 10% of historical
          observations for that day-of-year at that pixel.
        </p>
      </div>
      <div class="card">
        <div class="text-xs uppercase tracking-wide font-semibold text-rose-600 mb-2">Definition 3</div>
        <h3 class="text-lg font-bold text-slate-900">Z-score (>1.5σ)</h3>
        <p class="text-sm text-slate-600 mt-2 leading-relaxed">
          <span class="kbd">(CHL − clim_mean) / clim_std > 1.5</span>. Anomaly definition — orthogonal to
          percentile because it accounts for the spread of historical values.
        </p>
      </div>
    </div>

    <!-- Interactive metric-picker + slider -->
    <div class="card mb-10">
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h2 class="text-lg font-bold text-slate-900">Skill vs horizon (interactive)</h2>
        <div class="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 text-sm">
          <button v-for="m in ['F1', 'POD', 'FAR']" :key="m" @click="metric = m"
            :class="['px-3 py-1 rounded-md transition-colors', metric === m ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']">
            {{ m }}
          </button>
        </div>
      </div>
      <BloomChart :metric="metric" />

      <div class="mt-6">
        <HorizonSlider v-model="horizon" />
      </div>

      <div class="grid md:grid-cols-3 gap-3 mt-6">
        <div class="p-4 rounded-lg bg-slate-50 border border-slate-200">
          <div class="text-xs text-slate-500 uppercase tracking-wide font-semibold">Siegel</div>
          <div class="text-2xl font-bold tabular-nums text-slate-900">{{ currentValues.siegel[metric].toFixed(3) }}</div>
          <div class="text-xs text-slate-500 mt-1">{{ metric }} at H+{{ horizon }}</div>
        </div>
        <div class="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
          <div class="text-xs text-emerald-700 uppercase tracking-wide font-semibold">Percentile</div>
          <div class="text-2xl font-bold tabular-nums text-emerald-900">{{ currentValues.percentile[metric].toFixed(3) }}</div>
          <div class="text-xs text-emerald-700 mt-1">{{ metric }} at H+{{ horizon }}</div>
        </div>
        <div class="p-4 rounded-lg bg-rose-50 border border-rose-200">
          <div class="text-xs text-rose-700 uppercase tracking-wide font-semibold">Z-score</div>
          <div class="text-2xl font-bold tabular-nums text-rose-900">{{ currentValues.zscore[metric].toFixed(3) }}</div>
          <div class="text-xs text-rose-700 mt-1">{{ metric }} at H+{{ horizon }}</div>
        </div>
      </div>
    </div>

    <!-- Metric explainer -->
    <div class="grid md:grid-cols-4 gap-3 mb-10 text-sm">
      <div class="card">
        <div class="font-bold text-slate-900 mb-1">POD</div>
        <div class="text-slate-600 leading-relaxed">Probability of detection — <em>what fraction of real blooms did we catch?</em> Range 0–1, higher is better.</div>
      </div>
      <div class="card">
        <div class="font-bold text-slate-900 mb-1">FAR</div>
        <div class="text-slate-600 leading-relaxed">False-alarm ratio — <em>of our bloom alarms, what fraction were spurious?</em> Range 0–1, lower is better.</div>
      </div>
      <div class="card">
        <div class="font-bold text-slate-900 mb-1">CSI</div>
        <div class="text-slate-600 leading-relaxed">Critical success index — Jaccard of predicted and actual blooms. Range 0–1, higher is better.</div>
      </div>
      <div class="card">
        <div class="font-bold text-slate-900 mb-1">F1</div>
        <div class="text-slate-600 leading-relaxed">Harmonic mean of precision and recall — single-number summary. F1 ≥ 0.5 is the operational bar.</div>
      </div>
    </div>

    <!-- Why not accuracy -->
    <div class="grid lg:grid-cols-2 gap-8 mb-10">
      <div class="prose prose-slate max-w-none">
        <h3>Why not accuracy?</h3>
        <p>
          Because for rare events accuracy is meaningless. Predict "no bloom" every day → 90% accuracy,
          0% usefulness. The contingency-table metrics — POD, FAR, CSI, F1 — count true positives, false
          positives, false negatives separately, so a lazy "always-negative" model scores 0 across the
          board.
        </p>

        <h3>How well does it actually work?</h3>
        <p>
          At H+1, F1 sits at 0.69–0.71 across all three definitions. At H+7, F1 is still 0.59–0.63.
          POD stays in the 0.6–0.7 band — the model catches ~2 out of 3 real bloom days at one week's
          lead. FAR rises from 0.30 to 0.45 — of the alarms raised, most are real, and the false-alarm
          rate deteriorates gently rather than collapsing.
        </p>

        <h3>Translation for an operational user</h3>
        <p>
          "Given a bloom alarm from this system at H+3, there's a ~65% chance a real bloom will occur.
          The system will miss about a third of real blooms." That's a useful signal for a fisheries or
          aquaculture operator — actionable, quantifiable, and reliably calibrated.
        </p>
      </div>

      <div class="space-y-4">
        <FigureCard
          src="09_bloom_skill.png"
          title="Bloom-detection skill vs horizon (all 4 metrics)"
          caption="POD stays high (0.6–0.7). FAR grows gently (0.30 → 0.45). CSI declines from 0.55 to 0.41. F1 declines from 0.71 to 0.59 — never crossing the 0.5 line."
        />
      </div>
    </div>

    <!-- Fallback note -->
    <div class="card bg-gradient-to-br from-emerald-50 to-white border-emerald-200 mb-10">
      <h2 class="text-xl font-bold text-slate-900 mb-3">The dormant fallback</h2>
      <p class="text-slate-700 leading-relaxed">
        The methodology plan included a decision branch: <em>if F1 < 0.5 across all three definitions at
        H+3, switch to Isolation Forest on forecast residuals as the headline detector.</em> We
        implemented the branch, tested it, and it did not fire. The threshold-based detector is the
        headline; the unsupervised path is documented as a backup for future studies where the
        threshold-based path might underperform.
      </p>
    </div>

    <div class="mt-10 flex flex-wrap gap-3 justify-between">
      <router-link to="/findings/walk-forward" class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
        ← Finding 03
      </router-link>
      <router-link to="/about" class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
        About the project →
      </router-link>
    </div>
  </div>
</template>
