<script setup>
import nb12 from '../data/nb12.json'
import nb07 from '../data/nb07.json'
import { steps, stepPath } from '../data/steps.js'
import StepLayout from '../components/StepLayout.vue'
import StatTile from '../components/StatTile.vue'
import GainTable from '../components/GainTable.vue'

const H = [1, 4, 7]
const days = (h) => `+${h} day${h > 1 ? 's' : ''}`
const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`
const signed2 = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(2)}`
const fmt = (n) => Math.round(n).toLocaleString('en-GB')
const longDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const step05 = steps.find((s) => s.number === '05')
const step07 = steps.find((s) => s.number === '07')
const step08 = steps.find((s) => s.number === '08')
const step11 = steps.find((s) => s.number === '11')

const [firstYear, lastYear] = nb12.years
const passes = nb12.decision.includes('worth')
const rule = nb12.decision_rule

// --- Does wind come before sudden changes? ------------------------------------------------
const MEASURE_NAMES = {
  'Yesterday': 'Yesterday’s wind',
  'Strongest of past 3 days': 'Strongest of the past three days',
  'Mixing energy, past 3 days': 'Mixing energy, past three days',
  'Rise over the week before': 'Rise over the week before',
}
const primary = nb12.measures.find((m) => m.measure === rule.measure)
const classes = nb12.classes
const windiest = classes[classes.length - 1]
const calmest = classes[0]
const quietest = classes.reduce((a, b) => (b.sudden_pct < a.sudden_pct ? b : a))
const BAR_MAX = Math.max(20, Math.ceil(Math.max(...classes.map((c) => c.sudden_pct)) / 5) * 5)
const seasonMax = Math.max(...nb12.seasons.flatMap((s) => Object.values(s.sudden_pct)))
const windiestEverySeason = nb12.seasons.every((s) => s.sudden_pct[5] === Math.max(...Object.values(s.sudden_pct)))
const strongestSeason = nb12.seasons.reduce((a, b) => (b.sudden_pct[5] - b.sudden_pct[1] > a.sudden_pct[5] - a.sudden_pct[1] ? b : a))
const shade = (v) => `rgba(95, 81, 201, ${Math.min(0.85, v / seasonMax) * 0.55})`

// --- Which way? ------------------------------------------------------------------------------
const rising = classes.map((c) => c.rising_pct)

// --- Is that where the model loses? --------------------------------------------------------
const ALL = 'All years'
const UNSEEN = nb12.groups.find((g) => g.years !== ALL).years
const group = (years, name) => nb12.groups.find((g) => g.years === years && g.group === name)
const groupRows = (years) => nb12.groups.filter((g) => g.years === years)
const classGains = (years) => groupRows(years).filter((g) => g.group.startsWith('Wind class')).map((g) => g.model_gain)
const bestClass = (years) => groupRows(years).filter((g) => g.group.startsWith('Wind class'))
  .reduce((a, b) => (b.model_gain > a.model_gain ? b : a))
const groupLabel = (name) => name.replace('Wind class 1', 'Calmest fifth').replace(`Wind class ${classes.length}`, 'Windiest fifth')
  .replace('Wind class ', 'Fifth ')

// --- The hedge -------------------------------------------------------------------------------
const hedgeRow = (pred, h) => nb12.hedge.find((r) => pred(r.data) && r.horizon === h)
const isUnseen = (d) => d === String(lastYear)
const isLive = (d) => d.startsWith('Live')
const trainingYears = nb12.hedge.filter((r) => r.data.includes('in training'))
const trainRange = (key) => [Math.min(...trainingYears.map((r) => r[key])), Math.max(...trainingYears.map((r) => r[key]))]
const kept = Math.round(100 * trainingYears.reduce((s, r) => s + r.hedge_gain, 0) / trainingYears.reduce((s, r) => s + r.model_gain, 0))
const liveDays = (h) => Number((hedgeRow(isLive, h)?.data.match(/\((\d+) issue days\)/) || [])[1])
const hedgeRows = [
  { label: `Model, ${lastYear}`, note: 'unseen year', values: Object.fromEntries(H.map((h) => [h, hedgeRow(isUnseen, h)?.model_gain])) },
  { label: `Hedge, ${lastYear}`, note: 'unseen year', emphasis: true, values: Object.fromEntries(H.map((h) => [h, hedgeRow(isUnseen, h)?.hedge_gain])) },
  { label: 'Model, live', note: `issue days from 26 Oct, targets to ${shortDate(nb12.live_chl_archive_days[1])}`, values: Object.fromEntries(H.map((h) => [h, hedgeRow(isLive, h)?.model_gain])) },
  { label: 'Hedge, live', note: 'the same days', emphasis: true, values: Object.fromEntries(H.map((h) => [h, hedgeRow(isLive, h)?.hedge_gain])) },
]
const trial = nb07.evaluation.hedge_test ?? null

