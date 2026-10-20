<script setup>
import { computed, ref } from 'vue'
import nb06 from '../data/nb06.json'
import nb05 from '../data/nb05.json'
import { unpack } from '../data/packed.js'
import { chlLayer, formatChl, DIVERGING_RAMP, ERROR_RAMP } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GridMap from '../components/GridMap.vue'
import LineChart from '../components/LineChart.vue'
import StatTile from '../components/StatTile.vue'

const { grid, examples, regions } = nb06
const rows = grid.latitude.length
const cols = grid.longitude.length
const maps = nb06.pixel_maps
const summary = (h) => maps[h].summary

const dateLabel = (date) => new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', timeZone: 'UTC' })
const pct = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`
const asPct = (log) => Math.round((10 ** log - 1) * 100)

// --- Example days ---------------------------------------------------------------
const DAYS = Object.keys(examples)
const day = ref(DAYS[0])
const horizon = ref('1')
const exampleView = ref('forecast')
const example = computed(() => examples[day.value][horizon.value])

const ratioTicks = [-0.3, -0.15, 0, 0.15, 0.3]
const NOT_MODELLED = 'Not forecast: rarely observed coastal pixel (step 04)'
const exampleLayers = computed(() => {
  const forecast = unpack(example.value.forecast, rows, cols)
  const observed = unpack(example.value.observed, rows, cols)
  const ratio = forecast.map((row, r) => row.map((f, c) => (f !== null && observed[r][c] !== null ? f - observed[r][c] : null)))
  const fromLog = { decode: (v) => 10 ** v, domain: [0.03, 1], ticks: [0.03, 0.1, 0.3, 1], tickFormat: (t) => (t === 1 ? '≥1' : `${t}`) }
  return [
    chlLayer({ id: 'forecast', label: 'Forecast', values: forecast, ...fromLog,
               missingLabel: NOT_MODELLED, missingLegend: 'Not forecast (step 04)' }),
    chlLayer({ id: 'observed', label: 'Observed', values: observed, ...fromLog,
               missingLabel: 'Not observed — not scored', missingLegend: 'Not observed, or not forecast' }),
    {
      id: 'error',
      label: 'Error',
      kind: 'sequential',
      values: ratio,
      decode: (v) => v,
      ramp: DIVERGING_RAMP,
      domain: [-0.3, 0.3],
      ticks: ratioTicks,
      tickFormat: (t) => ({ '-0.3': '½×', '-0.15': '', 0: 'right', 0.15: '', 0.3: '2×' }[t] ?? ''),
      legendTitle: 'Forecast ÷ observed',
      legendNote: 'Blue: forecast too low. Red: too high.',
      format: (v) => (Math.abs(v) < 0.005 ? 'About right' : `${Math.round((10 ** Math.abs(v) - 1) * 100)}% too ${v > 0 ? 'high' : 'low'}`),
      missingLabel: 'Not observed — not scored',
      missingLegend: 'Not observed, or not forecast',
      describe(r, c) {
        if (ratio[r][c] === null) return { line: 'Not observed — not scored' }
        const v = ratio[r][c]
        return { line: this.format(v), note: `forecast ${formatChl(forecast[r][c] === null ? NaN : 10 ** forecast[r][c])}, observed ${formatChl(10 ** observed[r][c])}` }
      },
    },
  ]
})
const methodsToday = computed(() => [
  { label: 'Model', value: example.value.log_rmse_model },
  { label: 'Blend rule', value: example.value.log_rmse_damped },
  { label: 'No change', value: example.value.log_rmse_persistence },
])
const bestToday = computed(() => methodsToday.value.reduce((a, b) => (b.value < a.value ? b : a)).label)

// --- Per-pixel maps over 2025 --------------------------------------------------------
const mapHorizon = ref('1')
const pixelView = ref('error')
const pixelLayers = computed(() => {
  const m = maps[mapHorizon.value]
  return [
    {
      id: 'error',
      label: 'Typical error',
      kind: 'sequential',
      values: unpack(m.log_rmse, rows, cols),
      decode: (v) => v,
      ramp: ERROR_RAMP,
      domain: [0, 0.3],
      ticks: [0, 0.1, 0.2, 0.3],
      tickFormat: (t, i) => (i === 3 ? '≥0.3' : `${t}`),
      legendTitle: 'Typical log error, 2025',
      legendNote: '0.1 ≈ 26% too high or low; 0.2 ≈ 58%.',
      format: (v) => `${v.toFixed(3)} (≈${asPct(v)}%)`,
      missingLabel: 'Not forecast, or too few scored days',
      missingLegend: 'Not forecast (step 04) or too few days',
    },
    {
      id: 'gain',
      label: 'Gain over the blend',
      kind: 'sequential',
      values: unpack(m.gain_vs_blend, rows, cols),
      decode: (v) => v,
      ramp: [...DIVERGING_RAMP].reverse(),
      domain: [-15, 15],
      ticks: [-15, 0, 15],
      tickFormat: (t) => (t === -15 ? '≤ −15%' : t === 15 ? '≥ +15%' : '0'),
      legendTitle: 'Model vs blend rule, 2025',
      legendNote: 'Blue: model better. Red: blend better.',
      format: (v) => `${pct(v)} ${v >= 0 ? 'better' : 'worse'} than the blend`,
      missingLabel: 'Not forecast, or too few scored days',
      missingLegend: 'Not forecast (step 04) or too few days',
    },
    {
      id: 'bias',
      label: 'Winter bias',
      kind: 'sequential',
      values: unpack(m.bias_winter, rows, cols),
      decode: (v) => v,
      ramp: DIVERGING_RAMP,
      domain: [-0.04, 0.04],
      ticks: [-0.04, 0, 0.04],
      tickFormat: (t) => (t === 0 ? '0' : `${t > 0 ? '+' : '−'}0.04`),
      legendTitle: 'Mean forecast − observed (mg/m³)',
      legendNote: 'Target days in Dec, Jan and Feb 2025.',
      format: (v) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(3)} mg/m³ (${v >= 0 ? 'too high' : 'too low'})`,
      missingLabel: 'Not forecast, or too few scored days',
      missingLegend: 'Not forecast (step 04) or too few days',
    },
  ]
})

