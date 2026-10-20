<script setup>
import nb02 from '../data/nb02.json'
import { chlLayer, SST_RAMP, WIND_RAMP } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GridMap from '../components/GridMap.vue'
import WindFlagChart from '../components/WindFlagChart.vue'
import PassTimeline from '../components/PassTimeline.vue'
import StatTile from '../components/StatTile.vue'

const { grids, example, coverage, together, ranges } = nb02
const retention = nb02.wind_retention

const fmt = (n) => Math.round(n).toLocaleString('en-GB')
const exampleDate = new Date(`${example.date}T00:00:00Z`).toLocaleDateString('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
})

const keptPct = (100 * (retention.ascending.kept + retention.descending.kept))
  / (retention.ascending.before + retention.descending.before)
const landPct = nb02.wind_flags.find((f) => f.flag === 'some_portion_of_wvc_is_over_land').pct

// How many 1 km chlorophyll pixels fit in one cell of each coarser grid.
const pixelsPer = (g) =>
  (g.spacing_deg[0] / grids.chl.spacing_deg[0]) * (g.spacing_deg[1] / grids.chl.spacing_deg[1])
const sstPixels = pixelsPer(grids.sst)
const windPixels = pixelsPer(grids.wind)

const mapLayers = [
  chlLayer({
    id: 'chl',
    label: 'Chlorophyll · 1 km',
    values: example.chl_log1000,
    domain: [0.02, 0.5],
    ticks: [0.02, 0.05, 0.1, 0.2, 0.5],
    tickFormat: (t) => `${t}`,
  }),
  {
    id: 'sst',
    label: 'Temperature · 5 km',
    kind: 'sequential',
    values: example.sst_c100,
    decode: (raw) => raw / 100,
    ramp: SST_RAMP,
    domain: [26, 28.5],
    ticks: [26, 27, 28, 28.5],
    tickFormat: (t, i) => (i === 3 ? '' : `${t}`),
    legendTitle: 'Sea temperature (°C)',
    format: (v) => `${v.toFixed(2)} °C`,
    missingLabel: 'No observation (cloud)',
    nativeGrid: nb02.native_centres.sst,
  },
  {
    id: 'wind',
    label: 'Wind · 12 km',
    kind: 'sequential',
    values: example.wind_ms100,
    decode: (raw) => raw / 100,
    ramp: WIND_RAMP,
    domain: [2.5, 6],
    ticks: [3, 4, 5, 6],
    legendTitle: `Wind speed, ${example.wind_pass_utc} UTC pass (m/s)`,
    format: (v) => `${v.toFixed(1)} m/s`,
    missingLabel: 'No usable measurement',
    missingLegend: 'No usable measurement',
    nativeGrid: nb02.native_centres.wind,
  },
]

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'checks', label: 'First checks' },
  { id: 'wind-qc', label: 'Cleaning the wind' },
  { id: 'timing', label: 'When the wind was measured' },
  { id: 'grid', label: 'One grid for everything' },
  { id: 'result', label: 'What the combined file holds' },
]

const gridRows = [
  { data: 'Chlorophyll', cells: grids.chl.cells, size: '≈ 1 km', per: '1' },
  { data: 'Sea temperature', cells: grids.sst.cells, size: '≈ 5 km', per: `≈ ${Math.round(sstPixels)}` },
  { data: 'Wind', cells: grids.wind.cells, size: '≈ 12 km', per: `≈ ${Math.round(windPixels / 10) * 10}` },
]
</script>

