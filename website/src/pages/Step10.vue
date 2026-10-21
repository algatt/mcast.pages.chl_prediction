<script setup>
import { computed, ref } from 'vue'
import nb10 from '../data/nb10.json'
import { unpack } from '../data/packed.js'
import { BLOOM, BLOOM_RAMP } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GainTable from '../components/GainTable.vue'
import IntervalChart from '../components/IntervalChart.vue'
import GridMap from '../components/GridMap.vue'
import LineChart from '../components/LineChart.vue'
import ReliabilityChart from '../components/ReliabilityChart.vue'
import StatTile from '../components/StatTile.vue'

const H = [1, 4, 7]
const { grid } = nb10
const rows = grid.latitude.length
const cols = grid.longitude.length
const days = (h) => `+${h} day${h > 1 ? 's' : ''}`
const fmt = (n) => Math.round(n).toLocaleString('en-GB')
const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`
const longDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', timeZone: 'UTC' })
const ratio = (10 ** nb10.bloom_anomaly_log10).toFixed(1)

// --- How common are blooms -----------------------------------------------------------
const count = (period, h = 1) => nb10.counts.find((r) => r.period === period && r.horizon === h)
const YEARS = [...new Set(nb10.by_season.map((r) => r.year))]
const SEASONS = ['Winter', 'Spring', 'Summer', 'Autumn']
const seasonCell = (y, s) => nb10.by_season.find((r) => r.year === y && r.season === s)
const yearShare = (y) => nb10.by_year.find((r) => r.year === y).bloom_pct
const cellStyle = (pct) => {
  const k = Math.min(BLOOM_RAMP.length - 1, Math.floor(Math.sqrt(pct / 32) * BLOOM_RAMP.length))
  return { background: BLOOM_RAMP[k], color: k >= 4 ? '#fff' : 'var(--ink-primary, #0f172a)' }
}
const winters = nb10.by_season.filter((r) => r.season === 'Winter' && r.year > 2017)   // 2017: January–February only
const wettest = winters.reduce((a, b) => (b.bloom_pct > a.bloom_pct ? b : a))
const quietest = winters.reduce((a, b) => (b.bloom_pct < a.bloom_pct ? b : a))

const toYear = (d) => {
  const t = new Date(`${d}T00:00:00Z`)
  return t.getUTCFullYear() + (t - Date.UTC(t.getUTCFullYear(), 0, 1)) / (365.25 * 864e5)
}
const areaSeries = [{ name: 'Area in bloom', color: BLOOM, points: nb10.area_series.map((r) => ({ x: toYear(r.date), y: r.share_pct, date: r.date })) }]
const dateOf = Object.fromEntries(areaSeries[0].points.map((p) => [p.x, p.date]))

// --- Screening ------------------------------------------------------------------------------
const METHODS = [
  { name: 'Anomaly rule', label: 'Anomaly rule', note: 'a simple rule: one table per lead time' },
  { name: 'Model in use, as a probability', label: 'Model in use, as a probability', note: 'step 09’s forecast, through a fitted curve' },
  { name: 'Classifier', label: 'Bloom model', note: `trained on blooms directly, ${nb10.n_inputs} inputs · chosen`, emphasis: true },
  { name: 'Classifier + area state', label: 'Bloom model + area state', note: 'adds the area’s last 30 days' },
]
const screen = (h, m) => nb10.screening.find((r) => r.horizon === h && r.method === m)
const screeningRows = METHODS.map((m) => ({
  label: m.label, note: m.note, emphasis: m.emphasis,
  values: Object.fromEntries(H.map((h) => [h, screen(h, m.name).skill])),
}))

// --- The test -----------------------------------------------------------------------------------
const test = (h, m) => nb10.test.find((r) => r.horizon === h && r.method === m)
const intervalGroups = [
  { title: 'Bloom model against the usual frequency', rows: H.map((h) => ({ label: days(h), value: test(h, 'Bloom model').skill, low: test(h, 'Bloom model').low, high: test(h, 'Bloom model').high })) },
  { title: 'Anomaly rule against the usual frequency', rows: H.map((h) => ({ label: days(h), value: test(h, 'Anomaly rule').skill, low: test(h, 'Anomaly rule').low, high: test(h, 'Anomaly rule').high })) },
  { title: 'Bloom model against the anomaly rule — the hardest test', rows: H.map((h) => ({ label: days(h), value: test(h, 'Bloom model').skill_rule, low: test(h, 'Bloom model').rule_low, high: test(h, 'Bloom model').rule_high })) },
]

// --- Reliability ------------------------------------------------------------------------------
const COLORS = { 1: '#0d9488', 4: '#2a78d6', 7: '#eb6834' }
const reliabilitySeries = H.map((h) => ({
  name: days(h),
  color: COLORS[h],
  points: nb10.reliability.filter((r) => r.horizon === h).map((r) => ({ x: r.mean_prob, y: r.observed_freq, n: r.n })),
}))
const band = (h, from) => nb10.reliability.find((r) => r.horizon === h && Math.abs(r.from - from) < 1e-9)

// --- Two days in May --------------------------------------------------------------------
const examples = nb10.examples
const exampleIndex = ref(0)
const example = computed(() => examples[exampleIndex.value])
const exampleView = ref('probability')
const probabilityLayer = (id, label, packed, who) => ({
  id,
  label,
  kind: 'sequential',
  values: unpack(packed, rows, cols),
  decode: (v) => v,
  ramp: BLOOM_RAMP,
  domain: [0, 0.4],
  ticks: [0, 0.1, 0.2, 0.3, 0.4],
  tickFormat: (t) => (t === 0.4 ? '≥40%' : `${Math.round(t * 100)}%`),
  legendTitle: `Bloom probability, ${who}`,
  format: (v) => `${(100 * v).toFixed(v < 0.1 ? 1 : 0)}% chance of a bloom`,
  missingLabel: 'Not forecast (step 04)',
  missingLegend: 'Not forecast (step 04)',
})
const exampleLayers = computed(() => {
  const observed = unpack(example.value.maps.observed, rows, cols)
  return [
    probabilityLayer('probability', 'Bloom model', example.value.maps.probability, 'bloom model'),
    probabilityLayer('rule', 'Anomaly rule', example.value.maps.rule, 'anomaly rule'),
    {
      id: 'observed',
      label: 'What happened',
      kind: 'categorical',
      categoryAt: (r, c) => (observed[r][c] === null ? null : observed[r][c] > 0.5 ? 'bloom' : 'none'),
      categories: {
        bloom: { color: BLOOM, label: `Bloom: at least ${ratio} × the usual value` },
        none: { color: '#d4d2ca', label: 'Observed, no bloom' },
      },
      missingLegend: 'Not observed (cloud) or not forecast',
    },
  ]
})

// --- Warnings -----------------------------------------------------------------------------------
const warning = (h, m) => nb10.warnings.find((r) => r.horizon === h && r.method === m)
const WARNING_METHODS = [
  { name: 'Anomaly rule', label: 'Anomaly rule' },
  { name: 'Bloom model', label: 'Bloom model' },
  { name: 'Model in use, value ≥ 1.6 × usual', label: 'Step 09 forecast value' },
]

// --- Where ---------------------------------------------------------------------------------------
const GROUPS = ['Winter', 'Spring', 'Summer', 'Autumn', 'Within 5 km of the coast', 'Further offshore']
const part = (g, h) => nb10.breakdown.find((r) => r.group === g && r.horizon === h)
const whereRows = GROUPS.map((g) => ({
  label: g,
  note: SEASONS.includes(g) ? `${Math.round((100 * part(g, 1).blooms) / count('test').blooms)}% of 2025’s blooms` : '',
  values: Object.fromEntries(H.map((h) => [h, part(g, h).skill_rule])),
}))

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'blooms', label: 'What counts as a bloom' },
  { id: 'methods', label: 'Rules and models' },
  { id: 'screening', label: 'Screening on 2024' },
  { id: 'test', label: 'The test: 2025' },
  { id: 'reliability', label: 'Are the probabilities honest?' },
  { id: 'may', label: 'Two days in May' },
  { id: 'warnings', label: 'Yes or no warnings' },
  { id: 'verdict', label: 'What it shows' },
]
</script>

<template>
  <StepLayout number="10" :sections="sections">
    <template #lead>
      Steps 05 and 09 forecast how much chlorophyll there will be, and both miss blooms. This step asks a different
      question — how likely is a bloom? — and finds that a model trained for it ranks the risk much better than simple
      rules, but cannot yet turn that into better probabilities.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        A forecast built to be right on average leans towards the usual value. That is the right choice most days, and the
        wrong one on the days that matter most: when chlorophyll is unusually high. This step forecasts the <strong>probability
        of a bloom</strong> at each pixel, 1, 4 and 7 days ahead, and scores those probabilities directly.
      </p>
      <p>
        The score is the <strong>Brier score</strong>: the average squared difference between the probability and what happened,
        counted as 1 for a bloom and 0 otherwise. Lower is better. Results are given as a <strong>skill score</strong>, the %
        reduction in the Brier score compared with a simple rule, with a 95% range from resampling whole days. The rules of the
        experiment are unchanged: train on 2017–2023, choose on 2024, test once on 2025, and only use data available at 20:30 UTC.
      </p>
    </section>

    <section id="blooms" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What counts as a bloom</h2>
        <p>
          A <strong>bloom</strong> here is a pixel-day where the satellite saw chlorophyll at least <strong>{{ ratio }} times the usual
          value</strong> for that pixel and month — the “high-chlorophyll days” of steps 05 and 09. It is a relative definition:
          a doubling in summer, when the water is clearest, counts as much as a doubling in winter.
        </p>
        <p>
          The first thing this step found is how much blooms vary. In the training years, {{ count('train').bloom_pct.toFixed(1) }}% of
          observed pixel-days were blooms; in 2024 and 2025, only {{ count('validation').bloom_pct.toFixed(1) }}% and
          {{ count('test').bloom_pct.toFixed(1) }}%. Most of the difference is winter:
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Share of observed pixel-days that were blooms</div>
        <div class="figure-subtitle">By year and season; winter runs from December of the year before</div>
        <div class="mt-4 overflow-x-auto">
          <table class="data-table">
            <thead><tr><th></th><th v-for="y in YEARS" :key="y" class="!text-center">{{ y }}</th></tr></thead>
            <tbody>
              <tr v-for="s in SEASONS" :key="s">
                <td class="font-semibold text-ink-950">{{ s }}</td>
                <td v-for="y in YEARS" :key="y" class="!p-1">
                  <div class="rounded px-1 py-1.5 text-center text-xs tabular-nums" :style="cellStyle(seasonCell(y, s).bloom_pct)">
                    {{ seasonCell(y, s).bloom_pct.toFixed(1) }}
                  </div>
                </td>
              </tr>
              <tr>
                <td class="font-semibold text-ink-950">Whole year</td>
                <td v-for="y in YEARS" :key="y" class="text-center text-xs tabular-nums font-semibold">{{ yearShare(y).toFixed(1) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <figcaption class="figure-caption">
          Percent of observed pixel-days at least {{ ratio }} × the usual value for the month (2017–2023 normal). 2017–2023 are the
          training years, 2024 the choosing year and 2025 the test year. Winter 2017 is January–February only.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The winter of {{ wettest.year }} had blooms on {{ Math.round(wettest.bloom_pct) }}% of observed pixel-days; the winter of
          {{ quietest.year }}, on {{ quietest.bloom_pct.toFixed(1) }}%. Seen across the whole area, bloom winters stand out clearly:
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Share of the area in bloom, past 30 days</div>
        <div class="figure-subtitle">Observed pixel-days that were blooms, as known at each week’s end</div>
        <div class="mt-4">
          <LineChart :series="areaSeries" :x-domain="[2017, 2026]" :y-domain="[0, 60]" :y-ticks="[0, 20, 40, 60]"
                     :x-ticks="YEARS.map((y) => ({ value: y + 0.5, label: `${y}` }))" :y-format="(v) => `${v}%`"
                     :x-format="(v) => shortDate(dateOf[v]) + ' ' + dateOf[v].slice(0, 4)" :show-end-labels="false"
                     :show-legend="false" :height="220" aria-label="Share of the area in bloom over the past 30 days, 2017–2025" />
        </div>
        <figcaption class="figure-caption">
          Uses only chlorophyll available at the time (one day late), as a forecast would. The peaks are winters.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          This matters for everything that follows. A forecast that learns “how often do blooms happen?” from 2017–2023 has learnt
          from bloom-rich years, and will expect too many in quiet ones. 2024 and 2025 were both quiet.
        </p>
      </div>
    </section>

    <section id="methods" class="mt-14 scroll-mt-24 article">
      <h2>Rules and models</h2>
      <p>Two simple rules, and three ways to build a model:</p>
      <ul>
        <li><strong>Usual frequency</strong>: how often this pixel had a bloom in this calendar month in the training years. It ignores
          today. Every skill score below is measured against it, unless stated otherwise.</li>
        <li><strong>Anomaly rule</strong>: how far from normal is the latest observation? The rule looks up how often a bloom followed,
          in the training years, when the water was that far from normal — one small table per lead time. It is the bloom version
          of the blend rule: cheap, and hard to beat.</li>
        <li><strong>Model in use, as a probability</strong>: step 09’s chlorophyll forecast, turned into a probability by a curve fitted
          to how often a forecast of each size came true.</li>
        <li><strong>Bloom model</strong>: a model of the same kind as step 09’s, with the same {{ nb10.n_inputs }} inputs, trained to
          predict “bloom or not” directly.</li>
        <li><strong>Bloom model + area state</strong>: the same, with two extra inputs from the chart above — how much of the area has
          been in bloom over the past 30 days, and how far from normal it has been — so it can tell a bloom winter from a quiet one.</li>
      </ul>
    </section>

    <section id="screening" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Screening on 2024</h2>
        <p>
          Each was trained on 2017–2023 and scored on 2024. The rule for choosing, fixed in advance: the lowest Brier score averaged over
          the three lead times.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Skill over the usual frequency, 2024</div>
        <div class="figure-subtitle">Reduction in the Brier score; higher is better</div>
        <div class="mt-5">
          <GainTable :rows="screeningRows" />
        </div>
        <figcaption class="figure-caption">
          Validation year 2024, about {{ (count('validation').n / 1e6).toFixed(1) }} million scored forecasts per lead time, of which
          {{ fmt(count('validation').blooms) }} were blooms. The step 09 forecast was refitted on 2017–2023 for this comparison, so
          that it had not seen 2024.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          At 1 day, the bloom model is the best of all ({{ signed(screen(1, 'Classifier').skill) }}). From 4 days on, the anomaly rule
          is better than every model, and at 7 days the models fall below even the usual frequency. Step 09’s forecast, turned into a
          probability, is behind the bloom model at every lead time: a forecast built for the average carries less information about blooms.
        </p>
        <p>
          The area-state inputs did not help: worse than the plain bloom model at every lead time. The models already see how far the
          water is from normal at each pixel; the 30-day area average seems to add noise rather than information. The plain bloom model
          was therefore taken to the test.
        </p>
      </div>
    </section>

    <section id="test" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The test: 2025</h2>
        <p>
          The bloom model and both rules were refitted on 2017–2024 and scored once on 2025: about
          {{ (count('test').n / 1e6).toFixed(1) }} million forecasts per lead time, {{ fmt(count('test').blooms) }} of them blooms.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Skill of bloom probabilities, 2025</div>
        <div class="figure-subtitle">Reduction in the Brier score; dot = estimate, line = 95% range from resampling whole days</div>
        <div class="mt-5">
          <IntervalChart :groups="intervalGroups" />
        </div>
        <figcaption class="figure-caption">
          Teal: the whole range is above zero. Grey: the range includes zero. Each comparison has its own scale.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Both the bloom model and the anomaly rule clearly beat the usual frequency, most at 1 day. But against each other, the bloom
          model is <strong>no better</strong>: {{ signed(test(1, 'Bloom model').skill_rule) }} at 1 day,
          {{ signed(test(4, 'Bloom model').skill_rule) }} at 4 and {{ signed(test(7, 'Bloom model').skill_rule) }} at 7, with ranges
          that include zero.
        </p>
        <p>
          That is only half the story. The Brier score mixes two things: telling bloom pixels from the rest (<em>discrimination</em>),
          and giving probabilities that come true as often as they say (<em>reliability</em>). Discrimination alone is measured by
          the <strong>AUC</strong>: the chance that a randomly chosen bloom got a higher probability than a randomly chosen non-bloom
          (0.5 is guessing, 1 is perfect).
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile v-for="h in H" :key="h" :label="`${days(h)} · AUC`"
                  :value="test(h, 'Bloom model').auc.toFixed(2)"
                  :detail="`bloom model; anomaly rule ${test(h, 'Anomaly rule').auc.toFixed(2)}, usual frequency ${test(h, 'Usual frequency').auc.toFixed(2)}`" />
      </div>

      <div class="article mt-8">
        <p>
          On discrimination, the bloom model is better at every lead time: at 1 day it ranks a bloom above a non-bloom
          {{ Math.round(100 * test(1, 'Bloom model').auc) }}% of the time, against {{ Math.round(100 * test(1, 'Anomaly rule').auc) }}%
          for the rule. So it knows <em>where</em> blooms are more likely. What it gets wrong is <em>how much</em> more likely.
        </p>
      </div>
    </section>

    <section id="reliability" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Are the probabilities honest?</h2>
        <p>
          A reliability diagram groups forecasts by their probability and asks how often each group came true. If forecasts of 20%
          come true 20% of the time, the dot sits on the diagonal.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Bloom model: forecast probability against what happened, 2025</div>
        <div class="figure-subtitle">Observed bloom frequency in each band of forecast probability; square-root scales</div>
        <div class="mt-4">
          <ReliabilityChart :series="reliabilitySeries" aria-label="Reliability diagram of bloom probabilities in 2025 at three lead times" />
        </div>
        <figcaption class="figure-caption">
          Most forecasts are below 5%, where the dots are largest. Below the diagonal: blooms happened less often than forecast.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          At 1 day the model is nearly reliable up to about 30%, and too confident above that. At 4 and 7 days its probabilities
          are squeezed the wrong way at both ends. Its higher forecasts are too high: forecasts of 20–30% came true
          {{ Math.round(100 * band(4, 0.2).observed_freq) }}% of the time at 4 days and {{ Math.round(100 * band(7, 0.2).observed_freq) }}%
          at 7. And its lowest are too low: pixels it gave under 1% bloomed {{ (100 * band(4, 0).observed_freq).toFixed(1) }}% and
          {{ (100 * band(7, 0).observed_freq).toFixed(1) }}% of the time. This is the quiet-year problem from the start of the page. The
          model learnt how often blooms followed from bloom-rich years, and 2025 was not one.
        </p>
        <p>
          The anomaly rule suffers less because it leans on today’s water: in a quiet year few pixels are far from normal, so it gives
          few high probabilities. A model that ranks well but is too confident and a rule that ranks less well but is better
          calibrated end up with about the same score.
        </p>
      </div>
    </section>

    <section id="may" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Two days in May</h2>
        <p>
          The 2025 test day with the most observed blooms was {{ longDate(examples[0].target_date) }}. After two almost completely
          cloudy days, the satellite saw chlorophyll across the area at nearly twice its usual May level: {{ fmt(examples[0].bloom_pixels) }}
          of {{ fmt(examples[0].observed_pixels) }} observed pixels counted as blooms. The gap-filled product (step 01) shows the same
          jump, so it is a real event — a modest one in absolute terms, against May’s low normal, and it lasted about a week.
        </p>
      </div>

      <figure class="figure">
        <div class="segmented" role="group" aria-label="Example day">
          <button v-for="(e, k) in examples" :key="e.target_date" type="button" :aria-pressed="exampleIndex === k" @click="exampleIndex = k">
            {{ shortDate(e.target_date) }}
          </button>
        </div>
        <div class="mt-4 figure-title">Bloom forecast for {{ longDate(example.target_date) }}, issued the evening before</div>
        <div class="figure-subtitle">{{ fmt(example.bloom_pixels) }} of {{ fmt(example.observed_pixels) }} observed pixels were blooms</div>
        <div class="mt-5">
          <GridMap :key="`may-${exampleIndex}`" v-model="exampleView" :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea"
                   :layers="exampleLayers" :aria-label="`Bloom probability map for ${example.target_date}`" />
        </div>
        <figcaption class="figure-caption">
          On blooming pixels, the bloom model gave on average {{ (100 * example.mean_prob_on_blooms).toFixed(1) }}% and the anomaly rule
          {{ (100 * example.rule_prob_on_blooms).toFixed(1) }}%; on the rest, the model gave {{ (100 * example.mean_prob_elsewhere).toFixed(1) }}%.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          On {{ shortDate(examples[0].target_date) }} nothing saw it coming: the newest observations were days old and normal, and every
          method gave blooming pixels a probability of a few percent. No forecast built on yesterday’s satellite image can see a bloom
          that starts under cloud.
        </p>
        <p>
          Three days later, on {{ shortDate(examples[1].target_date) }}, the bloom was in the inputs. Both methods now gave higher
          probabilities where it was, but the anomaly rule went further ({{ (100 * examples[1].rule_prob_on_blooms).toFixed(0) }}% on
          blooming pixels, against {{ (100 * examples[1].mean_prob_on_blooms).toFixed(0) }}% from the model). The model held back, and over
          spring 2025 as a whole the rule did better (see the table at the end of the page).
        </p>
      </div>
    </section>

    <section id="warnings" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Yes or no warnings</h2>
        <p>
          A user may want a warning rather than a probability. A warning is issued when the probability passes a threshold, chosen on
          2024 to make the most of the <em>critical success index</em>: hits divided by hits, misses and false alarms together, a
          standard score for rare events. For comparison, step 09’s chlorophyll forecast is also turned into a warning, issued
          whenever it forecasts at least {{ ratio }} × the usual value.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Bloom warnings, 2025</div>
        <div class="figure-subtitle">Thresholds chosen on 2024</div>
        <div class="mt-4 overflow-x-auto">
          <table class="data-table">
            <thead>
              <tr><th>Lead time</th><th>Method</th><th class="text-right">Blooms caught</th><th class="text-right">Warnings that were wrong</th>
                <th class="text-right">Critical success index</th></tr>
            </thead>
            <tbody>
              <template v-for="h in H" :key="h">
                <tr v-for="(m, k) in WARNING_METHODS" :key="m.name" :class="k === 0 ? 'border-t-2 border-slate-200' : ''">
                  <td class="font-semibold text-ink-950">{{ k === 0 ? days(h) : '' }}</td>
                  <td>{{ m.label }}</td>
                  <td class="num">{{ warning(h, m.name).hit_rate.toFixed(0) }}%</td>
                  <td class="num">{{ warning(h, m.name).false_alarm_ratio.toFixed(0) }}%</td>
                  <td class="num font-semibold">{{ warning(h, m.name).csi.toFixed(1) }}%</td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
        <figcaption class="figure-caption">
          Blooms caught: share of blooms that had a warning. Warnings that were wrong: share of warnings with no bloom. About
          {{ fmt(count('test').blooms) }} blooms per lead time.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Step 09’s forecast, the best value forecast in the experiment, catches {{ warning(1, WARNING_METHODS[2].name).hit_rate.toFixed(0) }}%
          of blooms at 1 day and under {{ Math.ceil(warning(7, WARNING_METHODS[2].name).hit_rate) }}% at 7. A bloom-specific forecast catches
          {{ warning(1, 'Bloom model').hit_rate.toFixed(0) }}–{{ warning(1, 'Anomaly rule').hit_rate.toFixed(0) }}% at 1 day — at the price
          of about {{ Math.round(warning(1, 'Anomaly rule').false_alarm_ratio / 10) * 10 }}% of warnings being wrong. Beyond a day, more than
          eight in ten blooms are missed by every method, and about nine in ten warnings are false.
        </p>
      </div>
    </section>

    <section id="verdict" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What it shows</h2>
      </div>

      <figure class="figure">
        <div class="figure-title">Bloom model against the anomaly rule, by season and area, 2025</div>
        <div class="figure-subtitle">Reduction in the Brier score; positive means the model is better</div>
        <div class="mt-5">
          <GainTable :rows="whereRows" />
        </div>
      </figure>

      <div class="mt-4 grid gap-4">
        <div class="card">
          <div class="font-semibold text-ink-950">Blooms can be forecast a day ahead — by a simple rule</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Knowing how unusual the water is today improves bloom probabilities by {{ Math.round(test(1, 'Anomaly rule').skill) }}% at 1 day
            over the usual frequency. A dedicated model matches this, but does not beat it.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">The model knows where, not how often</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            It ranks bloom risk much better than any rule (AUC {{ test(1, 'Bloom model').auc.toFixed(2) }} against
            {{ test(1, 'Anomaly rule').auc.toFixed(2) }}), but its probabilities are too high in a quiet year, because blooms vary so
            much between years. It beats the rule in summer at every lead time, but loses in spring, the season with most blooms, and
            in winter from 4 days on.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">Where to go from here</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The natural next step is to correct the model’s confidence using recent data, with the rule fixed in advance and checked on
            live data rather than on 2025, which has now been used. Blooms that start under cloud will remain out of reach of any
            forecast built only on satellite chlorophyll.
          </p>
        </div>
      </div>
    </section>
  </StepLayout>
</template>