// --- Error by month (from the step 05 re-run) -----------------------------------------
const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const monthSeries = (h) => [
  { name: 'Blend', color: '#eb6834', points: nb05.breakdown.month.filter((r) => r.horizon === h).map((r) => ({ x: r.month, y: r.log_rmse_damped })) },
  { name: 'Model', color: '#0d9488', points: nb05.breakdown.month.filter((r) => r.horizon === h).map((r) => ({ x: r.month, y: r.log_rmse_model })) },
]
const monthOf = (h, m) => nb05.breakdown.month.find((r) => r.horizon === h && r.month === m)
const worstMonth = (h) => nb05.breakdown.month.filter((r) => r.horizon === h).reduce((a, b) => (b.log_rmse_model > a.log_rmse_model ? b : a))
const bestMonth = (h) => nb05.breakdown.month.filter((r) => r.horizon === h).reduce((a, b) => (b.log_rmse_model < a.log_rmse_model ? b : a))
const monthsBlendWins = (h) => nb05.breakdown.month.filter((r) => r.horizon === h && r.log_rmse_damped < r.log_rmse_model).map((r) => MONTH_LONG[r.month - 1])

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'days', label: 'Two days, three forecasts' },
  { id: 'where', label: 'Where the errors are' },
  { id: 'when', label: 'When the errors are' },
  { id: 'lessons', label: 'What the maps add' },
]
</script>

