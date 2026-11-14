<script setup>
import nb07 from '../data/nb07.json'
import { steps, stepPath } from '../data/steps.js'
import { unpack } from '../data/packed.js'
import { chlLayer, formatChl, SST_RAMP, BLOOM_RAMP } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GridMap from '../components/GridMap.vue'
import StatTile from '../components/StatTile.vue'
import IntervalChart from '../components/IntervalChart.vue'

const H = [1, 4, 7]
const { grid, live, archive, evaluation } = nb07
const rows = grid.latitude.length
const cols = grid.longitude.length
const map = (name) => unpack(live.maps[name], rows, cols)

const longDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const fmt = (n) => n.toLocaleString('en-GB')
const pctOf = (n, total) => `${((100 * n) / total).toFixed(n / total > 0.995 ? 2 : 0)}%`
const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`
const days = (h) => `+${h} day${h > 1 ? 's' : ''}`
const step11 = steps.find((s) => s.number === '11')
const step10 = steps.find((s) => s.number === '10')
const step08 = steps.find((s) => s.number === '08')

// The live forecast uses the model in use: the step 05 model until 20 October 2026, the step 09 model since.
const modelName = live.model_file.includes('step09') ? 'step 09 model' : 'step 05 model'

// When the newest chlorophyll was first downloaded, against the 20:00 UTC schedule of the day after the observation.
const chlRetrieved = live.chl_retrieved_utc || live.retrieved_utc
const retrievedAt = chlRetrieved.slice(11, 16)
const retrievedDay = chlRetrieved.slice(0, 10)
const beforeSchedule = retrievedDay < live.issue_date || (retrievedDay === live.issue_date && retrievedAt < '20:00')

const fallback = map('fallback')
const nFallback = live.pixels - live.pixels_with_history
const chlRange = { decode: (v) => 10 ** v, domain: [0.02, 0.5], ticks: [0.02, 0.05, 0.1, 0.2, 0.5], tickFormat: (t) => `${t}` }
const forecastLayer = (h, date) => {
  const values = map(`forecast_${h}`)
  return chlLayer({
    id: `f${h}`,
    label: days(h),
    legendTitle: `Forecast for ${shortDate(date)} (mg/m³)`,
    values,
    ...chlRange,
    missingLabel: 'Not forecast (step 04)',
    missingLegend: 'Not forecast (step 04)',
    describe: (r, c) =>
      values[r][c] === null
        ? { line: 'Not forecast (step 04)' }
        : { line: formatChl(10 ** values[r][c]), note: fallback[r][c] > 0.5 ? 'No observation yet: usual value for the month used' : `forecast for ${longDate(date)}` },
  })
}
const sstLo = live.sst_range ? Math.floor(live.sst_range[0] * 2) / 2 : 15
const sstHi = live.sst_range ? Math.max(sstLo + 1, Math.ceil(live.sst_range[1] * 2) / 2) : 30
const sstTicks = Array.from({ length: Math.round((sstHi - sstLo) / 0.5) + 1 }, (_, k) => sstLo + 0.5 * k)
  .filter((_, k, all) => all.length <= 5 || k % 2 === 0)
const mapLayers = [
  ...live.target_dates.map((d, i) => forecastLayer(H[i], d)),
  chlLayer({ id: 'latest', label: 'Latest obs.', values: map('latest'), ...chlRange,
             legendTitle: 'Latest chlorophyll observed (mg/m³)',
             missingLabel: 'Not observed since the archive began', missingLegend: 'No observation yet' }),
  {
    id: 'age',
    label: 'Its age',
    kind: 'sequential',
    values: map('age'),
    decode: (v) => v,
    ramp: ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'],
    domain: [1, 7],
    ticks: [1, 2, 3, 4, 5, 6, 7],
    tickFormat: (t) => (t === 7 ? '≥7' : `${t}`),
    legendTitle: 'Age of latest chlorophyll (days)',
    format: (v) => `${Math.round(v)} day${Math.round(v) > 1 ? 's' : ''} old`,
    missingLabel: 'Not observed since the archive began',
    missingLegend: 'No observation yet',
  },
  {
    id: 'sst',
    label: 'Temperature',
    kind: 'sequential',
    values: map('sst'),
    decode: (v) => v,
    ramp: SST_RAMP,
    domain: [sstLo, sstHi],
    ticks: sstTicks,
    legendTitle: 'Sea temperature (°C)',
    format: (v) => `${v.toFixed(1)} °C`,
    missingLabel: 'Not observed (cloud)',
  },
]

const ageShare = (k) => ((100 * (live.age_counts[k] || 0)) / live.pixels_with_history)
const olderThan3 = Object.entries(live.age_counts).filter(([k]) => Number(k) > 3).reduce((s, [, v]) => s + v, 0)
const oldestAge = Math.max(...Object.keys(live.age_counts).map(Number))

// --- Live scores ------------------------------------------------------------------------
const score = (h, method) => evaluation.scores.find((r) => r.horizon === `+${h}d` && r.method === method)
const gainOf = (h) => evaluation.gains.find((g) => g.horizon === `+${h}d`)
const testGainOf = (h) => evaluation.test_gains.find((g) => g.horizon === `+${h}d`)
const vsNoChange = (h) => 100 * (1 - score(h, 'Forecast model').log_rmse / score(h, 'No change').log_rmse)
const withRange = (r) => r && r.low !== null && r.high !== null
const gainGroups = [
  {
    title: `Live, ${shortDate(evaluation.first_issue_day)} – ${shortDate(evaluation.last_target_day)} ${evaluation.last_target_day.slice(0, 4)}`,
    rows: H.filter((h) => withRange(gainOf(h))).map((h) => ({ label: days(h), value: gainOf(h).gain, low: gainOf(h).low, high: gainOf(h).high })),
  },
  {
    title: `The ${evaluation.test_year} test year (step 09)`,
    rows: H.map((h) => ({ label: days(h), value: testGainOf(h).gain, low: testGainOf(h).low, high: testGainOf(h).high })),
  },
].filter((g) => g.rows.length)
const behindRange = H.map((h) => -gainOf(h).gain)
const allBehind = H.every((h) => gainOf(h).gain !== null && gainOf(h).gain < 0)
const clearlyBehind = H.filter((h) => withRange(gainOf(h)) && gainOf(h).high < 0)

// --- The hedge trial (step 12) --------------------------------------------------------------
const hedgeTest = evaluation.hedge_test ?? null
const hedgeScore = (h, method) => hedgeTest?.scores.find((r) => r.horizon === `+${h}d` && r.method === method)
const hedgeDays = hedgeTest ? Math.max(0, ...H.map((h) => hedgeScore(h, 'Forecast model')?.issue_days ?? 0)) : 0
const step12 = steps.find((s) => s.number === '12')

// --- Live blooms -----------------------------------------------------------------------
const blooms = live.blooms
const probabilityLayer = (h, date) => ({
  id: `b${h}`,
  label: days(h),
  kind: 'sequential',
  values: map(`bloom_${h}`),
  decode: (v) => v,
  ramp: BLOOM_RAMP,
  domain: [0, 0.4],
  ticks: [0, 0.1, 0.2, 0.3, 0.4],
  tickFormat: (t) => (t === 0.4 ? '≥40%' : `${Math.round(t * 100)}%`),
  legendTitle: `Chance of a bloom on ${shortDate(date)}`,
  format: (v) => `${(100 * v).toFixed(v < 0.1 ? 1 : 0)}% chance of a bloom`,
  missingLabel: 'Not forecast (step 04)',
  missingLegend: 'Not forecast (step 04)',
})
const bloomLayers = blooms ? live.target_dates.map((d, i) => probabilityLayer(H[i], d)) : []
const bloomScore = (h, method) => evaluation.blooms?.find((r) => r.horizon === `+${h}d` && r.method === method)
const bloomGroups = evaluation.blooms
  ? [
      { method: 'Bloom model', title: 'Bloom model (step 10) against the usual frequency' },
      { method: 'Anomaly rule', title: 'Anomaly rule against the usual frequency' },
    ].map((g) => ({
      title: g.title,
      rows: H.filter((h) => bloomScore(h, g.method)?.low_vs_usual !== null).map((h) => {
        const r = bloomScore(h, g.method)
        return { label: days(h), value: r.skill_vs_usual, low: r.low_vs_usual, high: r.high_vs_usual }
      }),
    })).filter((g) => g.rows.length)
  : []

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'live', label: 'A real forecast' },
  { id: 'recipe', label: 'The same recipe as training' },
  { id: 'scores', label: 'How it has done so far' },
  ...(blooms ? [{ id: 'blooms', label: 'Live bloom forecasts' }] : []),
  { id: 'next', label: 'What still needs checking' },
]
</script>

<template>
  <StepLayout number="07" :sections="sections">
    <template #lead>
      Everything so far used the reprocessed archive. A real forecast has to work from the near-real-time feed,
      published within a day and processed with less information. This step runs the model on that feed every day,
      and scores each live forecast once the satellite has seen the day it predicted.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Step 01 explained that each dataset comes in two versions: the carefully reprocessed multi-year archive used for
        training, and the near-real-time version a live service would receive. Their values and their gaps can differ.
        A model that only works on the archive would be of little use, so this step:
      </p>
      <ol>
        <li>reads the latest near-real-time chlorophyll and sea temperature from the local archive (step 08);</li>
        <li>builds the model’s inputs from them, exactly as for training ({{ live.n_inputs }} inputs for the model in use);</li>
        <li>issues a forecast for 1, 4 and 7 days ahead, and the chance of a bloom (step 10), and saves both with every input used;</li>
        <li>re-issues every past live forecast from the archive and scores it against what the satellite later observed.</li>
      </ol>
      <p>
        The last part needs patience: a 7-day forecast can only be scored with seven days of history behind it and a week
        later still. Copernicus keeps only about nine days of the live feed, which is why step 08 saves every day as it
        appears. Since {{ longDate(evaluation.first_issue_day) }} every forecast has had a complete history.
      </p>
    </section>

    <section id="live" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>A real forecast, issued {{ longDate(live.issue_date) }}</h2>
        <p>
          This is the forecast the {{ modelName }} ({{ live.n_inputs }} inputs) produced from the near-real-time feed for the evening of
          {{ longDate(live.issue_date) }}. The newest chlorophyll it had was from {{ longDate(live.latest_chl_date) }}, and
          the temperature from the night before the issue day. Switch between the three forecasts and the inputs behind them.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Live forecast and its inputs</div>
        <div class="figure-subtitle">Issued {{ longDate(live.issue_date) }}, {{ live.issue_time_utc }} UTC, from Copernicus near-real-time data</div>
        <div class="mt-5">
          <GridMap :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea" :layers="mapLayers"
                   aria-label="Live chlorophyll forecast and its inputs" />
        </div>
        <figcaption class="figure-caption">
          Chlorophyll maps share one colour range, suited to autumn values.
          <template v-if="nFallback > 0">
            The {{ nFallback }} pixel{{ nFallback > 1 ? 's' : '' }} not observed since the archive began
            {{ nFallback > 1 ? 'are' : 'is' }} forecast from the usual value for the month (hover to see which).
          </template>
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="Chlorophyll from yesterday" :value="`${Math.round(ageShare('1'))}%`"
                  :detail="olderThan3 ? `of pixels; ${fmt(olderThan3)} had to use an observation 4–${oldestAge} days old` : 'of pixels'" />
        <StatTile label="Observed at least once" :value="pctOf(live.pixels_with_history, live.pixels)"
                  :detail="`${fmt(live.pixels_with_history)} of ${fmt(live.pixels)} pixels; the other ${nFallback} use the usual value`" />
        <StatTile label="Temperature" :value="pctOf(live.pixels_with_sst, live.pixels)"
                  :detail="live.sst_range ? `of pixels had last night’s value (${live.sst_range[0].toFixed(1)}–${live.sst_range[1].toFixed(1)} °C)` : 'last night’s temperature was not yet archived'" />
      </div>

      <div class="article mt-8">
        <p>
          One honest detail about timing. The forecast is defined as issued at 20:30 UTC. The chlorophyll for
          {{ longDate(live.latest_chl_date) }} was first downloaded on {{ longDate(retrievedDay) }} at {{ retrievedAt }} UTC<template v-if="beforeSchedule">,
          earlier than the 20:00 UTC delivery time in Copernicus’s published schedule</template>. The inputs are therefore the ones a
          20:30 forecast would have used, unless Copernicus revised them later that day. Step 08 keeps a record of when each file
          was first downloaded, and keeps any later version separately, so that delivery times can be checked rather than assumed.
        </p>
      </div>
    </section>

    <section id="recipe" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The same recipe as training</h2>
        <p>
          A model is only valid on inputs prepared exactly as its training inputs were. The step therefore uses the same shared code as
          steps 02 and 04 on the live data, and checks the points where the two feeds differ:
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>What</th><th>Archive (training)</th><th>Live feed (this step)</th></tr></thead>
          <tbody>
            <tr><td class="font-semibold text-ink-950">Chlorophyll grid</td><td>1 km, 133 × 101</td>
              <td>Same grid; checked coordinate by coordinate before use</td></tr>
            <tr><td class="font-semibold text-ink-950">Temperature grid</td><td>0.05° (≈5 km)</td>
              <td>0.0625° (≈7 km); copied onto the 1 km grid the same way as in step 02</td></tr>
            <tr><td class="font-semibold text-ink-950">Quality rule</td><td>Chlorophyll below 0.01 or above 10 mg/m³ removed</td><td>Same rule</td></tr>
            <tr><td class="font-semibold text-ink-950">Usual value for the month</td><td>2017–2023 median</td>
              <td>The same stored values, saved with the model</td></tr>
            <tr><td class="font-semibold text-ink-950">No observation yet</td><td>Almost never happens</td>
              <td>Forecast falls back to the usual value for the month</td></tr>
            <tr><td class="font-semibold text-ink-950">Versions</td><td>Multi-year archive versions</td>
              <td>CHL {{ live.versions.CHL }}, SST {{ live.versions.SST }}, pinned and recorded with each forecast</td></tr>
          </tbody>
        </table>
      </div>

      <div class="article">
        <p>
          The fallback deserves a word. In training, a pixel with no chlorophyll at all in its history only occurs in the first
          days of the record, so the model has hardly learnt what to do with one. Tested on a winter day, it would forecast such
          pixels about a quarter lower than their usual value. On the live feed, a pixel that has been under cloud since the archive
          began is in that position, so for it the forecast is simply the usual value. On {{ longDate(live.issue_date) }}
          that applied to {{ nFallback }} pixel{{ nFallback === 1 ? '' : 's' }}. Bloom probabilities use the same fallback: the usual
          bloom frequency for the pixel and month.
        </p>
      </div>
    </section>

    <section id="scores" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>How the live forecast has done so far</h2>
        <p>
          Every live forecast issued from {{ longDate(evaluation.first_issue_day) }} has been scored against the near-real-time
          observation of the day it predicted, up to {{ longDate(evaluation.last_target_day) }}, with the same rules as the 2025 test:
          only days and pixels the satellite actually saw count.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile v-for="h in H" :key="h" :label="days(h)"
                  :value="score(h, 'Forecast model').log_rmse.toFixed(3)"
                  :detail="`typical log error over ${score(h, 'Forecast model').issue_days} issue days; blend rule ${score(h, 'Blend rule').log_rmse.toFixed(3)}, no change ${score(h, 'No change').log_rmse.toFixed(3)}`" />
      </div>

      <figure class="figure">
        <div class="figure-title">The model against the blend rule, live and in the {{ evaluation.test_year }} test</div>
        <div class="figure-subtitle">Reduction in typical log error; dot = estimate, line = 95% range from resampling whole days</div>
        <div class="mt-5">
          <IntervalChart :groups="gainGroups" />
        </div>
        <figcaption class="figure-caption">
          Positive means the model beats the blend rule. Teal: the whole range is above zero. Grey: the range includes zero or lies
          below it. Each panel has its own scale.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Two results, one expected and one not. The model is clearly better than “no change”, by
          {{ Math.round(Math.min(...H.map(vsNoChange))) }}–{{ Math.round(Math.max(...H.map(vsNoChange))) }}% at every lead time, much as in
          the test.
          <template v-if="allBehind">
            But it is <strong>behind the blend rule</strong>, by {{ Math.round(Math.min(...behindRange)) }}–{{ Math.round(Math.max(...behindRange)) }}%<template v-if="clearlyBehind.length">,
            clearly so at {{ clearlyBehind.map(days).join(' and ') }}</template>, where in {{ evaluation.test_year }} it was ahead at every lead time.
          </template>
          <template v-else>
            Against the blend rule, the live gains are {{ H.map((h) => `${signed(gainOf(h).gain)} at ${days(h)}`).join(', ') }}, against
            {{ H.map((h) => signed(testGainOf(h).gain)).join(', ') }} in {{ evaluation.test_year }}.
          </template>
        </p>
        <p>
          <router-link v-if="step11" :to="stepPath(step11)" class="font-semibold text-teal-800 hover:underline">Step 11</router-link><span v-else>Step 11</span>
          looks for the reason. It is not the live data, which turns out to match the archive almost exactly, and it is not the season.
          The model wins on most days but loses heavily on a few days of sudden change, when chlorophyll jumps or drops by a quarter or
          more overnight. A few weeks of one autumn are still a small sample, and the ranges above treat neighbouring days as independent,
          so they are, if anything, too narrow.
        </p>
      </div>

      <div v-if="hedgeTest" class="article mt-8">
        <h3 class="text-lg font-semibold text-ink-950">A hedge, on trial from {{ longDate(hedgeTest.test_from) }}</h3>
        <p>
          One remedy needs no new data: average the model’s forecast and the blend rule’s, on the log scale
          (<router-link v-if="step12" :to="stepPath(step12)" class="font-semibold text-teal-800 hover:underline">step 12</router-link><span v-else>step 12</span>).
          On the archive it gives up a little of the model’s gain in a normal year and limits the damage on days like the ones above. Because
          those days prompted it, it is judged only on forecasts issued from {{ longDate(hedgeTest.test_from) }}, alongside the model and the
          blend rule.
        </p>
        <p>
          The rule, fixed before the trial: once the 1-day forecast has {{ hedgeTest.decision_days }} scored issue days, publish the hedge or
          the blend rule instead of the model only if its gain over the model has a 95% range above zero (the larger gain if both do);
          otherwise keep the model.
        </p>
        <p class="font-semibold text-ink-950">{{ hedgeTest.decision.text }}</p>
      </div>

      <div v-if="hedgeTest && hedgeDays > 0" class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>Lead time</th><th class="text-right">Issue days</th><th class="text-right">Model</th>
            <th class="text-right">Hedge</th><th class="text-right">Blend rule</th></tr></thead>
          <tbody>
            <tr v-for="h in H" :key="h">
              <td class="font-semibold text-ink-950">{{ days(h) }}</td>
              <td class="num">{{ hedgeScore(h, 'Forecast model')?.issue_days ?? 0 }}</td>
              <td v-for="m in ['Forecast model', 'Hedge', 'Blend rule']" :key="m" class="num">
                {{ hedgeScore(h, m)?.log_rmse != null ? hedgeScore(h, m).log_rmse.toFixed(3) : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">Typical log error on the trial’s issue days; lower is better.</p>
      </div>
    </section>

    <section v-if="blooms" id="blooms" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Live bloom forecasts</h2>
        <p>
          Each live run now also gives the chance of a bloom, meaning chlorophyll at least 1.6 × the usual value for the month, from the
          <router-link :to="stepPath(step10)" class="font-semibold text-teal-800 hover:underline">step 10</router-link> bloom model.
          A warning is a probability at or above the threshold chosen in step 10.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Chance of a bloom, issued {{ longDate(live.issue_date) }}</div>
        <div class="figure-subtitle">Bloom model (step 10), from the same inputs as the chlorophyll forecast</div>
        <div class="mt-5">
          <GridMap :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea" :layers="bloomLayers"
                   aria-label="Live bloom probability forecast" />
        </div>
        <figcaption class="figure-caption">
          The step 10 test found the model’s high probabilities too high: read anything above about 30% as “likely”, not as an exact chance.
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile v-for="h in H" :key="h" :label="`Warning area, ${days(h)}`"
                  :value="`${blooms.area_warned_pct[h].toFixed(1)}%`"
                  :detail="`of pixels at or above ${Math.round(100 * blooms.thresholds[h])}%; highest ${Math.round(blooms.highest_pct[h])}%`" />
      </div>

      <template v-if="bloomGroups.length">
        <div class="article mt-8">
          <p>
            Scored in the same way as the chlorophyll forecasts, over the same days, blooms made up
            {{ bloomScore(1, 'Bloom model').bloom_pct.toFixed(1) }}–{{ bloomScore(7, 'Bloom model').bloom_pct.toFixed(1) }}% of observed
            pixel-days, close to the 2024–2025 rate. Each method is compared with the usual bloom frequency for the pixel and month, using
            the Brier score (the mean squared difference between probability and outcome).
          </p>
        </div>

        <figure class="figure">
          <div class="figure-title">Live bloom probabilities against the usual frequency</div>
          <div class="figure-subtitle">Reduction in the Brier score; dot = estimate, line = 95% range from resampling whole days</div>
          <div class="mt-5">
            <IntervalChart :groups="bloomGroups" />
          </div>
          <figcaption class="figure-caption">
            Positive means better than simply using the usual frequency. Each panel has its own scale.
          </figcaption>
        </figure>

        <div class="article">
          <p>
            So far the usual frequency has been the best bloom forecast at 1 and 4 days: both the model and the anomaly rule, which react
            to the latest observation, did worse, and about {{ Math.round(bloomScore(1, 'Bloom model').false_alarm_pct) }}% of the model’s
            1-day warnings were false alarms. At 7 days the model is level with the usual frequency. This is the same pattern as the chlorophyll
            forecasts: in an autumn of sudden changes, a high reading was often followed by a fall. Until a longer record says otherwise, the
            bloom maps are an experiment, not a warning service.
          </p>
        </div>
      </template>
    </section>

    <section id="next" class="mt-14 scroll-mt-24 article">
      <h2>What still needs checking</h2>
      <ol>
        <li><strong>A longer live score.</strong> Re-run this step every week or two; the ranges narrow as days accumulate. The score that matters
          most will come after a winter and spring, when chlorophyll is highest and changes fastest.</li>
        <li><strong>Sudden changes.</strong> The live losses come from a few days of rapid change (step 11). Step 05 found that daily wind
          adds little on average; whether wind <em>events</em>, a few days of strong wind that mix the water, announce these changes has not
          yet been tested. Another option is to hedge the model’s forecast towards the blend rule’s.</li>
        <li><strong>Delivery times.</strong> Use the download times recorded by step 08 to check how often chlorophyll really
          arrives before 20:30 UTC, the margin every forecast depends on.</li>
        <li><strong>Version changes.</strong> The archive chlorophyll version used for training retires on 24 November 2026 (step 01), and the
          live gap-filled chlorophyll and temperature versions on 12 January 2027. The live versions are pinned, so each switch is a decision
          to be checked, not something that happens unnoticed.</li>
      </ol>
      <p>
        Until those checks are done, the live forecast is a working demonstration, not a validated service.
      </p>
      <div class="mt-6 flex flex-wrap gap-3">
        <router-link :to="stepPath(step08)" class="button-light">Step 08 · Live data archive</router-link>
        <router-link v-if="step11" :to="stepPath(step11)" class="button-light">Step 11 · {{ step11.title }}</router-link>
      </div>
    </section>
  </StepLayout>
</template>
