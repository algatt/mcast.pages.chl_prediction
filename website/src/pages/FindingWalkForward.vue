<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import SkillChart from '../components/SkillChart.vue'
import PerFoldChart from '../components/PerFoldChart.vue'
import FigureCard from '../components/FigureCard.vue'
import Term from '../components/Term.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
import WorkedExample from '../components/WorkedExample.vue'
import WorkedStep from '../components/WorkedStep.vue'
import { HORIZONS, xgbV2Single, xgbV2WalkForward } from '../data/results.js'

// Build a gap table
const rows = HORIZONS.map((h, i) => ({
  h,
  single: xgbV2Single.r2[i],
  wf: xgbV2WalkForward.r2_mean[i],
  wfStd: xgbV2WalkForward.r2_std[i],
  gap: xgbV2WalkForward.r2_mean[i] - xgbV2Single.r2[i],
}))
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Finding 03"
      title="The single split was systematically lucky"
      lead="A single 70/15/15 chronological split tells you what the model did on one window. Walk-forward across 8 quarterly folds tells you what it does across seasons. The two numbers should agree — here they don't, and the disagreement is the finding."
    />

    <!-- Reader onboarding -->
    <ExplainerBox title="Refresher — chronological split vs walk-forward" tone="primer" :open="true">
      <p>
        Both are ways to test a forecasting model on data it has not seen. They are both time-aware
        (never shuffle a time series!) but they differ in <em>how many test windows</em> they use.
      </p>
      <ul>
        <li>
          <strong><Term slug="chronological-split">Chronological split</Term></strong>: draw <em>one</em>
          date line. Train on everything before, test on everything after. You get a single R² number.
          Fast, simple, but the score depends heavily on <em>where</em> you drew the line.
        </li>
        <li>
          <strong><Term slug="walk-forward">Walk-forward</Term></strong>: draw <em>many</em> date lines.
          Fold 1: train through end-of-Q4-2021, test on Q1-2022. Fold 2: train through end-of-Q1-2022,
          test on Q2-2022. And so on. You get 8 R² numbers (one per test quarter) instead of 1, so you
          can compute a mean and standard deviation. This is what makes a claim publication-grade.
        </li>
      </ul>
      <p>
        <strong>Why walk-forward here mattered so much</strong>: our 3-year data splits neatly into
        seasons, and some seasons are much harder to forecast than others. A single-split score can
        accidentally land on the easy season and look great.
      </p>
    </ExplainerBox>

    <!-- Worked example -->
    <WorkedExample title="Worked example: rating a violinist"
                   intro="An analogy for why one test window can lie, and why we need many.">
      <WorkedStep n="1" title="Meet the violinist">
        You want to know how good a violinist is. She plays year-round: some pieces are her favourites
        (she plays them beautifully), some are still in rehearsal (a bit rough).
      </WorkedStep>
      <WorkedStep n="2" title="Bad approach: one concert">
        You attend one concert. She plays her favourite piece. You give her a score of 9/10. This is
        <strong>a single chronological split</strong> — one test window. You have no idea if she
        would also score 9 on the pieces she is still working on.
      </WorkedStep>
      <WorkedStep n="3" title="Better approach: eight concerts across the year">
        You attend 8 concerts, one every 6 weeks. She plays a mix of favourites and rehearsal pieces.
        Her scores: 6, 7, 9, 7, 8, 7, 6, 8. Average = 7.25, standard deviation = 1.0. This is
        <strong>walk-forward</strong> — 8 test windows across the whole year.
      </WorkedStep>
      <WorkedStep n="4" title="What did the single concert miss?">
        It caught her at her <em>best</em>. The honest score is 7.25 ± 1.0, not 9. And crucially, the
        ± 1.0 tells you something the single 9 could not: her skill varies a lot from piece to piece.
        That is itself a finding — it says "she is good on average but inconsistent".
      </WorkedStep>
      <WorkedStep n="5" title="Our model's version">
        Our single-split score was R² = 0.78 at H+3, taken on autumn 2023 — a favourable "concert".
        Our 8-fold walk-forward score is R² = 0.65 ± 0.12. The single split was 0.13 R² too optimistic.
        The ± 0.12 tells us the model's skill varies meaningfully across seasons — winter is much
        harder than autumn.
      </WorkedStep>
    </WorkedExample>

    <!-- The core chart -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-4">R² vs horizon — single-split vs walk-forward</h2>
      <SkillChart metric="r2" :showWF="true" />
      <p class="text-sm text-slate-600 mt-4 leading-relaxed">
        Blue line: single-split (Notebook 8b). Red line with pink band: walk-forward mean ± std across 8 quarterly folds.
        The blue line is above the pink band at every horizon — the single split was optimistic across the board.
      </p>
    </div>

    <!-- Gap table -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-4">The gap, per horizon</h2>
      <div class="overflow-x-auto -mx-2">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-slate-200 text-slate-500 text-xs uppercase tracking-wide">
              <th class="text-left p-2 font-semibold">Horizon</th>
              <th class="text-right p-2 font-semibold">Single-split R²</th>
              <th class="text-right p-2 font-semibold">Walk-forward R²</th>
              <th class="text-right p-2 font-semibold">Std</th>
              <th class="text-right p-2 font-semibold">Gap</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.h" class="border-b border-slate-100">
              <td class="p-2 font-mono font-semibold">H+{{ r.h }}</td>
              <td class="p-2 text-right tabular-nums text-slate-700">{{ r.single.toFixed(3) }}</td>
              <td class="p-2 text-right tabular-nums text-slate-700">{{ r.wf.toFixed(3) }}</td>
              <td class="p-2 text-right tabular-nums text-slate-500">± {{ r.wfStd.toFixed(3) }}</td>
              <td class="p-2 text-right tabular-nums font-bold" :class="Math.abs(r.gap) > 0.10 ? 'text-rose-600' : 'text-amber-700'">
                {{ r.gap > 0 ? '+' : '' }}{{ r.gap.toFixed(3) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="text-sm text-slate-600 mt-4 leading-relaxed">
        The gap grows with horizon — from -0.09 at H+1 to -0.22 at H+7. That's a pattern of systematic
        optimism, not sampling noise. The single-split test window is behaving qualitatively differently
        from the average quarter.
      </p>
    </div>

    <!-- Per-fold breakdown -->
    <div class="card mb-10">
      <h2 class="text-lg font-bold text-slate-900 mb-4">Per-fold R² at H+3 — why the single-split was lucky</h2>
      <PerFoldChart />
      <p class="text-sm text-slate-600 mt-4 leading-relaxed">
        The single-split test window was <strong>2023Q4</strong> — one of the two <em>easiest</em> quarters
        in the record (R² = 0.79 at H+3). Winter quarters (2022Q1, 2023Q1) run at R² = 0.46–0.52 — as much
        as 0.34 R² lower. The single-split number is a best case, not a typical case.
      </p>
    </div>

    <!-- Interpretation -->
    <div class="grid lg:grid-cols-2 gap-8 mb-10">
      <div class="prose prose-slate max-w-none">
        <h3>Why winter is harder</h3>
        <p>
          Winter is the Mediterranean's <em>convective mixing</em> season. Deep-mixing events entrain
          nutrients into the surface and drive winter blooms — highly dynamic, event-driven productivity.
          The Coverage Atlas (Gate 2) also showed winter is the cloudiest season (DJF ≈ 40% coverage vs
          summer's ≈ 62%). Less data on more variable dynamics = harder forecasting.
        </p>
        <p>
          A single chronological split in a 3-year time series inevitably lands the test in one season.
          If that season is winter (unlucky) or autumn/summer (lucky), the reported R² can be off by
          0.2 in either direction. There's no way to know from a single split whether you're on the
          lucky or unlucky side.
        </p>

        <h3>The publication-grade phrasing</h3>
        <p>
          Instead of "R² = 0.78 at H+3" — which is a lucky one-window number — the paper should read:
        </p>
        <blockquote class="border-l-4 border-ocean-500 pl-4 italic text-slate-700 my-4">
          "R² = 0.65 ± 0.12 at H+3 across 8 expanding-window quarterly folds, with winter quarters
          scoring 0.15–0.30 R² below autumn."
        </blockquote>
        <p>
          The std isn't a nuisance — it's the honest signal that the forecasting environment isn't
          stationary. Winter is a different regime.
        </p>
      </div>

      <div class="space-y-4">
        <FigureCard
          src="10_walk_forward_per_fold.png"
          title="Per-fold R² by horizon"
          caption="Every horizon shows the same winter dip: 2022Q1 and 2023Q1 sit conspicuously below the other six quarters. The single-split test (2023Q4) is at the top of every horizon's range — the definition of a lucky landing."
        />
      </div>
    </div>

    <!-- The lesson box -->
    <div class="card bg-gradient-to-br from-amber-50 to-white border-amber-200 mb-10">
      <h2 class="text-xl font-bold text-slate-900 mb-3">The lesson</h2>
      <div class="prose prose-slate max-w-none">
        <p>
          In any time series where seasons have fundamentally different dynamics, a <strong>single
          chronological split will be systematically lucky or unlucky</strong> depending on where it
          lands. This is not a subtle bias — here it inflates R² by up to 0.22.
        </p>
        <p class="mb-0">
          Walk-forward with quarterly (or seasonal) folds isn't a nice-to-have. It's <em>the</em> honest
          evaluation. The error bar is a feature: it tells the reader how season-dependent the skill is.
        </p>
      </div>
    </div>

    <div class="mt-10 flex flex-wrap gap-3 justify-between">
      <router-link to="/findings/group-ablation" class="px-5 py-2.5 rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors">
        ← Finding 02
      </router-link>
      <router-link to="/findings/bloom-detection" class="px-5 py-2.5 rounded-lg bg-ocean-600 text-white font-semibold hover:bg-ocean-700 transition-colors">
        Finding 04 — Bloom Detection →
      </router-link>
    </div>
  </div>
</template>