<template>
  <StepLayout number="06" :sections="sections">
    <template #lead>
      Averages hide a lot. This step draws the 2025 forecasts as maps: what an individual forecast looks
      like next to what the satellite then saw, where in the study area the model is reliable, and where
      it is not.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Step 05 scored the model with one number per lead time. Here the same 2025 forecasts are broken down in space
        and time. Two example forecast days show what the model actually produces. Then every pixel gets its own score
        for the whole year, which shows where the model can be trusted, and the year is split by month.
      </p>
      <p>
        All maps use the final model from step 05, re-run on the 2025 test year. The re-run reproduces step 05’s scores
        exactly, so these maps and step 05’s numbers describe the same forecasts.
      </p>
    </section>

    <section id="days" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Two days, three forecasts</h2>
        <p>
          A forecast covers every one of the study area’s pixels, but it can only be checked where the satellite later
          sees the sea. Pick a day and a lead time, then switch between the forecast, what was observed, and the error.
        </p>
      </div>

      <figure class="figure">
        <div class="flex flex-wrap items-center gap-3">
          <div class="segmented" role="group" aria-label="Issue day">
            <button v-for="d in DAYS" :key="d" type="button" :aria-pressed="day === d" @click="day = d">Issued {{ dateLabel(d) }}</button>
          </div>
          <div class="segmented" role="group" aria-label="Lead time">
            <button v-for="h in ['1', '4', '7']" :key="h" type="button" :aria-pressed="horizon === h" @click="horizon = h">+{{ h }} day{{ h === '1' ? '' : 's' }}</button>
          </div>
        </div>
        <div class="mt-4 figure-title">Forecast for {{ dateLabel(example.target_date) }} 2025</div>
        <div class="figure-subtitle">
          Issued {{ dateLabel(day) }} at 20:30 UTC; the satellite later observed {{ example.coverage_pct.toFixed(0) }}% of the area
        </div>
        <div class="mt-5">
          <GridMap :key="`${day}-${horizon}`" v-model="exampleView" :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea"
                   :layers="exampleLayers" :aria-label="`Forecast map issued ${day}, ${horizon} days ahead`" />
        </div>
        <div class="mt-5 grid gap-3 sm:grid-cols-3">
          <div v-for="m in methodsToday" :key="m.label" class="rounded-lg border p-3"
               :class="m.label === bestToday ? 'border-teal-300 bg-teal-50/60' : 'border-slate-200'">
            <div class="label-caps">{{ m.label }}{{ m.label === bestToday ? ' · best today' : '' }}</div>
            <div class="mt-1 text-lg font-semibold text-ink-950 tabular-nums">{{ m.value.toFixed(3) }}</div>
            <div class="text-[11px] text-slate-500">typical log error, ≈{{ asPct(m.value) }}%</div>
          </div>
        </div>
        <figcaption class="figure-caption">
          Scores on this day only, over the {{ example.scored.toLocaleString('en-GB') }} pixels the satellite observed.
          Maps are stored at about 3% precision.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Two things show up. The forecast map is smoother than the observed one: the model predicts the typical value
          for what it knows, not the fine detail of eddies and filaments, which no forecast can know a week ahead. And
          single days vary: in mid-February the model clearly beats both simple rules at +1 and +4 days (at +7 days it ties
          with “no change” and beats the blend by a wide margin), but on 15 August the blend rule does slightly better
          at +1 and +7 days. Step 05’s averages are the fair comparison; a single day
          tells you little.
        </p>
      </div>
    </section>

    <section id="where" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Where the errors are</h2>
        <p>
          Every pixel was forecast on about {{ Math.round(summary('1').median_pairs_per_pixel) }} days of 2025 that the
          satellite could check, enough to give each pixel its own score. Three maps, for +1 or +7 days:
        </p>
        <ul>
          <li><strong>Typical error</strong> — how far off the model usually is at that pixel.</li>
          <li><strong>Gain over the blend</strong> — whether the model beats the three-number blend rule there.</li>
          <li><strong>Winter bias</strong> — whether winter forecasts there are too high or too low on average.</li>
        </ul>
      </div>

      <figure class="figure">
        <div class="segmented" role="group" aria-label="Lead time">
          <button v-for="h in ['1', '7']" :key="h" type="button" :aria-pressed="mapHorizon === h" @click="mapHorizon = h">+{{ h }} day{{ h === '1' ? '' : 's' }}</button>
        </div>
        <div class="mt-4 figure-title">Each pixel’s 2025 score, +{{ mapHorizon }} day{{ mapHorizon === '1' ? '' : 's' }} ahead</div>
        <div class="figure-subtitle">Pixels with fewer than {{ nb06.min_pairs }} scored days are left blank</div>
        <div class="mt-5">
          <GridMap :key="`pixels-${mapHorizon}`" v-model="pixelView" :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea"
                   :layers="pixelLayers" aria-label="Per-pixel forecast scores for 2025" />
        </div>
        <figcaption class="figure-caption">
          Winter bias uses target days in December, January and February only (about
          {{ Math.round(summary('1').median_winter_pairs_per_pixel) }} per pixel).
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="Model beats the blend" :value="`${Math.round(summary('1').pixels_beating_blend_pct)}%`"
                  :detail="`of pixels at +1 day; ${Math.round(summary('7').pixels_beating_blend_pct)}% at +7 days`" />
        <StatTile label="Coast vs open sea" :value="`${(regions['1'].coast_median_error / regions['1'].open_median_error).toFixed(1)}×`"
                  detail="larger typical error along the Sicilian coast than in the open channel, at +1 day" />
        <StatTile label="Winter forecasts too high" :value="`${Math.round(summary('7').winter_bias_share_positive_pct)}%`"
                  :detail="`of pixels at +7 days, by ${summary('7').winter_bias_mean.toFixed(3)} mg/m³ on average`" />
      </div>

      <div class="article mt-8">
        <p>
          <strong>The open channel is where the model works.</strong> There its typical error at +1 day is about
          {{ regions['1'].open_median_error.toFixed(3) }} (≈{{ asPct(regions['1'].open_median_error) }}%), and it beats the
          blend by a median {{ pct(regions['1'].open_median_gain) }}.
          <strong>The Sicilian coast is where it struggles.</strong> Chlorophyll there is higher, patchier and changes faster,
          so errors are larger ({{ regions['1'].coast_median_error.toFixed(3) }}, ≈{{ asPct(regions['1'].coast_median_error) }}%),
          and the model’s edge shrinks to {{ pct(regions['1'].coast_median_gain) }} at +1 day and
          {{ pct(regions['7'].coast_median_gain) }} at +7 days: along the coast, a week ahead, the blend rule is better.
        </p>
        <p>
          This also explains a detail of step 05. Measured pixel by pixel, the typical gain over the blend is
          {{ pct(summary('1').median_pixel_gain) }} at +1 day, higher than step 05’s overall 5.4%. The overall score is weighted
          towards the coastal pixels, whose errors are largest, and that is where the model helps least.
        </p>
        <p>
          The winter bias map shows the pattern step 05 hinted at: winter forecasts are a little too high almost everywhere.
          The model leans towards the usual value, so this is consistent with the 2025 winter being lower than the
          training years’ usual — the same downward drift step 03 found between eras.
        </p>
      </div>
    </section>

    <section id="when" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>When the errors are</h2>
        <p>The same 2025 forecasts, split by the month of the target day:</p>
      </div>

      <div class="grid gap-6 md:grid-cols-2">
        <figure v-for="h in [1, 7]" :key="h" class="figure !my-0">
          <div class="figure-title">+{{ h }} day{{ h > 1 ? 's' : '' }} ahead</div>
          <div class="figure-subtitle">Typical log error by month, 2025</div>
          <div class="mt-3">
            <LineChart :series="monthSeries(h)" :x-domain="[1, 12]" :y-domain="[0.04, 0.18]"
                       :x-ticks="MONTH_SHORT.map((label, i) => ({ value: i + 1, label }))"
                       :y-ticks="[0.04, 0.08, 0.12, 0.16]" :y-format="(v) => v.toFixed(2)"
                       :value-format="(v) => `${v.toFixed(3)} (≈${asPct(v)}%)`"
                       :x-format="(m) => MONTH_LONG[m - 1]" :height="230"
                       :aria-label="`Monthly forecast error for the model and the blend rule, ${h} days ahead`" />
          </div>
        </figure>
      </div>
      <p class="mt-3 text-xs text-slate-500">Lower is better. Hover to compare the two in any month.</p>

      <div class="article mt-8">
        <p>
          The model’s error follows the seasons, highest in {{ MONTH_LONG[worstMonth(1).month - 1] }}
          (≈{{ asPct(worstMonth(1).log_rmse_model) }}% at +1 day) and lowest in {{ MONTH_LONG[bestMonth(1).month - 1] }}
          (≈{{ asPct(bestMonth(1).log_rmse_model) }}%). At +1 day the model is below the blend in
          {{ 12 - monthsBlendWins(1).length }} of the 12 months; the blend edges ahead only in
          {{ monthsBlendWins(1).join(' and ') }}. At +7 days the two lines are close all year, and the blend is better in
          {{ monthsBlendWins(7).length }} months: {{ monthsBlendWins(7).join(', ') }}. The model’s clearest gains come in
          late winter and spring (February to April) and in autumn, the months when chlorophyll is changing.
        </p>
      </div>
    </section>

    <section id="lessons" class="mt-14 scroll-mt-24 article">
      <h2>What the maps add</h2>
      <ul>
        <li><strong>Trust depends on place.</strong> The model is clearly useful in the open channel and around Malta; along the
          Sicilian coast its advantage is small at 1 day and gone at 7.</li>
        <li><strong>Forecasts are smooth.</strong> They give the typical value, not the detailed pattern; small features are not
          forecast.</li>
        <li><strong>Winter runs slightly high.</strong> A consistent, small positive bias in winter, consistent with recent winters
          being lower than the training years.</li>
        <li><strong>Single days are noisy.</strong> On any given day either method can win; only the averages of step 05 decide.</li>
      </ul>
      <p>
        A live forecast should therefore come with this map of reliability, so that users know where it can be trusted.
      </p>
    </section>
  </StepLayout>
</template>
