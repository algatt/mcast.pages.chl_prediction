<script setup>
import nb05 from '../data/nb05.json'
import StepLayout from '../components/StepLayout.vue'
import LineChart from '../components/LineChart.vue'
import GainTable from '../components/GainTable.vue'
import IntervalChart from '../components/IntervalChart.vue'
import BlendBars from '../components/BlendBars.vue'
import StatTile from '../components/StatTile.vue'

const H = [1, 4, 7]
const CLIM = 'Climatology (2017–2023)'

const testRow = (h, method) => nb05.test.find((r) => r.horizon === `+${h}d` && r.method === method)
const valRow = (h, method) => nb05.validation.find((r) => r.horizon === `+${h}d` && r.method === method)
const interval = (h, baseline) => nb05.intervals.find((r) => r.horizon === `+${h}d` && r.baseline === baseline)
const logRmse = (h, method) => testRow(h, method)['RMSE (log10)']
const asPct = (log) => Math.round((10 ** log - 1) * 100)

const coefficients = nb05.damped_coefficients
const settings = nb05.model_settings

// Test chart
const METHODS = [
  { name: 'Persistence', label: 'No change', color: '#9e9b93' },
  { name: CLIM, label: 'Usual value', color: '#2a78d6' },
  { name: 'Damped persistence', label: 'Blend', color: '#eb6834' },
  { name: 'Forecast model', label: 'Model', color: '#0d9488' },
]
const testSeries = METHODS.map((m) => ({
  name: m.label,
  color: m.color,
  points: H.map((h) => ({ x: h, y: logRmse(h, m.name) })),
}))

// Validation: input sets
const featureSets = [
  { name: 'Core: CHL history + season + location', label: 'Chlorophyll history, season, location', note: '8 inputs' },
  { name: 'Core + climatology', label: '+ usual value for the month', note: '9 inputs' },
  { name: 'Core + climatology + SST', label: '+ sea temperature', note: '11 inputs · chosen', emphasis: true },
  { name: 'All 21 features', label: '+ wind', note: '21 inputs' },
]
const validationRows = featureSets.map((f) => ({
  label: f.label,
  note: f.note,
  emphasis: f.emphasis,
  values: Object.fromEntries(H.map((h) => [h, valRow(h, f.name)['Log RMSE gain vs best baseline (%)']])),
}))

// Training years experiment
const eraMethods = ['Climatology', 'Damped persistence', 'Core + SST', 'Core + climatology + SST']
const eraLabels = {
  Climatology: 'Usual value for the month',
  'Damped persistence': 'Blend rule',
  'Core + SST': 'Model without the usual-value input',
  'Core + climatology + SST': 'Model as finally chosen',
}
const era = (method, years) => nb05.era.find((r) => r.method === method && r.years === years).log_rmse
const eraChange = (method, h) => 100 * (era(method, '2017–2023')[h] / era(method, '2008–2023')[h] - 1)

// Test intervals
const intervalGroups = [
  { baseline: 'Persistence', title: 'Against “no change”' },
  { baseline: CLIM, title: 'Against the usual value for the month' },
  { baseline: 'Damped persistence', title: 'Against the blend rule — the hardest test' },
].map((g) => ({
  title: g.title,
  rows: H.map((h) => {
    const r = interval(h, g.baseline)
    return { label: `+${h} day${h > 1 ? 's' : ''}`, value: r['Log RMSE gain (%)'], low: r['95% interval low'], high: r['95% interval high'] }
  }),
}))
const damped = (h) => interval(h, 'Damped persistence')

// Where the model helps
const groups = ['Winter', 'Spring', 'Summer', 'Autumn', 'High chlorophyll']
const seasonRow = (group, h) => nb05.breakdown.season.find((r) => r.group === group && r.horizon === h)
const seasonRows = groups.map((g) => ({
  label: g === 'High chlorophyll' ? 'High-chlorophyll days' : g,
  note: g === 'High chlorophyll' ? 'at least 1.6 × the usual value' : '',
  values: Object.fromEntries(H.map((h) => {
    const r = seasonRow(g, h)
    return [h, 100 * (1 - r.log_rmse_model / r.log_rmse_damped)]
  })),
}))
const high = (h) => seasonRow('High chlorophyll', h)

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'baselines', label: 'The simple rules to beat' },
  { id: 'model', label: 'The model' },
  { id: 'inputs', label: 'Choosing the inputs' },
  { id: 'years', label: 'Choosing the years' },
  { id: 'test', label: 'The test: 2025' },
  { id: 'where', label: 'Where it helps, and where not' },
  { id: 'verdict', label: 'The verdict' },
]
</script>

