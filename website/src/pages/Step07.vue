<script setup>
import nb07 from '../data/nb07.json'
import { unpack } from '../data/packed.js'
import { chlLayer, formatChl, SST_RAMP } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GridMap from '../components/GridMap.vue'
import StatTile from '../components/StatTile.vue'

const { grid, live, archive, earlier } = nb07
const rows = grid.latitude.length
const cols = grid.longitude.length
const map = (name) => unpack(live.maps[name], rows, cols)

const longDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const fmt = (n) => n.toLocaleString('en-GB')
const pctOf = (n, total) => `${((100 * n) / total).toFixed(n / total > 0.995 ? 2 : 0)}%`
const retrievedAt = live.retrieved_utc.slice(11, 16)

const fallback = map('fallback')
const chlRange = { decode: (v) => 10 ** v, domain: [0.02, 0.5], ticks: [0.02, 0.05, 0.1, 0.2, 0.5], tickFormat: (t) => `${t}` }
const forecastLayer = (h, date) => {
  const values = map(`forecast_${h}`)
  return chlLayer({
    id: `f${h}`,
    label: `+${h} day${h > 1 ? 's' : ''}`,
    legendTitle: `Forecast for ${shortDate(date)} (mg/m³)`,
    values,
    ...chlRange,
    missingLabel: 'Not forecast (step 04)',
    missingLegend: 'Not forecast (step 04)',
    describe: (r, c) =>
      values[r][c] === null
        ? { line: 'Not forecast (step 04)' }
        : { line: formatChl(10 ** values[r][c]), note: fallback[r][c] > 0.5 ? 'No recent observation: usual value for the month used' : `forecast for ${longDate(date)}` },
  })
}
const ages = map('age')
const mapLayers = [
  ...live.target_dates.map((d, i) => forecastLayer([1, 4, 7][i], d)),
  chlLayer({ id: 'latest', label: 'Latest obs.', values: map('latest'), ...chlRange,
             legendTitle: 'Latest chlorophyll observed (mg/m³)',
             missingLabel: 'No observation in the last 9 days', missingLegend: 'No recent observation' }),
  {
    id: 'age',
    label: 'Its age',
    kind: 'sequential',
    values: ages,
    decode: (v) => v,
    ramp: ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b'],
    domain: [1, 7],
    ticks: [1, 2, 3, 4, 5, 6, 7],
    legendTitle: 'Age of latest chlorophyll (days)',
    format: (v) => `${Math.round(v)} day${Math.round(v) > 1 ? 's' : ''} old`,
    missingLabel: 'No observation in the last 9 days',
    missingLegend: 'No recent observation',
  },
  {
    id: 'sst',
    label: 'Temperature',
    kind: 'sequential',
    values: map('sst'),
    decode: (v) => v,
    ramp: SST_RAMP,
    domain: [22.5, 25.5],
    ticks: [22.5, 23.5, 24.5, 25.5],
    legendTitle: 'Sea temperature (°C)',
    format: (v) => `${v.toFixed(1)} °C`,
    missingLabel: 'Not observed (cloud)',
  },
]

const ageShare = (k) => ((100 * (live.age_counts[k] || 0)) / live.pixels_with_history)
const olderThan3 = Object.entries(live.age_counts).filter(([k]) => Number(k) > 3).reduce((s, [, v]) => s + v, 0)

// The rolling window problem
const NEEDED = 15
const windows = [
  { label: 'Needed for a full check', days: NEEDED, tone: 'need', note: '7 days of history + 1 day delay + 7 days ahead' },
  { label: 'Offered by Copernicus, 7 Oct 2026', days: 15, tone: 'had', note: '22 Sep – 6 Oct' },
  { label: 'Offered by Copernicus, 19 Oct 2026', days: archive.chl.days, tone: 'short', note: `${shortDate(archive.chl.first)} – ${shortDate(archive.chl.last)}` },
]

const earlierRow = (h, method) => earlier.rows.find((r) => r.horizon === `+${h}d` && r.history === 'Complete' && r.method === method)

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'live', label: 'A real forecast' },
  { id: 'recipe', label: 'The same recipe as training' },
  { id: 'checking', label: 'Checking it takes patience' },
  { id: 'earlier', label: 'An earlier check' },
  { id: 'next', label: 'What still needs checking' },
]
</script>