const sections = [
  { id: 'question', label: 'The question' },
  { id: 'rules', label: 'Rules fixed in advance' },
  { id: 'wind', label: 'Does wind come first?' },
  { id: 'direction', label: 'Which way?' },
  { id: 'model', label: 'Is that where the model loses?' },
  { id: 'hedge', label: 'A cheaper remedy' },
  { id: 'meaning', label: 'What it means' },
]
</script>

<template>
  <StepLayout number="12" :sections="sections">
    <template #lead>
      This analysis uses the 14 November 2026 snapshot. Step 07 contains the updated issue-time replay.
      Live, the model loses on a few days when chlorophyll jumps or drops sharply overnight. Before building anything new, this
      step asks a narrow question of {{ lastYear - firstYear + 1 }} years of the archive: do days of strong wind come before those
      changes? It also tests a remedy that needs no new data at all.
    </template>

    <section id="question" class="article scroll-mt-24">
      <h2>The question</h2>
      <p>
        <router-link :to="stepPath(step11)" class="font-semibold text-teal-800 hover:underline">Step 11</router-link> found that the
        model’s live losses come from a few days of sudden change, and that nothing in its inputs announces them. Strong wind is the obvious
        candidate: it mixes the surface layer, bringing up nutrients or spreading a bloom, and it does so within a day or two.
      </p>
      <p>
        <router-link :to="stepPath(step05)" class="font-semibold text-teal-800 hover:underline">Step 05</router-link> tested wind as an
        ordinary input and found it adds little on average. But an average over every day can hide a signal that matters on a few. So this
        step does not build a model. It asks two simpler questions first, on the archive from {{ firstYear }} (when the wind record starts)
        to {{ lastYear }}:
      </p>
      <ol>
        <li><strong>Does wind come before sudden changes?</strong> If it does, wind is worth a modelling step of its own.</li>
        <li><strong>Is that where the model loses to the blend rule?</strong> If it is, wind would point at the model’s weak days.</li>
      </ol>
    </section>

    <section id="rules" class="mt-14 scroll-mt-24 article">
      <h2>Rules fixed in advance</h2>
      <p>
        A question asked after seeing a problem invites a search until something turns up. To avoid that, the definitions and the
        decision were written down before any result was looked at.
      </p>
      <ul>
        <li><strong>Sudden-change day.</strong> An issue day whose average next-day change, from the latest observation to the
          target, is in the top 10% for its season. Judging within the season stops winter, when everything changes more, from
          taking all the places. In practice that means an overnight change, averaged over the whole area, of more than about
          {{ Math.round(nb12.sudden_threshold_pct.Summer) }}% in summer, {{ Math.round(nb12.sudden_threshold_pct.Autumn) }}% in autumn,
          {{ Math.round(nb12.sudden_threshold_pct.Spring) }}% in spring and {{ Math.round(nb12.sudden_threshold_pct.Winter) }}% in winter:
          {{ nb12.sudden_days }} of {{ fmt(nb12.issue_days) }} issue days.</li>
        <li><strong>Wind, as a forecast would have it.</strong> The average over the area of both satellite passes, using only days before
          the issue day, one day late as in step 04. Four measures: yesterday’s wind, the strongest of the past three days, the mixing
          energy of the past three days, and the rise of yesterday’s wind over the week before.</li>
        <li><strong>Wind classes.</strong> Within each season, days are split into five equal groups by wind, from the calmest fifth to the
          windiest.</li>
        <li><strong>The decision.</strong> Wind is worth a modelling step if, for the strongest of the past three days, sudden changes are at
          least {{ rule.ratio }} times as common after the windiest fifth of days as after the calmest, and the 95% range of that ratio,
          from resampling whole weeks, lies above 1.</li>
      </ul>
    </section>

    <section id="wind" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Does wind come before sudden changes?</h2>
        <p>
          Yes. After the windiest fifth of days, {{ windiest.sudden_pct.toFixed(0) }}% of issue days were sudden-change days, against
          {{ calmest.sudden_pct.toFixed(0) }}% after the calmest fifth. By construction the average is 10%.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="Windiest against calmest" :value="`${primary.ratio.toFixed(1)}×`"
                  :detail="`as many sudden-change days; 95% range ${primary.ratio_low.toFixed(2)}–${primary.ratio_high.toFixed(2)}`" />
        <StatTile label="The rule" :value="passes ? 'Passed' : 'Not passed'"
                  :detail="`at least ${rule.ratio}×, with the whole range above 1`" />
        <StatTile label="Wind and the size of change" :value="signed2(nb12.correlation_size)"
                  :detail="`rank correlation within season, over ${fmt(primary.issue_days)} issue days`" />
      </div>

      <figure class="figure">
        <div class="figure-title">Sudden-change days after calm and windy days</div>
        <div class="figure-subtitle">{{ firstYear }}–{{ lastYear }}, 1-day forecasts; wind = strongest of the past three days, in fifths within each season</div>
        <div class="mt-6">
          <div class="relative h-48 flex items-end gap-3 sm:gap-6 border-b border-slate-300" role="img"
               :aria-label="`Share of sudden-change days by wind class: ${classes.map((c) => `${c.sudden_pct.toFixed(0)}%`).join(', ')}`">
            <div class="absolute inset-x-0 border-t border-dashed border-slate-500" :style="{ bottom: `${(100 * 10) / BAR_MAX}%` }">
              <span class="absolute right-0 -top-4 font-mono text-[10px] text-slate-500">10% on average</span>
            </div>
            <div v-for="c in classes" :key="c.wind_class" class="flex-1 h-full flex flex-col justify-end items-center">
              <span class="mb-1 text-xs font-semibold tabular-nums text-ink-950">{{ c.sudden_pct.toFixed(1) }}%</span>
              <span class="w-full max-w-[4.5rem] rounded-t" :class="c === windiest ? 'bg-[#5f51c9]' : 'bg-[#a9a1e6]'"
                    :style="{ height: `${(100 * c.sudden_pct) / BAR_MAX}%` }"></span>
            </div>
          </div>
          <div class="mt-2 flex gap-3 sm:gap-6">
            <div v-for="c in classes" :key="c.wind_class" class="flex-1 text-center text-[11px] leading-tight text-slate-600">
              <span class="font-semibold text-ink-950">{{ c === calmest ? 'Calmest' : c === windiest ? 'Windiest' : `Fifth ${c.wind_class}` }}</span>
              <span class="block tabular-nums">about {{ c.wind_median_ms.toFixed(0) }} m/s</span>
            </div>
          </div>
        </div>
        <figcaption class="figure-caption">
          Each bar is one fifth of the issue days, about {{ fmt(windiest.issue_days) }} days each. Wind speeds are each fifth’s median,
          over all seasons.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The pattern is not a smooth rise. The calm days are about average; the middle fifths are quietest
          ({{ quietest.sudden_pct.toFixed(0) }}% at the lowest); and the step up comes in the two windiest fifths. It is the strong-wind days that
          matter, not wind in general, which is why an average over all days, as in step 05, could miss it.
        </p>
        <p>
          The other measures tell the same story. Yesterday’s wind alone gives the largest ratio; the rise over the week before is the only
          measure whose range reaches below 1:
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>Wind measure</th><th class="text-right">After the windiest fifth</th><th class="text-right">After the calmest fifth</th>
            <th class="text-right">Ratio (95% range)</th><th class="text-right">Correlation with size</th></tr></thead>
          <tbody>
            <tr v-for="m in nb12.measures" :key="m.measure" :class="m === primary ? 'bg-teal-50/60' : ''">
              <td class="font-semibold text-ink-950">{{ MEASURE_NAMES[m.measure] || m.measure }}<span v-if="m === primary" class="block text-[11px] font-normal text-slate-500">the measure the rule uses</span></td>
              <td class="num">{{ m.sudden_windiest_pct.toFixed(1) }}%</td>
              <td class="num">{{ m.sudden_calmest_pct.toFixed(1) }}%</td>
              <td class="num">{{ m.ratio.toFixed(2) }}× ({{ m.ratio_low.toFixed(2) }}–{{ m.ratio_high.toFixed(2) }})</td>
              <td class="num">{{ signed2(m.correlation) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">
          Share of issue days that were sudden-change days. Correlation: rank correlation, within season, of the wind measure with the size of
          the next-day change.
        </p>
      </div>

      <div class="article">
        <p>
          <template v-if="windiestEverySeason">In every season the windiest fifth has the most sudden changes.</template>
          The effect is strongest in {{ strongestSeason.season.toLowerCase() }}, the season of the live record:
          {{ strongestSeason.sudden_pct[5].toFixed(0) }}% after the windiest days against {{ strongestSeason.sudden_pct[1].toFixed(0) }}% after the calmest.
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>Season</th>
            <th v-for="k in classes.map((c) => c.wind_class)" :key="k" class="!text-center">{{ k === 1 ? 'Calmest' : k === classes.length ? 'Windiest' : `Fifth ${k}` }}</th></tr></thead>
          <tbody>
            <tr v-for="s in nb12.seasons" :key="s.season">
              <td class="font-semibold text-ink-950">{{ s.season }}</td>
              <td v-for="k in classes.map((c) => c.wind_class)" :key="k" class="!text-center tabular-nums"
                  :style="{ background: shade(s.sudden_pct[k]) }">{{ s.sudden_pct[k].toFixed(0) }}%</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">Share of sudden-change days, by season and wind fifth. Darker: more sudden changes. About 90–100 issue days per cell.</p>
      </div>
    </section>

    <section id="direction" class="mt-14 scroll-mt-24 article">
      <h2>Which way?</h2>
      <p>
        A forecast of the amount can only use wind directly if wind also says which way chlorophyll will move. This was checked after the
        first result, as a description rather than part of the decision, and the answer is no. In every wind fifth, between
        {{ Math.round(Math.min(...rising)) }}% and {{ Math.round(Math.max(...rising)) }}% of days saw chlorophyll rise. Wind goes with the
        size of the change ({{ signed2(nb12.correlation_size) }}), but hardly at all with its direction ({{ signed2(nb12.correlation_signed) }}).
      </p>
      <p>
        Strong wind says “expect a big change”, not “expect a rise”. That is still useful: it is a warning that today’s value is about to
        become a poor guide.
      </p>
    </section>

    <section id="model" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Is that where the model loses?</h2>
        <p>
          If the model’s weakness were windy, fast-changing days, its gain over the blend rule should shrink on them. In the archive it does not.
          Across all years the model gains most after the windiest days, and more on sudden-change days than on others; in {{ lastYear }} its gain
          varies between groups with no clear pattern.
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead>
            <tr><th>Days</th>
              <th class="text-right">Issue days</th><th class="text-right">Model vs blend</th><th class="text-right">Hedge vs blend</th>
              <th class="text-right">Issue days</th><th class="text-right">Model vs blend</th><th class="text-right">Hedge vs blend</th></tr>
            <tr class="text-[11px]"><th></th>
              <th colspan="3" class="!text-center">{{ firstYear }}–{{ lastYear }}, mostly in training</th>
              <th colspan="3" class="!text-center">{{ lastYear }} only, unseen</th></tr>
          </thead>
          <tbody>
            <tr v-for="g in groupRows(ALL)" :key="g.group" :class="g.group === 'Sudden-change days' ? 'border-t-2 border-slate-300' : ''">
              <td class="font-semibold text-ink-950 whitespace-nowrap">{{ groupLabel(g.group) }}</td>
              <td class="num">{{ fmt(g.issue_days) }}</td>
              <td class="num font-semibold text-ink-950">{{ signed(g.model_gain) }}</td>
              <td class="num">{{ signed(g.hedge_gain) }}</td>
              <td class="num">{{ fmt(group(UNSEEN, g.group).issue_days) }}</td>
              <td class="num font-semibold text-ink-950">{{ signed(group(UNSEEN, g.group).model_gain) }}</td>
              <td class="num">{{ signed(group(UNSEEN, g.group).hedge_gain) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">
          Reduction in typical log error at 1 day, against the blend rule; positive means better than the blend. The model was trained on issue
          days up to {{ longDate(nb12.trained_until) }}, so its scores before {{ lastYear }} flatter it.
        </p>
      </div>

      <div class="article">
        <p>
          Across all years the model’s gain ranges from {{ signed(Math.min(...classGains(ALL))) }} to {{ signed(Math.max(...classGains(ALL))) }}
          by wind fifth, highest in the {{ groupLabel(bestClass(ALL).group).toLowerCase() }}. Those years are mostly in training, but {{ lastYear }},
          the fair test, shows no clear weakness on windy or sudden days either ({{ signed(Math.min(...classGains(UNSEEN))) }} to
          {{ signed(Math.max(...classGains(UNSEEN))) }} by wind fifth; {{ signed(group(UNSEEN, 'Sudden-change days').model_gain) }} on sudden-change days,
          {{ signed(group(UNSEEN, 'Other days').model_gain) }} on the others).
        </p>
        <p>
          So the second answer is no. In the archive, sudden-change days are not where the model loses to the blend rule; the live losses of
          step 11 are not what the archive would have predicted. Wind events come before sudden changes, but in the past the model has coped
          with them as well as the blend rule, or better.
        </p>
      </div>
    </section>

    <section id="hedge" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>A cheaper remedy: the hedge</h2>
        <p>
          Whatever the cause of the live losses, there is a remedy that needs no new data: average the model’s forecast and the blend rule’s,
          half and half on the log scale. The weight was fixed, not tuned. When the two disagree, the hedge lands between them, so it cannot
          lose as badly as the worse of the two.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">The model and the hedge against the blend rule</div>
        <div class="figure-subtitle">Reduction in typical log error; teal = better than the blend rule</div>
        <div class="mt-5">
          <GainTable :rows="hedgeRows" />
        </div>
        <figcaption class="figure-caption">
          Live issue days: {{ H.map((h) => `${liveDays(h)} at ${days(h)}`).join(', ') }}, the same days as step 07’s live scores at the time of this
          step. Too few for 95% ranges.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The trade is clear. In the archive years the hedge keeps about {{ kept }}% of the model’s 1-day gain
          ({{ signed(trainRange('hedge_gain')[0]) }} to {{ signed(trainRange('hedge_gain')[1]) }}, against {{ signed(trainRange('model_gain')[0]) }} to
          {{ signed(trainRange('model_gain')[1]) }}). In {{ lastYear }} it costs a little at 1 day, almost nothing at 4 and nothing at 7. On the live weeks it cuts
          the loss to the blend rule by more than half at every lead time.
        </p>
        <p>
          But the live weeks are the very days that suggested the hedge, so they cannot also be the evidence for it. The hedge is therefore on
          trial on new days only, with its decision rule fixed in advance
          (<router-link :to="stepPath(step07)" class="font-semibold text-teal-800 hover:underline">step 07</router-link>).
        </p>
      </div>
    </section>

    <section id="meaning" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What it means</h2>
      </div>
      <div class="mt-4 grid gap-4">
        <div class="card">
          <div class="font-semibold text-ink-950">Wind announces how much, not which way</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The rule fixed in advance is passed: sudden changes are {{ primary.ratio.toFixed(1) }} times as common after the windiest days as after
            the calmest. But wind says nothing about the direction, so it is more use as a warning (when to trust today’s value less) than as
            a straightforward input to a forecast of the amount.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">In the archive, the model already copes</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The model is not weaker than the blend rule on windy or sudden-change days in the archive, including in {{ lastYear }}. So the live losses
            remain unexplained, and wind may help less than the first result suggests. A modelling step with wind-event inputs is worth doing, but
            it should be judged, with its bar set in advance, on the days the model gets wrong, not only on average.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">Live wind is now being kept</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            A live forecast that uses wind needs live wind. Since 15 November 2026 the archive
            (<router-link :to="stepPath(step08)" class="font-semibold text-teal-800 hover:underline">step 08</router-link>) saves both daily
            satellite passes; its first run reached back to 16 October, which covers every live issue day scored so far. That also allows this
            check to be repeated on the live weeks themselves.
          </p>
        </div>
        <div v-if="trial" class="card">
          <div class="font-semibold text-ink-950">The hedge, on trial since {{ longDate(trial.test_from) }}</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            After {{ trial.decision_days }} scored issue days at 1 day, the hedge or the blend rule replaces the model only if its gain over the model
            has a 95% range above zero. Latest status: {{ trial.decision.text }}
          </p>
        </div>
      </div>
      <div class="mt-8 flex flex-wrap gap-3">
        <router-link to="/" class="button-light">Back to the overview</router-link>
        <router-link :to="stepPath(step07)" class="button-light">Step 07 · Live data validation</router-link>
        <router-link :to="stepPath(step11)" class="button-light">Step 11 · {{ step11.title }}</router-link>
      </div>
    </section>
  </StepLayout>
</template>