<template>
  <StepLayout number="02" :sections="sections">
    <template #lead>
      Step 01 left us with four files on three different grids, one of them measured twice a day.
      This step checks each file, removes unreliable wind measurements, and puts everything onto the
      same 1 km grid and the same calendar — without inventing any values on the way.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        A forecasting model needs a table where each row is “this pixel, on this day”, and the columns
        are everything we know about it. The downloads are not in that shape yet:
      </p>
      <ul>
        <li>chlorophyll is on a 1 km grid, temperature on a 5 km grid, and wind on a 12 km grid;</li>
        <li>wind comes as two separate files, one per daily satellite pass;</li>
        <li>temperature is in kelvin, and wind arrives with quality flags that have not been applied yet.</li>
      </ul>
      <p>
        The result is a single file, <code>malta_daily_observations.nc</code>, holding every variable on
        the chlorophyll grid for every day from 2008 to 2025. It is about {{ Math.round(nb02.file_mb) }} MB.
      </p>
    </section>

    <section id="checks" class="mt-14 scroll-mt-24 article">
      <h2>First checks: dates and units</h2>
      <p>
        Before combining anything, the step checks that every file has exactly one record per day and no
        missing or duplicated dates. A missing day would silently shift every later step by one day,
        which in a forecasting experiment is the same as cheating or being wrong.
      </p>
      <p>
        It then prints the range of every variable, which is the quickest way to spot nonsense. Two
        things came out of that check:
      </p>
      <ul>
        <li>
          <strong>Temperature is converted from kelvin to degrees Celsius.</strong> It then ranges from
          {{ ranges.sst_c[0].toFixed(1) }} to {{ ranges.sst_c[1].toFixed(1) }} °C, which is plausible
          for this part of the Mediterranean.
        </li>
        <li>
          <strong>One chlorophyll value is {{ fmt(ranges.chl_max_mg_m3) }} mg/m³.</strong> Open-sea values
          here are typically 0.05–2 mg/m³, so this is a failed retrieval, not a bloom. It comes from a
          pixel at the edge of Malta’s coast that was observed only four times in 18 years.
        </li>
      </ul>
      <div class="not-prose callout callout-later">
        <div class="label-caps !text-amber-800">Looking ahead · step 04</div>
        <p class="mt-2 text-sm leading-relaxed text-slate-700">
          The impossible value is left in place here, because this step only combines data. Step 04
          deals with it: it treats chlorophyll above 10 mg/m³ as missing (246 values out of 41 million)
          and leaves out pixels observed fewer than 200 times in the training years, which are mostly
          coastal pixels like this one.
        </p>
      </div>
    </section>

    <section id="wind-qc" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Cleaning the wind</h2>
        <p>
          The wind satellite measures how rough the sea surface looks to its radar, and turns that into a
          wind speed and direction. Each measurement comes with flags that say what might be wrong with it.
          Some flags mean the measurement failed; others are warnings.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Quality flags on wind measurements, 2019–2025</div>
        <div class="figure-subtitle">Share of all {{ fmt(retention.ascending.before + retention.descending.before) }} measurements carrying each flag, both passes</div>
        <div class="mt-5">
          <WindFlagChart :flags="nb02.wind_flags" />
        </div>
        <figcaption class="figure-caption">
          A measurement can carry several flags, so the bars add up to more than 100%. Measurements are
          counted on the satellite’s own 12 km grid, before regridding.
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-2">
        <StatTile label="Kept" :value="`${keptPct.toFixed(0)}%`"
                  detail="of wind measurements pass the quality filter" />
        <StatTile label="Over land, partly" :value="`${landPct.toFixed(0)}%`"
                  detail="of measurements touch land somewhere in their 12 km cell — kept" />
      </div>

      <div class="article mt-8">
        <p>
          Five flags mark a failed or unreliable retrieval, and those measurements are removed. (A sixth
          removal flag, for product monitoring events, never occurs here.) Four are kept, and each of those
          is a judgement call:
        </p>
        <ul>
          <li><strong>Cell partly over land.</strong> In a box this close to Malta and Sicily, almost every
            12 km wind cell touches land somewhere. Removing them would remove most of the data. The cost is
            that some coastal wind values may be less accurate.</li>
          <li><strong>Light wind.</strong> Calm conditions are real and matter for chlorophyll; the flag only
            says direction is hard to measure when the wind is light.</li>
          <li><strong>Noisy radar beam</strong> and <strong>strong wind</strong> are warnings rather than
            failures.</li>
        </ul>
      </div>
    </section>

    <section id="timing" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>When the wind was measured</h2>
        <p>
          Wind is measured at two moments each day, when the satellite passes over: once in the morning and
          once in the evening. The two passes are kept as separate variables rather than averaged, because
          they describe different times of day and are not always both available.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Time of the two wind passes over the study area</div>
        <div class="figure-subtitle">Range of measurement times, 2019–2025 (UTC)</div>
        <div class="mt-5">
          <PassTimeline :passes="nb02.wind_pass_hours_utc" />
        </div>
        <figcaption class="figure-caption">
          Every measurement time falls on the same calendar day as its daily label, which the step checks
          explicitly. Hover over a bar for the exact range.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Keeping the exact measurement time matters later. The evening pass can end after 20:30 UTC, when
          forecasts are issued, and in practice wind data is only published the next morning. So a forecast
          issued on a given evening can use the previous day’s wind but not that evening’s pass. Step 04
          builds that rule in.
        </p>
      </div>
    </section>

    <section id="grid" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>One grid for everything</h2>
        <p>
          To put temperature and wind on the 1 km chlorophyll grid, each chlorophyll pixel takes the value of
          the coarse cell it falls in. Nothing is averaged or smoothed, and a pixel whose coarse cell has no
          value stays empty. The table shows how coarse the other grids are.
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead>
            <tr><th>Data</th><th class="text-right">Native grid (cells)</th><th>Cell size</th><th class="text-right">1 km pixels per cell</th></tr>
          </thead>
          <tbody>
            <tr v-for="g in gridRows" :key="g.data">
              <td class="font-semibold text-ink-950">{{ g.data }}</td>
              <td class="num">{{ g.cells[0] }} × {{ g.cells[1] }}</td>
              <td>{{ g.size }}</td>
              <td class="num">{{ g.per }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <figure class="figure">
        <div class="figure-title">All three variables on the 1 km grid, {{ exampleDate }}</div>
        <div class="figure-subtitle">
          A clear summer day: chlorophyll observed on {{ example.coverage_pct.chl.toFixed(0) }}% of the sea,
          temperature on {{ example.coverage_pct.sst.toFixed(0) }}%, wind on {{ example.coverage_pct.wind.toFixed(0) }}%.
        </div>
        <div class="mt-5">
          <GridMap :latitude="example.latitude" :longitude="example.longitude" :sea="example.sea"
                   :layers="mapLayers" :aria-label="`Collated observations for ${exampleDate}`" />
        </div>
        <figcaption class="figure-caption">
          Temperature and wind appear as blocks because each coarse value is copied to every 1 km pixel
          inside its cell. Tick “Show the original grid” to see the cell edges. Each map has its own colour
          range, chosen for this day.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The blocks are the honest picture. Smoothing them would make the maps prettier and suggest detail
          that was never measured. A model given these values knows, in effect, the temperature of a 5 km
          patch of sea and the wind over a 12 km patch, and nothing finer.
        </p>
      </div>
    </section>

    <section id="result" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What the combined file holds</h2>
        <p>
          The combined file has one layer per variable and day: chlorophyll, temperature, the three wind
          components for each pass, their measurement times and flags, and a simple yes/no layer for each
          source saying whether it has a value. Those yes/no layers become useful inputs later: “was the
          sea visible yesterday?” is information in itself.
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead>
            <tr><th>Variable</th><th>Years</th><th class="text-right">Days with any value</th><th class="text-right">Sea pixel-days with a value</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in coverage" :key="c.name">
              <td class="font-semibold text-ink-950">{{ c.name }}</td>
              <td class="tabular-nums">{{ c.period[0] }}–{{ c.period[1] }}</td>
              <td class="num">{{ fmt(c.days_with_data) }} of {{ fmt(c.days) }} ({{ (100 * c.days_with_data / c.days).toFixed(0) }}%)</td>
              <td class="num">{{ c.sea_pixel_days_pct.toFixed(0) }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="article">
        <p>
          Two things stand out. First, the gaps in different sources do not line up: only
          {{ together.chl_with_sst_pct.toFixed(0) }}% of chlorophyll observations have a temperature value for the
          same pixel and day, and since 2019 only {{ together.chl_with_wind_since_2019_pct.toFixed(0) }}% have
          wind and {{ together.chl_with_all_since_2019_pct.toFixed(0) }}% have all three. A model that required every
          input would throw most of the data away, so later steps keep missing inputs as missing and let the
          model handle them.
        </p>
        <p>
          Second, wind is missing on about two days in five even after 2019. The satellite’s two measurement
          strips do not cross this small box on every pass, and the quality filter removes more. That
          sparseness is one reason wind ends up adding little to the forecast in step 05.
        </p>
      </div>
    </section>
  </StepLayout>
</template>