<template>
  <StepLayout number="07" :sections="sections">
    <template #lead>
      Everything so far used the reprocessed archive. A real forecast has to work from the near-real-time feed,
      published within a day and processed with less information. This step runs the final model on that feed,
      end to end, and sets out what it would take to check it properly.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Step 01 explained that each dataset comes in two versions: the carefully reprocessed multi-year archive used for
        training, and the near-real-time version a live service would receive. Their values and their gaps can differ.
        A model that only works on the archive would be of little use, so this step:
      </p>
      <ol>
        <li>downloads the latest near-real-time chlorophyll and sea temperature;</li>
        <li>builds the model’s 11 inputs from them, exactly as step 04 did for the archive;</li>
        <li>issues a forecast for 1, 4 and 7 days ahead and saves it, with every input it used;</li>
        <li>where enough data exists, re-issues forecasts for past days and scores them against what was later observed.</li>
      </ol>
      <p>
        The first three work. The fourth is limited by how little history the live feed keeps, as explained below.
      </p>
    </section>

    <section id="live" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>A real forecast, issued {{ longDate(live.issue_date) }}</h2>
        <p>
          This is the forecast the final model produced from the near-real-time feed for the evening of
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
          Chlorophyll maps share one colour range, suited to autumn values. The 5 pixels with no observation in the past 9
          days are forecast from the usual value for the month (hover to see which).
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="Chlorophyll from yesterday" :value="`${Math.round(ageShare('1'))}%`"
                  :detail="`of pixels; ${olderThan3} pixels had to use an observation 4–6 days old`" />
        <StatTile label="Recent observation" :value="pctOf(live.pixels_with_history, live.pixels)"
                  :detail="`${fmt(live.pixels_with_history)} of ${fmt(live.pixels)} pixels; the other ${live.pixels - live.pixels_with_history} use the usual value`" />
        <StatTile label="Temperature" :value="pctOf(live.pixels_with_sst, live.pixels)"
                  :detail="`of pixels had last night’s value (${live.sst_range[0].toFixed(1)}–${live.sst_range[1].toFixed(1)} °C)`" />
      </div>

      <div class="article mt-8">
        <p>
          One honest detail about timing. The forecast is defined as issued at 20:30 UTC, but this run was made at
          {{ retrievedAt }} UTC, and the chlorophyll for {{ longDate(live.latest_chl_date) }} was already published by then
          — earlier than the 20:00 UTC delivery time in Copernicus’s published schedule. The inputs are therefore the ones a 20:30 forecast
          would have used, unless Copernicus revised them later that afternoon. Step 08 keeps a record of when each file was
          first downloaded, so that delivery times can be checked rather than assumed.
        </p>
      </div>
    </section>

    <section id="recipe" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The same recipe as training</h2>
        <p>
          A model is only valid on inputs prepared exactly as its training inputs were. The step therefore repeats each rule of
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
            <tr><td class="font-semibold text-ink-950">Quality rule</td><td>Chlorophyll above 10 mg/m³ removed</td><td>Same rule</td></tr>
            <tr><td class="font-semibold text-ink-950">Usual value for the month</td><td>2017–2023 median</td>
              <td>The same stored values, saved with the model</td></tr>
            <tr><td class="font-semibold text-ink-950">No recent observation</td><td>Almost never happens</td>
              <td>Forecast falls back to the usual value for the month</td></tr>
            <tr><td class="font-semibold text-ink-950">Versions</td><td>Multi-year archive versions</td>
              <td>CHL {{ live.versions.CHL }}, SST {{ live.versions.SST }}, recorded with each forecast</td></tr>
          </tbody>
        </table>
      </div>

      <div class="article">
        <p>
          The fallback deserves a word. In training, a pixel with no chlorophyll at all in its history only occurs in the first
          days of the record, so the model has hardly learnt what to do with one. Tested on a winter day, it would forecast such
          pixels about a quarter lower than their usual value. On the live feed, with only a few days of history, a few pixels
          per day can be in that position, so for them the forecast is simply the usual value. On {{ longDate(live.issue_date) }}
          that applied to {{ live.pixels - live.pixels_with_history }} pixels.
        </p>
        <p>
          The step is also built to prepare the inputs a second way, for a batch of days at once, and to check that both ways give
          identical values and identical forecasts (they did on 7 October, the last run long enough for it). That guards against the
          most common error in a live pipeline: preparing inputs slightly differently from training without noticing.
        </p>
      </div>
    </section>

    <section id="checking" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Checking it takes patience</h2>
        <p>
          To score a live forecast, you need its inputs (seven days of history, available a day late) and, a week later, the
          observation it predicted. That is {{ NEEDED }} consecutive days of near-real-time chlorophyll. But Copernicus only keeps a
          short rolling window of the live feed, and does not promise how long:
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Days of near-real-time chlorophyll available</div>
        <div class="figure-subtitle">Against the {{ NEEDED }} days a full retrospective check needs</div>
        <div class="mt-5 space-y-3">
          <div v-for="w in windows" :key="w.label" class="grid grid-cols-1 sm:grid-cols-[15rem_1fr] gap-x-4 gap-y-1 items-center">
            <div class="text-sm"><span class="font-semibold text-ink-950">{{ w.label }}</span>
              <span class="block text-[11px] text-slate-500">{{ w.note }}</span></div>
            <div class="flex items-center gap-2">
              <div class="flex gap-[2px]">
                <span v-for="k in NEEDED" :key="k" class="w-4 sm:w-5 h-5 rounded-sm"
                      :class="k <= w.days ? `day--${w.tone}` : 'day--none'"></span>
              </div>
              <span class="text-xs font-semibold tabular-nums text-ink-950">{{ w.days }}</span>
            </div>
          </div>
        </div>
        <figcaption class="figure-caption">
          Each square is one day of chlorophyll. On 19 October only {{ archive.chl.days }} days were offered, too few for any
          complete check at 7 days.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          So the evaluation part of this step failed on its most recent run — correctly, with a clear message rather than a
          misleading score. The fix is step 08: download each new day once, keep it, and build the history locally. After about
          two weeks of daily runs, this step can score live forecasts properly; after a winter, it can do so in the season where
          forecasts matter most.
        </p>
      </div>
    </section>

    <section id="earlier" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>An earlier check, with the earlier model</h2>
        <p>
          On 7 October 2026, while the live window still held 15 days, this step did score forecasts for
          {{ earlier.n_issue_dates }} issue days ({{ shortDate(earlier.issue_dates[0]) }} – {{ shortDate(earlier.issue_dates[1]) }}).
          That run used the <em>previous</em> version of the model, with {{ earlier.features }} inputs and trained on 2022–2024,
          so its numbers do not describe the final model:
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>Lead time</th><th class="text-right">Issue days scored</th><th class="text-right">Previous model</th>
            <th class="text-right">No change</th></tr></thead>
          <tbody>
            <tr v-for="h in [1, 4, 7]" :key="h">
              <td class="font-semibold text-ink-950">+{{ h }} day{{ h > 1 ? 's' : '' }}</td>
              <td class="num">{{ earlierRow(h, 'Forecast model').issue_dates }}</td>
              <td class="num">{{ earlierRow(h, 'Forecast model').log_rmse.toFixed(3) }}</td>
              <td class="num">{{ earlierRow(h, 'Persistence').log_rmse.toFixed(3) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">
          Typical log error on issue days with a complete 7-day history; lower is better. Scored against near-real-time
          observations.
        </p>
      </div>

      <div class="article">
        <p>
          What this does show is that the pipeline runs on live data and produces sensible forecasts, which beat “no change” on
          those days. What it cannot show is how good the final model is live: a handful of autumn days, with between one and
          seven scored issue days per lead time, is far too little.
        </p>
      </div>
    </section>

    <section id="next" class="mt-14 scroll-mt-24 article">
      <h2>What still needs checking</h2>
      <ol>
        <li><strong>A proper live score.</strong> Re-run this step on the local archive once it covers a few weeks, and again
          after a winter. The scores should be compared with step 05’s 2025 test.</li>
        <li><strong>Live versus archive values.</strong> Once the archive covers the same days (its interim updates run about a
          month behind), compare the two versions directly: how different are the values and the gaps?</li>
        <li><strong>Delivery times.</strong> Use the download times recorded by step 08 to check how often chlorophyll really
          arrives before 20:30 UTC, the margin every forecast depends on.</li>
        <li><strong>Version changes.</strong> The archive versions used for training retire on 24 November 2026 (step 01). The
          replacement needs checking against these results.</li>
      </ol>
      <p>
        Until those checks are done, the live forecast is a working demonstration, not a validated service.
      </p>
    </section>
  </StepLayout>
</template>

<style scoped>
.day--need { background: #07171e; }
.day--had { background: #0d9488; }
.day--short { background: #0d9488; }
.day--none { background: repeating-linear-gradient(135deg, var(--gap-hatch) 0 1px, var(--gap) 1px 5px); }
</style>