<template>
  <StepLayout number="05" :sections="sections">
    <template #lead>
      This is where the forecast is built and judged. A machine-learning model is trained on 2017–2023,
      tuned on 2024, and then tested once on 2025 against three simple rules. The result is a real
      improvement — but a smaller one than “model versus no change” would suggest.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Any forecasting model has to answer one question: is it better than the obvious? So this step first
        defines three simple rules, then trains a model, and scores every method in exactly the same way, on the
        same pixels and days.
      </p>
      <p>
        The score is the <strong>typical error on a log scale</strong> (root-mean-square error of log₁₀ chlorophyll).
        A log scale suits chlorophyll because it varies by a factor of a hundred between summer water and the
        Sicilian coast; an error of 0.1 means the forecast is typically about 26% too high or too low, whatever
        the chlorophyll level. Lower is better, and every comparison below is of this score.
      </p>
      <p>
        Two years are kept away from training. <strong>2024</strong> is used to choose between versions of the model.
        <strong>2025</strong> is used only once, at the end, for the final verdict (step 04).
      </p>
    </section>

    <section id="baselines" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The simple rules to beat</h2>
        <ul>
          <li><strong>No change</strong> (persistence): the forecast is the latest observation. Hard to beat over a day or
            two, as step 03 showed.</li>
          <li><strong>Usual value</strong> (climatology): the median for this pixel and calendar month, from 2017–2023.
            It ignores today completely.</li>
          <li><strong>The blend</strong> (damped persistence): a weighted mix of the two, on the log scale, with three
            numbers per lead time fitted on the training years. The further ahead the forecast, the more it leans on
            the usual value:</li>
        </ul>
      </div>

      <figure class="figure">
        <div class="figure-title">How the blend rule mixes today with the usual value</div>
        <div class="figure-subtitle">Fitted weights for each lead time, training years 2017–2024</div>
        <div class="mt-5">
          <BlendBars :coefficients="coefficients" />
        </div>
        <figcaption class="figure-caption">
          The two weights add up to about one; a small constant completes the rule. Fitted by least squares on log
          chlorophyll.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The blend is the rule that matters most. It costs nothing, needs three numbers per lead time, and already
          captures the main thing a forecaster knows: chlorophyll drifts back towards its usual value. Any model worth
          running has to beat <em>it</em>, not just “no change”.
        </p>
      </div>
    </section>

    <section id="model" class="mt-14 scroll-mt-24 article">
      <h2>The model</h2>
      <p>
        The model is a <strong>gradient-boosted decision-tree ensemble</strong>. A decision tree is a flowchart of yes/no
        questions — “is the latest observation more than 3 days old? is it winter?” — ending in a prediction.
        Boosting builds {{ settings.max_iter }} small trees one after another, each correcting the remaining mistakes of
        the ones before it. It is a standard, well-understood method, it handles missing inputs directly, and it trains
        in a couple of minutes.
      </p>
      <p>
        There is one model per lead time (1, 4 and 7 days), each predicting log₁₀ chlorophyll. Training uses a random
        {{ Math.round(nb05.train_sample_fraction * 100) }}% of the training examples — about 11 million while choosing the
        inputs, about 12 million for the final model — because neighbouring pixels on the same day are nearly copies of each other, and a sample loses little while
        saving a lot of memory. Every day of the training years is still represented.
      </p>
      <p class="text-sm text-slate-500">
        Settings: {{ settings.max_iter }} trees, at most {{ settings.max_leaf_nodes }} leaves each, learning rate
        {{ settings.learning_rate }}, at least {{ settings.min_samples_leaf }} examples per leaf. These were not tuned.
      </p>
    </section>

    <section id="inputs" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Choosing the inputs</h2>
        <p>
          Step 04 prepared 21 inputs. Four versions of the model were trained with more and more of them, and scored
          on 2024 against the best of the three simple rules (at every lead time, that is the blend).
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Improvement over the best simple rule, 2024</div>
        <div class="figure-subtitle">Reduction in typical log error; each row adds inputs to the one above</div>
        <div class="mt-5">
          <GainTable :rows="validationRows" />
        </div>
        <figcaption class="figure-caption">
          Validation year 2024, about 2.5 million scored forecasts per lead time.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Chlorophyll history, season and location give about half of the gain at 1 day, but nothing beyond the blend
          at 4 and 7 days. Adding the usual-value input on its own changes little: with location and season, the model
          can already learn it. <strong>Sea temperature</strong> is what lifts every lead time, as step 03 suggested.
          <strong>Wind</strong> adds about one more percentage point at 1 day and nothing at 4 days, while making a live
          forecast depend on a third data feed. The final model therefore uses the 11 inputs without wind.
        </p>
      </div>
    </section>

    <section id="years" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Choosing the years</h2>
        <p>
          Step 01 downloaded data back to 2008, and step 03 showed that chlorophyll before 2017 was generally higher. So
          is more history better, or misleading? Every method was trained twice — on 2008–2023 and on 2017–2023 — and
          scored on 2024.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Typical log error on 2024, by training years</div>
        <div class="figure-subtitle">2008–2023 → 2017–2023, and the change; lower is better</div>
        <div class="mt-5 overflow-x-auto">
          <table class="data-table">
            <thead><tr><th>Method</th><th v-for="h in H" :key="h" class="text-right">+{{ h }} day{{ h > 1 ? 's' : '' }}</th></tr></thead>
            <tbody>
              <tr v-for="m in eraMethods" :key="m">
                <td class="font-semibold text-ink-950">{{ eraLabels[m] }}</td>
                <td v-for="h in H" :key="h" class="num whitespace-nowrap">
                  <span class="text-slate-500">{{ era(m, '2008–2023')[h].toFixed(3) }} →</span>
                  <span class="font-semibold text-ink-950"> {{ era(m, '2017–2023')[h].toFixed(3) }}</span>
                  <span class="block text-[11px]" :class="eraChange(m, h) < 0 ? 'text-teal-700' : 'text-slate-500'">
                    {{ eraChange(m, h) < 0 ? '▼' : '▲' }} {{ Math.abs(eraChange(m, h)).toFixed(1) }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <figcaption class="figure-caption">
          Same 2024 validation forecasts throughout; a 30% sample of each training period, so the 2017–2023 runs had about
          half as many examples.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          With half the data, the recent years do as well or better for every method, and the simple rules gain most:
          the usual value from recent years is 5% better, simply because “normal” has moved. So the final model, its
          monthly usual value and its blend rule all use <strong>2017 onwards</strong>. For the final test, 2024 is then
          added to the training data.
        </p>
      </div>
    </section>

    <section id="test" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The test: 2025</h2>
        <p>
          With the inputs and years fixed, the model is retrained on 2017–2024 and scored, once, on 2025 — about 2.8
          million forecasts per lead time, none of which it had seen.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Typical error by lead time, 2025</div>
        <div class="figure-subtitle">Root-mean-square error of log₁₀ chlorophyll; lower is better</div>
        <div class="mt-4">
          <LineChart :series="testSeries" :x-domain="[1, 7]" :y-domain="[0.08, 0.14]"
                     :x-ticks="H.map((h) => ({ value: h, label: `+${h} day${h > 1 ? 's' : ''}` }))"
                     :y-ticks="[0.08, 0.1, 0.12, 0.14]" :y-format="(v) => v.toFixed(2)"
                     :value-format="(v) => `${v.toFixed(4)} (≈${asPct(v)}%)`"
                     :x-format="(h) => `${h} day${h > 1 ? 's' : ''} ahead`" :height="270"
                     aria-label="Line chart of typical forecast error at 1, 4 and 7 days for four methods" />
        </div>
        <figcaption class="figure-caption">
          The vertical axis starts at 0.08 to show the differences. Hover for each value and its equivalent typical
          percentage error.
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile v-for="h in H" :key="h" :label="`+${h} day${h > 1 ? 's' : ''}`"
                  :value="`${testRow(h, 'Forecast model')['Median relative error (%)'].toFixed(0)}%`"
                  :detail="`median error of the model; typical log error ${logRmse(h, 'Forecast model').toFixed(3)} (≈${asPct(logRmse(h, 'Forecast model'))}%)`" />
      </div>

      <div class="article mt-8">
        <p>
          Half of the model’s forecasts are within about {{ testRow(1, 'Forecast model')['Median relative error (%)'].toFixed(0) }}–{{ testRow(7, 'Forecast model')['Median relative error (%)'].toFixed(0) }}%
          of what the satellite later observed. Its average bias is close to zero (under 0.003 mg/m³). And it is the best of
          the four methods at every lead time. But how much better, and can we be sure?
        </p>
        <p>
          To find out, the 2025 test days are resampled 1,000 times: each time, the year is rebuilt from randomly drawn days
          (some twice, some not at all), and the gain is recomputed. Whole days are drawn rather than pixels, because pixels on
          the same day share the same clouds and weather. The spread of the 1,000 results gives a 95% range for the gain.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">How much better the model is, with uncertainty, 2025</div>
        <div class="figure-subtitle">Reduction in typical log error; dot = estimate, line = 95% range</div>
        <div class="mt-5">
          <IntervalChart :groups="intervalGroups" />
        </div>
        <figcaption class="figure-caption">
          Teal: the whole range is above zero, so the gain is clear. Grey: the range includes zero, so “no gain” cannot be
          ruled out. Each comparison has its own scale.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Against “no change” and against the usual value, the model wins clearly at every lead time. Against the blend
          rule the picture is honest but modest: <strong>{{ damped(1)['Log RMSE gain (%)'].toFixed(1) }}%</strong> better at
          1 day, <strong>{{ damped(4)['Log RMSE gain (%)'].toFixed(1) }}%</strong> at 4 days (only just clear of zero), and
          <strong>{{ damped(7)['Log RMSE gain (%)'].toFixed(1) }}%</strong> at 7 days, where the range
          ({{ damped(7)['95% interval low'].toFixed(1) }} to +{{ damped(7)['95% interval high'].toFixed(1) }}%) includes no gain at all.
        </p>
      </div>
    </section>

    <section id="where" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Where it helps, and where not</h2>
        <p>Breaking the 2025 test down by season shows where the model’s edge over the blend comes from:</p>
      </div>

      <figure class="figure">
        <div class="figure-title">Improvement over the blend rule, by season, 2025</div>
        <div class="figure-subtitle">Reduction in typical log error, by the season of the target day</div>
        <div class="mt-5">
          <GainTable :rows="seasonRows" />
        </div>
        <figcaption class="figure-caption">
          Seasons follow the target day. High-chlorophyll days are those where the observed value is at least 1.6 times the
          usual value for the month; there are about 66,000 of them per lead time.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The model earns its keep in <strong>spring and autumn</strong>, the transitions, when temperature and recent change
          say something the season alone does not. In <strong>winter and summer</strong> it is barely better than the blend
          beyond the first day.
        </p>
        <p>
          On <strong>high-chlorophyll days</strong> it has no advantage at all, and like every rule it underestimates them,
          by about {{ (-high(1).bias_model).toFixed(2) }} mg/m³ on average at 1 day and
          {{ (-high(7).bias_model).toFixed(2) }} mg/m³ at 7 days, with a median error of
          {{ Math.round(high(1).median_rel_err_model) }}–{{ Math.round(high(7).median_rel_err_model) }}%. This is the expected
          weakness of a forecast that, sensibly, leans towards the usual value: blooms are, by definition, unusual.
        </p>
      </div>
    </section>

    <section id="verdict" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The verdict</h2>
      </div>
      <div class="mt-4 grid gap-4">
        <div class="card">
          <div class="font-semibold text-ink-950">1 day ahead: a real, modest improvement</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Clearly better than every simple rule, including the blend ({{ damped(1)['Log RMSE gain (%)'].toFixed(1) }}%,
            range {{ damped(1)['95% interval low'].toFixed(1) }} to {{ damped(1)['95% interval high'].toFixed(1) }}%).
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">4 days ahead: marginal</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            A small gain over the blend ({{ damped(4)['Log RMSE gain (%)'].toFixed(1) }}%) that is only just distinguishable from none.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">7 days ahead: not shown to beat the blend</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Better than “no change” and the usual value, but a three-number blend of the two does about as well. For a week
            ahead, the honest advice is to use the blend.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">Blooms: no skill</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Unusually high chlorophyll is underestimated by every method. Forecasting blooms would need a different approach,
            and is outside what this experiment shows.
          </p>
        </div>
      </div>
      <div class="article mt-8">
        <p>
          All of this is for the reprocessed archive, where data is consistent and complete. Step 07 checks whether the model
          still behaves on the near-real-time data a live forecast would actually receive.
        </p>
      </div>
    </section>
  </StepLayout>
</template>
