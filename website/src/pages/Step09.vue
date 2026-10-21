<script setup>
import { computed, ref } from 'vue'
import nb09 from '../data/nb09.json'
import { unpack } from '../data/packed.js'
import { DIVERGING_RAMP } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GainTable from '../components/GainTable.vue'
import IntervalChart from '../components/IntervalChart.vue'
import GridMap from '../components/GridMap.vue'
import StatTile from '../components/StatTile.vue'

const H = [1, 4, 7]
const { grid } = nb09
const rows = grid.latitude.length
const cols = grid.longitude.length
const days = (h) => `+${h} day${h > 1 ? 's' : ''}`
const fmt = (n) => n.toLocaleString('en-GB')
const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`
const asPct = (log) => Math.round((10 ** log - 1) * 100)
const gainOf = (a, b) => 100 * (1 - a / b)

// --- New inputs ------------------------------------------------------------------
const INPUTS = {
  chl_nbr5_yesterday: ['Yesterday’s chlorophyll nearby', 'The average of whatever the satellite saw yesterday in a 5 × 5-pixel square (about 5 km) around the pixel. Fills in when the pixel itself was under cloud.'],
  chl_nbr15_7d: ['The past week, wider area', 'The 7-day average chlorophyll, averaged again over a 15 × 15-pixel square (about 15 km): the state of the surrounding water.'],
  chl_trend_log: ['Rising or falling', 'The latest observation compared with the past week’s average: is chlorophyll going up or down?'],
  chl_anomaly_log: ['Unusual for the time of year', 'The latest observation compared with the usual value for the month: how far from normal is the water now?'],
  sst_anomaly: ['Unusually warm or cool', 'Last night’s sea temperature compared with the usual temperature for the month.'],
  sst_change_7d: ['Warming or cooling', 'Last night’s sea temperature minus its average over the previous week.'],
  coast_distance_km: ['Distance to the coast', 'In km, from the nearest land on the satellite grid. Coastal water behaves differently from the open channel.'],
}
const newInputs = nb09.new_inputs.map((r) => ({ ...r, label: INPUTS[r.name][0], text: INPUTS[r.name][1] }))
const missing = (name) => nb09.new_inputs.find((r) => r.name === name).missing_pct

// --- Screening on 2024 -------------------------------------------------------------
const CANDIDATES = [
  { name: 'A · current inputs', label: 'A · Step 05 inputs', note: '11 inputs, predicts chlorophyll' },
  { name: 'B · current inputs, residual', label: 'B · Step 05 inputs, correcting the blend', note: '11 inputs, predicts the blend’s error' },
  { name: 'C · current + new inputs', label: 'C · With the new inputs', note: '18 inputs, predicts chlorophyll · chosen', emphasis: true },
  { name: 'D · current + new inputs, residual', label: 'D · With the new inputs, correcting the blend', note: '18 inputs, predicts the blend’s error' },
]
const screen = (h, c) => nb09.screening.find((r) => r.horizon === h && r.candidate === c)
const screeningRows = CANDIDATES.map((c) => ({
  label: c.label, note: c.note, emphasis: c.emphasis,
  values: Object.fromEntries(H.map((h) => [h, screen(h, c.name).gain])),
}))

// --- Tuning ----------------------------------------------------------------------------
const settingsOf = (k) => nb09.tuning.find((r) => r.settings === k)
const tuningRows = [0, 1, 2, 3].map((k) => {
  const s = settingsOf(k)
  return {
    label: k === 0 ? 'Step 05 settings' : `Larger model ${k}`,
    note: `${s.max_iter} trees, ${s.max_leaf_nodes} leaves, rate ${s.learning_rate}, ≥${s.min_samples_leaf} per leaf${k === 0 ? ' · kept' : ''}`,
    emphasis: k === 0,
    values: Object.fromEntries(H.map((h) => [h, nb09.tuning.find((r) => r.horizon === h && r.settings === k).gain])),
  }
})

// --- The test: 2025 ------------------------------------------------------------------
const testGain = (h, vs) => nb09.test_gains.find((r) => r.horizon === h && r.vs === vs)
const score = (h, method) => nb09.test_scores.find((r) => r.horizon === h && r.method === method)
const intervalGroups = [
  { vs: 'Current model (step 05)', title: 'Against the step 05 model' },
  { vs: 'Blend rule', title: 'Against the blend rule' },
].map((g) => ({
  title: g.title,
  rows: H.map((h) => {
    const r = testGain(h, g.vs)
    return { label: days(h), value: r.gain, low: r.low, high: r.high }
  }),
}))
const vsStep05 = (h) => testGain(h, 'Current model (step 05)')
const vsBlend = (h) => testGain(h, 'Blend rule')

// --- Where it helps ----------------------------------------------------------------------
const GROUPS = ['Winter', 'Spring', 'Summer', 'Autumn', 'High chlorophyll']
const group = (g, h) => nb09.breakdown.find((r) => r.group === g && r.horizon === h)
const area = (a, h) => nb09.areas.find((r) => r.area === a && r.horizon === h)
const whereRows = [
  ...GROUPS.map((g) => ({
    label: g === 'High chlorophyll' ? 'High-chlorophyll days' : g,
    note: g === 'High chlorophyll' ? 'at least 1.6 × the usual value' : '',
    values: Object.fromEntries(H.map((h) => [h, gainOf(group(g, h).log_rmse_new, group(g, h).log_rmse_step05)])),
  })),
  { label: `Within ${nb09.coast_km} km of the coast`, note: '',
    values: Object.fromEntries(H.map((h) => [h, gainOf(area('coast', h).log_rmse_new, area('coast', h).log_rmse_step05)])) },
  { label: 'Further offshore', note: '',
    values: Object.fromEntries(H.map((h) => [h, gainOf(area('offshore', h).log_rmse_new, area('offshore', h).log_rmse_step05)])) },
]
const high = (h) => group('High chlorophyll', h)

const mapHorizon = ref('4')
const mapView = ref('step05')
const summary = (h) => nb09.maps[h].summary
const mapLayers = computed(() => {
  const m = nb09.maps[mapHorizon.value]
  const layer = (id, label, packed, limit, against) => ({
    id,
    label,
    kind: 'sequential',
    values: unpack(packed, rows, cols),
    decode: (v) => v,
    ramp: [...DIVERGING_RAMP].reverse(),
    domain: [-limit, limit],
    ticks: [-limit, 0, limit],
    tickFormat: (t) => (t === -limit ? `≤−${limit}%` : t === limit ? `≥${limit}%` : '0'),
    legendTitle: `New model vs ${against}, 2025`,
    legendNote: `Blue: new model better. Red: ${against} better.`,
    format: (v) => `${signed(v)} ${v >= 0 ? 'better' : 'worse'} than the ${against}`,
    missingLabel: 'Not forecast, or too few scored days',
    missingLegend: 'Not forecast (step 04) or too few days',
  })
  return [
    layer('step05', 'vs step 05 model', m.gain_vs_step05, 10, 'step 05 model'),
    layer('blend', 'vs blend rule', m.gain_vs_blend, 30, 'blend rule'),
  ]
})

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'ideas', label: 'Four ideas' },
  { id: 'screening', label: 'Screening on 2024' },
  { id: 'tuning', label: 'Bigger is not better' },
  { id: 'test', label: 'The test: 2025' },
  { id: 'where', label: 'Where it helps' },
  { id: 'promotion', label: 'Putting it into use' },
  { id: 'next', label: 'What comes next' },
]
</script>

<template>
  <StepLayout number="09" :sections="sections">
    <template #lead>
      With the live pipeline in place, this step goes back to the model. It tests four ideas for improving
      it on 2024, checks the winner once on 2025, and — because it is clearly better than the step 05 model at
      1 and 4 days — puts it into use for the live forecast.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Step 05 ended with a model that beat the simple blend rule clearly at 1 day, only just at 4 days, and not
        demonstrably at 7. This step asks whether that can be improved without breaking the rules the experiment has kept so far:
      </p>
      <ul>
        <li>the same years for training (2017–2023), choosing (2024) and the final test (2025);</li>
        <li>only data available at 20:30 UTC on the issue day;</li>
        <li>every idea judged against the blend rule, with a 95% range from resampling whole days, as in step 05;</li>
        <li>2025 used once, for the winner only.</li>
      </ul>
      <p>
        The step 05 model and its results are kept unchanged as the record of that step. The new model replaces it only for
        the live forecast, and only after passing the test.
      </p>
    </section>

    <section id="ideas" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Four ideas</h2>
        <h3>1. A stricter quality rule</h3>
        <p>
          Step 04 removed implausibly high chlorophyll values. Looking at the other end showed a handful of values close to
          zero, far below anything the channel produces. Values under {{ nb09.min_plausible_chl }} mg/m³ are now removed too:
          {{ fmt(nb09.removed_by_lower_bound) }} values in 2016–2025, too few to change the map of modelled pixels
          ({{ fmt(nb09.pixels) }}, as before). It is a small clean-up rather than an improvement, and is applied to every candidate below.
        </p>
        <h3>2. Seven new inputs</h3>
        <p>
          The step 05 model sees each pixel on its own: its own history, the season, its position and its temperature. Forecasters
          also look at the neighbourhood and at how things are changing. Seven new inputs, all built from data available at
          issue time, try to give the model the same view:
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">The seven new inputs</div>
        <div class="figure-subtitle">Share missing: over the training years, on modelled pixels</div>
        <div class="mt-4 overflow-x-auto">
          <table class="data-table">
            <thead><tr><th>Input and what it measures</th><th class="text-right">Missing</th></tr></thead>
            <tbody>
              <tr v-for="r in newInputs" :key="r.name">
                <td>
                  <span class="block font-semibold text-ink-950">{{ r.label }}</span>
                  <span class="block mt-0.5 text-sm text-slate-600">{{ r.text }}</span>
                </td>
                <td class="num">{{ r.missing_pct < 0.05 ? '0%' : `${r.missing_pct.toFixed(1)}%` }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <figcaption class="figure-caption">
          Missing values are left missing: the model handles them directly (step 05). The temperature inputs are missing on
          cloudy nights, as last night’s temperature is in step 04.
        </figcaption>
      </figure>

      <div class="article">
        <h3>3. Correcting the blend instead of starting from scratch</h3>
        <p>
          The step 05 model predicts chlorophyll directly, and has to rediscover what the blend rule already knows. An alternative
          is to let the blend make the forecast and train the model only on <em>its error</em>: the model then adds a correction
          where it has something to say, and leaves the blend alone where it has not. This is a common technique, and worth testing.
        </p>
        <h3>4. Light tuning</h3>
        <p>
          The step 05 settings were never tuned. The best of the candidates is tried with three larger versions of the model.
        </p>
      </div>
    </section>

    <section id="screening" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Screening on 2024</h2>
        <p>
          Ideas 2 and 3 give four candidates. Each is trained on 2017–2023 and scored on 2024 against the blend rule. The rule for
          choosing the winner was fixed before looking: the highest average gain over the three lead times.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Improvement over the blend rule, 2024</div>
        <div class="figure-subtitle">Reduction in typical log error, four candidate models</div>
        <div class="mt-5">
          <GainTable :rows="screeningRows" />
        </div>
        <figcaption class="figure-caption">
          Validation year 2024; each model trained on a 30% sample of 2017–2023. Candidate A is the step 05 recipe retrained with
          the stricter quality rule, so it shows what the other ideas add.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          <strong>The new inputs help at every lead time</strong>: candidate C beats A by about
          {{ (screen(1, CANDIDATES[2].name).gain - screen(1, CANDIDATES[0].name).gain).toFixed(1) }} percentage points at 1 day and
          {{ (screen(4, CANDIDATES[2].name).gain - screen(4, CANDIDATES[0].name).gain).toFixed(1) }} at 4 days. At 4 days its whole
          95% range ({{ signed(screen(4, CANDIDATES[2].name).low) }} to {{ signed(screen(4, CANDIDATES[2].name).high) }}) is above
          zero, which candidate A — the step 05 recipe — does not manage.
        </p>
        <p>
          <strong>Correcting the blend does not help</strong>: B is worse than A, and D worse than C, at 1 and 4 days, and neither is better at 7. The blend is
          a straight line on the log scale; a model that starts from it seems to spend its effort undoing that line rather than
          improving on it. The idea is dropped.
        </p>
      </div>
    </section>

    <section id="tuning" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Bigger is not better</h2>
        <p>Candidate C was then trained with larger settings: more trees, bigger trees, a faster learning rate.</p>
      </div>

      <figure class="figure">
        <div class="figure-title">Candidate C with different settings, 2024</div>
        <div class="figure-subtitle">Reduction in typical log error over the blend rule</div>
        <div class="mt-5">
          <GainTable :rows="tuningRows" />
        </div>
      </figure>

      <div class="article">
        <p>
          Doubling the trees gains a fraction at 1 day and loses at 4 and 7 days; the two largest versions lose at 4 and 7 days, and at
          7 days do worse than the blend itself. Larger models fit the training years more closely, including their day-to-day noise, and that does
          not carry over to a new year. By the same pre-set rule, the <strong>step 05 settings are kept</strong>.
        </p>
      </div>
    </section>

    <section id="test" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The test: 2025</h2>
        <p>
          The winner — the step 05 recipe with the seven new inputs and the stricter quality rule, {{ nb09.n_inputs }} inputs in all —
          was retrained on 2017–2024 and scored once on 2025, on exactly the same pixel-days as the step 05 model and the blend rule:
          about {{ (score(1, 'New model').n / 1e6).toFixed(1) }} million per lead time.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile v-for="h in H" :key="h" :label="days(h)"
                  :value="score(h, 'New model').log_rmse.toFixed(3)"
                  :detail="`typical log error (≈${asPct(score(h, 'New model').log_rmse)}%); step 05 model ${score(h, 'Current model (step 05)').log_rmse.toFixed(3)}, blend ${score(h, 'Blend rule').log_rmse.toFixed(3)}`" />
      </div>

      <figure class="figure">
        <div class="figure-title">How much better the new model is, with uncertainty, 2025</div>
        <div class="figure-subtitle">Reduction in typical log error; dot = estimate, line = 95% range from resampling whole days</div>
        <div class="mt-5">
          <IntervalChart :groups="intervalGroups" />
        </div>
        <figcaption class="figure-caption">
          Teal: the whole range is above zero. Grey: the range includes zero. Each comparison has its own scale.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Against the step 05 model, the gain is small but clear at 1 day ({{ signed(vsStep05(1).gain) }}, range
          {{ signed(vsStep05(1).low) }} to {{ signed(vsStep05(1).high) }}) and 4 days ({{ signed(vsStep05(4).gain) }}), and too small to
          tell at 7 days ({{ signed(vsStep05(7).gain) }}). Small, because the two models agree on most pixels most of the time; clear,
          because the gain holds up however the days are resampled.
        </p>
        <p>
          Against the blend rule, the test that matters, the picture improves at every lead time: {{ signed(vsBlend(1).gain) }} at
          1 day, {{ signed(vsBlend(4).gain) }} at 4 days, and {{ signed(vsBlend(7).gain) }} at 7 days. For the first time the 7-day range
          ({{ signed(vsBlend(7).low) }} to {{ signed(vsBlend(7).high) }}) stays above zero — only just, so the 7-day gain is real
          but slight.
        </p>
      </div>
    </section>

    <section id="where" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Where it helps</h2>
        <p>Splitting the 2025 test shows where the gain over the step 05 model comes from:</p>
      </div>

      <figure class="figure">
        <div class="figure-title">Improvement over the step 05 model, 2025</div>
        <div class="figure-subtitle">Reduction in typical log error, by season of the target day and by area</div>
        <div class="mt-5">
          <GainTable :rows="whereRows" />
        </div>
        <figcaption class="figure-caption">
          Same 2025 test as above, re-run for this page and checked against the saved scores. About {{ fmt(high(1).n) }}
          high-chlorophyll pixel-days and {{ fmt(area('coast', 1).n) }} coastal pixel-days per lead time.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          At 1 day the gain is spread across every season and area. At 4 days it comes mostly from winter, spring and autumn; at
          7 days only autumn still shows a gain worth mentioning. On <strong>high-chlorophyll days</strong> nothing has changed: the new model
          underestimates them by {{ (-high(1).bias_new).toFixed(2) }}–{{ (-high(7).bias_new).toFixed(2) }} mg/m³ on average, like the
          step 05 model, and at 7 days it does no better than the blend.
        </p>
        <p>
          On the map, the gain is largest in the open water between Malta and Sicily, where chlorophyll changes most from place to
          place and looking at the neighbourhood should help. There is one clear exception: a narrow band a few kilometres off the
          Sicilian coast, where the step 05 model does better at 1 and 4 days. Around Malta and in the south the two models are
          close, with small gains and losses here and there.
        </p>
      </div>

      <figure class="figure">
        <div class="segmented" role="group" aria-label="Lead time">
          <button v-for="h in ['1', '4', '7']" :key="h" type="button" :aria-pressed="mapHorizon === h" @click="mapHorizon = h">+{{ h }} day{{ h === '1' ? '' : 's' }}</button>
        </div>
        <div class="mt-4 figure-title">Where the new model is better, +{{ mapHorizon }} day{{ mapHorizon === '1' ? '' : 's' }} ahead</div>
        <div class="figure-subtitle">Each pixel’s 2025 gain; pixels with fewer than 30 scored days are left blank</div>
        <div class="mt-5">
          <GridMap :key="`gain-${mapHorizon}`" v-model="mapView" :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea"
                   :layers="mapLayers" aria-label="Per-pixel gain of the new model in 2025" />
        </div>
        <figcaption class="figure-caption">
          Better than the step 05 model at {{ Math.round(summary(mapHorizon).better_than_step05_pct) }}% of pixels, and better than the
          blend at {{ Math.round(summary(mapHorizon).better_than_blend_pct) }}%. Note the different colour scales: the gains over the
          step 05 model are much smaller.
        </figcaption>
      </figure>
    </section>

    <section id="promotion" class="mt-14 scroll-mt-24 article">
      <h2>Putting it into use</h2>
      <p>
        The new model passed the test that was set for it, so since 21 October 2026 it makes the live forecast (step 07). Putting
        it into use took three things:
      </p>
      <ul>
        <li><strong>The same recipe everywhere.</strong> The seven new inputs are built by the experiment’s shared code, the same
          code for training and for the live forecast, so the two cannot drift apart.</li>
        <li><strong>A check before switching.</strong> The model file used live is built from the tested one, and is only saved if it
          reproduces the 2025 scores above through the live forecast’s own code: every lead time, the same
          {{ (score(1, 'New model').n / 1e6).toFixed(1) }} million pixel-days, the same score.</li>
        <li><strong>A sanity check on live data.</strong> On the live feed for 20 October 2026, nine in ten of the new model’s forecasts
          were within about 10% of the step 05 model’s: a refinement, not a different forecast.</li>
      </ul>
      <p>
        The step 05 model is kept, unchanged, as the record of steps 05 and 06; the pages for those steps describe it.
      </p>
    </section>

    <section id="next" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What comes next</h2>
      </div>
      <div class="mt-4 grid gap-4">
        <div class="card">
          <div class="font-semibold text-ink-950">A better forecast at every lead time</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Clearly better than the blend at 1 and 4 days ({{ signed(vsBlend(1).gain) }}, {{ signed(vsBlend(4).gain) }}) and, just,
            at 7 days ({{ signed(vsBlend(7).gain) }}). The improvement over step 05 came from what the model can see, not from a
            bigger model.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">Blooms are still missed</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            A forecast trained to be right on average leans towards the usual value, and blooms are by definition unusual. Asking a
            different question — “how likely is a bloom here this week?” — and scoring that directly is the next step (step 10).
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">Live scores still to come</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The archive (step 08) keeps collecting the live data needed to score the new model on the live feed. Those scores will be
            added to step 07 when there are enough days to mean something.
          </p>
        </div>
      </div>
    </section>
  </StepLayout>
</template>
