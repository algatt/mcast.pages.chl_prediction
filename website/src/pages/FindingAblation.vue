<script setup>
import { ref } from 'vue'
import SectionHeader from '../components/SectionHeader.vue'
import FigureCard from '../components/FigureCard.vue'
import AblationChart from '../components/AblationChart.vue'
import Term from '../components/Term.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import WorkedExample from '../components/WorkedExample.vue'
import WorkedStep from '../components/WorkedStep.vue'
import { groupImportance } from '../data/results.js'

const view = ref('both')  // 'perm' | 'abl' | 'both'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 02"
      title="Every group helps, none is a silver bullet"
      lead="Grouped permutation and grouped ablation tell different stories — and both are correct. Reading them together is the rigorous way to handle correlated predictors."
    />

    <!-- Reader onboarding -->
    <ExplainerBox title="Refresher — permutation vs ablation" tone="primer" :open="true">
      <p>
        Both are ways to ask "how important is this feature?" — but they answer <em>different questions</em>.
      </p>
      <ul>
        <li>
          <strong><Term slug="permutation">Permutation importance</Term></strong>: take the trained model. Randomly shuffle one column of the input data (breaking that feature's link to the target while keeping its overall distribution). Predict again. If the score drops a lot, the model was leaning on that feature. If the score barely changes, the model was ignoring it.
        </li>
        <li>
          <strong><Term slug="ablation">Ablation</Term></strong>: take the feature out of the input table entirely. <em>Retrain the model from scratch.</em> Score the retrained model. If it is much worse, that feature was essential. If it barely matters, some other feature stepped in.
        </li>
      </ul>
      <p>
        The clever bit: the two often disagree, and the disagreement is the finding. If a feature looks essential by permutation but barely matters in ablation, it means another feature can substitute for it — the model was <em>using</em> it, but did not <em>need</em> it.
      </p>
    </ExplainerBox>

    <!-- Worked example -->
    <WorkedExample title="Worked example: the salt-and-pepper chef"
                   intro="A restaurant kitchen analogy for why permutation and ablation say different things about the same feature.">
      <WorkedStep n="1" title="The chef has two shakers on the counter: salt and pepper">
        Every dish uses both. Salt is heavily used; pepper is lightly used. Both make it out of the shaker onto every plate.
      </WorkedStep>
      <WorkedStep n="2" title="Permutation experiment: swap the labels randomly">
        Randomly relabel some salt shakers as "pepper" and vice versa. Now the chef reaches for the wrong shaker half the time. Dishes come out badly seasoned. The score drops a lot. <strong>Permutation says "salt matters".</strong>
      </WorkedStep>
      <WorkedStep n="3" title="Ablation experiment: remove salt entirely">
        Take salt off the counter. The chef re-learns to cook. She increases pepper, adds more herbs, uses more citrus. Dishes are different but still good. The score drops only a little. <strong>Ablation says "salt is not essential".</strong>
      </WorkedStep>
      <WorkedStep n="4" title="What is going on?">
        Salt was heavily <em>used</em>, but pepper and herbs can <em>substitute</em>. Permutation caught the use; ablation caught the substitutability. Both answers are correct — they are answering different questions.
      </WorkedStep>
      <WorkedStep n="5" title="What our model shows">
        <Term slug="autoregressive">chl_history features</Term> (yesterday's chlorophyll, last week's mean) are like salt: the model uses them heavily (permutation ΔRMSE = 0.110, 10× anything else). But they substitute for each other — drop the whole group and other lag features step in, so ablation ΔR² is only -0.006.
        <br /><br />
        <Term slug="doy">Day-of-year</Term> and depth are like the pot itself: nothing else in the kitchen substitutes for the sense of "where and when". Ablation says -0.017 R² — the biggest drop of any group.
      </WorkedStep>
    </WorkedExample>

    <!-- Interactive chart with view switcher -->
    <div class="card mb-10">
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h2 class="text-lg font-bold text-slate-900">Group-level importance (H+3)</h2>
        <div class="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 text-sm">
          <button @click="view = 'both'"
            :class="['px-3 py-1 rounded-md transition-colors', view === 'both' ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']">
            Both
          </button>
          <button @click="view = 'perm'"
            :class="['px-3 py-1 rounded-md transition-colors', view === 'perm' ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']">
            Permutation
          </button>
          <button @click="view = 'abl'"
            :class="['px-3 py-1 rounded-md transition-colors', view === 'abl' ? 'bg-white shadow font-semibold text-ocean-700' : 'text-slate-500']">
            Ablation
          </button>
        </div>
      </div>
      <AblationChart :view="view" />
      <p class="text-sm text-slate-600 mt-4 leading-relaxed">
        Bars are sorted with the most-essential group (by ablation ΔR²) at the top. Red bars in the ablation
        view flag groups where dropping them hurts by more than 0.005 R²; amber flags 0.002–0.005; grey is
        marginal but still positive.
      </p>
    </div>

    <!-- Divergence explainer -->
    <div class="grid lg:grid-cols-2 gap-6 mb-10">
      <div class="card bg-gradient-to-br from-ocean-50 to-white border-ocean-200">
        <div class="text-xs uppercase tracking-wide font-semibold text-ocean-700 mb-2">Permutation view</div>
        <h3 class="text-xl font-bold text-slate-900 mb-2">chl_history dominates 10×</h3>
        <p class="text-slate-700 leading-relaxed">
          Shuffle any group's columns on the validation set and measure the RMSE increase. Chl_history —
          the autoregressive lags — is 10× anything else. Nothing surprising: yesterday's chl-a is a
          brutally strong predictor of tomorrow's.
        </p>
        <div class="mt-4 text-2xl font-bold tabular-nums text-ocean-900">ΔRMSE = +0.110</div>
        <div class="text-xs text-slate-500">shuffling chl_history</div>
      </div>

      <div class="card bg-gradient-to-br from-amber-50 to-white border-amber-200">
        <div class="text-xs uppercase tracking-wide font-semibold text-amber-700 mb-2">Ablation view</div>
        <h3 class="text-xl font-bold text-slate-900 mb-2">static_time is most essential</h3>
        <p class="text-slate-700 leading-relaxed">
          Drop a group entirely and retrain. Now static_time (depth + DOY sin/cos) matters more than
          chl_history. Why? Depth and DOY have <em>no substitute</em>. Chl_history features substitute
          for each other — drop t0 and lag1 fills in.
        </p>
        <div class="mt-4 text-2xl font-bold tabular-nums text-amber-800">ΔR² = −0.017</div>
        <div class="text-xs text-slate-500">removing static_time</div>
      </div>
    </div>

    <!-- Full table -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-4">All groups, both views</h2>
      <div class="overflow-x-auto -mx-2">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wide">
              <th class="text-left p-2 font-semibold">Group</th>
              <th class="text-right p-2 font-semibold">Cols</th>
              <th class="text-right p-2 font-semibold">Permutation ΔRMSE</th>
              <th class="text-right p-2 font-semibold">Ablation ΔR²</th>
              <th class="text-left p-2 font-semibold">Verdict</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in [...groupImportance].sort((a,b) => a.abl - b.abl)" :key="g.group" class="border-b border-slate-100">
              <td class="p-2 font-mono">
                {{ g.group }}
                <span v-if="g.core" class="ml-1 text-[10px] text-slate-400">core</span>
              </td>
              <td class="p-2 text-right tabular-nums text-slate-600">{{ g.cols }}</td>
              <td class="p-2 text-right tabular-nums" :class="g.perm > 0.05 ? 'font-bold text-ocean-700' : 'text-slate-600'">
                +{{ g.perm.toFixed(4) }}
              </td>
              <td class="p-2 text-right tabular-nums" :class="g.abl <= -0.005 ? 'font-bold text-rose-600' : g.abl <= -0.002 ? 'text-amber-700' : 'text-slate-600'">
                {{ g.abl.toFixed(4) }}
              </td>
              <td class="p-2 text-slate-500 text-xs">
                <span v-if="g.abl <= -0.005">essential</span>
                <span v-else-if="g.abl <= -0.002">contributes</span>
                <span v-else>marginal</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Interpretation -->
    <div class="grid lg:grid-cols-2 gap-8 mb-10">
      <div class="prose prose-slate max-w-none">
        <h3>What the divergence means</h3>
        <p>
          <strong>Permutation</strong> measures what the model <em>uses</em>, given every other feature is
          available. If a feature's shuffle destroys prediction, the model was leaning on it heavily.
          Lag-1 chl is so strongly autocorrelated with today's chl that shuffling it is devastating.
        </p>
        <p>
          <strong>Ablation</strong> measures what the model <em>needs</em>, when forced to make do without.
          Chl_history features substitute for each other — drop t0 and lag1 fills in, drop lag1 and t0 and
          roll7_mean fill in — so removing the whole group hurts less than you'd guess from permutation.
          Static_time has no substitute; removing it makes the model lose its sense of "where and when".
        </p>
        <p>
          The rigorous practice is <strong>to report both</strong>. A feature-importance claim on one metric
          alone lies about correlated predictors.
        </p>
      </div>

      <div class="space-y-4">
        <FigureCard
          src="08_correlation_heatmap.png"
          title="Spearman correlation heatmap"
          caption="Ordered by group so the block structure is visible. No pair exceeded |ρ| ≥ 0.9 — pairs are independent enough that grouped analysis is the appropriate abstraction."
        />
      </div>
    </div>

    <!-- Collective lift -->
    <div class="card bg-gradient-to-br from-emerald-50 to-white border-emerald-200 mb-10">
      <h2 class="text-xl font-bold text-slate-900 mb-3">The collective lift</h2>
      <p class="text-slate-700 leading-relaxed">
        No single new group is a silver bullet. But six new groups together lift test R² at H+3 by
        <strong>+0.024</strong> over the chl-history-only v1 model. The lift <em>grows with horizon</em> —
        by H+6, the v2 model is +0.13 R² above v1. Longer horizons rely less on autoregression and more
        on physical drivers, exactly where the new groups pull weight.
      </p>
      <div class="grid grid-cols-3 gap-3 mt-4">
        <div class="p-3 rounded-lg bg-white border border-emerald-200 text-center">
          <div class="text-xs text-slate-500 uppercase tracking-wide">H+3 lift</div>
          <div class="text-2xl font-bold tabular-nums text-emerald-700">+0.02</div>
        </div>
        <div class="p-3 rounded-lg bg-white border border-emerald-200 text-center">
          <div class="text-xs text-slate-500 uppercase tracking-wide">H+5 lift</div>
          <div class="text-2xl font-bold tabular-nums text-emerald-700">+0.01</div>
        </div>
        <div class="p-3 rounded-lg bg-white border border-emerald-200 text-center">
          <div class="text-xs text-slate-500 uppercase tracking-wide">H+6 lift</div>
          <div class="text-2xl font-bold tabular-nums text-emerald-700">+0.13</div>
        </div>
      </div>
    </div>

    <div class="mt-10 flex flex-wrap gap-3 justify-between">
      <router-link to="/findings/l3-vs-l4" class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
        ← Finding 01
      </router-link>
      <router-link to="/findings/walk-forward" class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
        Finding 03 — Walk-Forward Honesty →
      </router-link>
    </div>
  </div>
</template>
