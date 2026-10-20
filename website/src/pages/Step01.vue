<script setup>
import nb01 from '../data/nb01.json'
import { chlLayer, formatChl, OBSERVED, FILLED } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GridMap from '../components/GridMap.vue'
import DatasetTimeline from '../components/DatasetTimeline.vue'
import ObservedFilledBar from '../components/ObservedFilledBar.vue'
import StatTile from '../components/StatTile.vue'
import YearCoverageChart from '../components/YearCoverageChart.vue'

const { comparison, example } = nb01
const coverageByYear = nb01.l3_coverage_by_year_pct

const fmt = (n) => n.toLocaleString('en-GB')
const exampleDate = new Date(`${example.date}T00:00:00Z`).toLocaleDateString('en-GB', {
  day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
})
const l4Total = comparison.valid_both + comparison.filled_by_l4
const filledPct = (100 * comparison.filled_by_l4) / l4Total

const l3 = example.l3_log1000
const l4 = example.l4_log1000
const chl = (raw) => formatChl(10 ** (raw / 1000))

const mapLayers = [
  chlLayer({ id: 'l3', label: 'L3 · observed', values: l3 }),
  chlLayer({
    id: 'l4',
    label: 'L4 · gap-filled',
    values: l4,
    showMissing: false,
    describe: (r, c) => ({
      line: l4[r][c] === null ? 'No value' : chl(l4[r][c]),
      note: l3[r][c] === null ? 'Interpolated: no satellite observation here' : 'Same pixel was observed in L3',
    }),
  }),
  {
    id: 'filled',
    label: 'What L4 filled in',
    kind: 'categorical',
    categoryAt: (r, c) => (l3[r][c] !== null ? 'observed' : l4[r][c] !== null ? 'filled' : null),
    categories: {
      observed: { color: OBSERVED, label: 'Observed by satellite (L3)' },
      filled: { color: FILLED, label: 'Filled in by interpolation (L4 only)' },
    },
    showMissing: false,
    describe: (r, c) =>
      l3[r][c] !== null
        ? { line: 'Observed by satellite', note: chl(l3[r][c]) }
        : { line: 'Filled in by interpolation', note: l4[r][c] === null ? '' : `L4 value ${chl(l4[r][c])}` },
  },
]

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'l3-l4', label: 'Observed or gap-filled?' },
  { id: 'datasets', label: 'The four datasets' },
  { id: 'two-versions', label: 'Two versions of the same data' },
  { id: 'years', label: 'How many years?' },
  { id: 'reproducible', label: 'Keeping it reproducible' },
]

const delivery = [
  { data: 'Chlorophyll (L3)', archive: 'Reprocessed periodically; interim updates about 31 days behind', live: 'The day after the satellite pass, by 20:00 UTC' },
  { data: 'Sea temperature', archive: 'About one month behind', live: 'The same day, by 12:00 UTC (night-time passes)' },
  { data: 'Wind (ASCAT)', archive: 'Monthly, about 3–4 months behind', live: 'The previous day’s passes, at about 07:00 UTC' },
]

const versions = [
  { data: 'Chlorophyll L3', id: 'cmems_obs-oc_med_bgc-plankton_my_l3-multi-1km_P1D', version: '202411', note: 'Retires 24 Nov 2026' },
  { data: 'Chlorophyll L4', id: 'cmems_obs-oc_med_bgc-plankton_my_l4-gapfree-multi-1km_P1D', version: '202311', note: 'Retires 24 Nov 2026' },
  { data: 'Sea temperature', id: 'cmems_obs-sst_med_phy_my_l3s_P1D-m', version: '202511', note: '' },
  { data: 'Wind, two passes', id: 'cmems_obs-wind_glo_phy_my_l3-metopb-ascat-{asc,des}-0.125deg_P1D-i', version: '202311', note: '' },
]
</script>

<template>
  <StepLayout number="01" :sections="sections">
    <template #lead>
      Before anything can be forecast, we need the right satellite data — and a clear idea of what
      that data really is. This step downloads four datasets for a box of sea around Malta, and
      checks one claim that shapes the whole experiment: that a gap-filled chlorophyll product is
      not the same thing as an observation.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        The study area is a box of sea between Malta and the south coast of Sicily:
        35.55–36.90° N and 13.90–15.20° E. At the resolution of the chlorophyll data, that is a grid of
        133 × 101 pixels, each about 1 km across. {{ fmt(comparison.sea_pixels) }} of those pixels are sea.
      </p>
      <p>It downloads four things from the
        <a href="https://marine.copernicus.eu/" target="_blank" rel="noopener">Copernicus Marine Service</a>,
        the EU’s free ocean-data service:</p>
      <ul>
        <li><strong>Chlorophyll, as observed</strong> (called <em>L3</em>): what the satellites saw each day, with gaps where they could not see. This is what we want to forecast.</li>
        <li><strong>Chlorophyll, gap-filled</strong> (called <em>L4</em>): the same data with every gap filled in by interpolation. We download it only to compare it with L3.</li>
        <li><strong>Sea-surface temperature</strong>, measured at night by satellite.</li>
        <li><strong>Wind</strong>, measured by a satellite radar (ASCAT) on two passes a day.</li>
      </ul>
      <p>
        Satellite products come in different “levels”. Level 3 means individual measurements have been
        turned into a map on a regular grid, but nothing has been invented where there was no
        measurement. Level 4 goes one step further and fills the gaps.
      </p>
    </section>

    <section id="l3-l4" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Observed or gap-filled?</h2>
        <p>
          Ocean-colour satellites measure chlorophyll from the colour of sunlight reflected by the sea.
          Clouds block the view, and so do sun glint and haze. On a typical day a large part of the area
          has no measurement at all. Over 2022–2025, only {{ comparison.l3_share_of_sea_pixel_days_pct.toFixed(0) }}%
          of sea pixels had a valid value on an average day.
        </p>
        <p>
          The map shows one winter day, {{ exampleDate }}. Switch between the views to see what the
          satellites actually observed, what the gap-filled product shows, and which pixels it invented.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Chlorophyll on {{ exampleDate }}</div>
        <div class="figure-subtitle">
          Observed (L3) on {{ example.l3_coverage_pct.toFixed(0) }}% of the sea; gap-filled (L4) everywhere.
        </div>
        <div class="mt-5">
          <GridMap :latitude="example.latitude" :longitude="example.longitude" :sea="example.sea"
                   :layers="mapLayers" :aria-label="`Chlorophyll map for ${exampleDate}`" />
        </div>
        <figcaption class="figure-caption">
          Copernicus Marine multi-sensor products for the Mediterranean, 1 km daily. On this day
          chlorophyll along the Sicilian coast (median 0.67 mg/m³) is about six times that of the open
          channel and the waters around Malta (about 0.11 mg/m³). Land pixels are those the gap-filled
          product never fills.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The gap-filled map looks complete and smooth, which makes it tempting. But the filled pixels
          are estimates, not measurements. To see how much of L4 is real, this step compares the two
          products pixel by pixel, for every day of 2022–2025.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Where every L4 value comes from, 2022–2025</div>
        <div class="figure-subtitle">{{ fmt(l4Total) }} sea pixel-days with an L4 value</div>
        <div class="mt-5">
          <ObservedFilledBar :observed="comparison.valid_both" :filled="comparison.filled_by_l4" />
        </div>
        <figcaption class="figure-caption">
          A pixel-day is one pixel on one day. No pixel-day had an L3 observation but no L4 value.
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="Filled in" :value="`${filledPct.toFixed(0)}%`"
                  detail="of all L4 values have no observation behind them" />
        <StatTile label="Identical" :value="`${comparison.exactly_equal_pct.toFixed(1)}%`"
                  detail="of L4 values equal L3 exactly, where both exist" />
        <StatTile label="Small adjustments" :value="`${comparison.changed_mae.toFixed(4)}`"
                  detail="mg/m³: average change to the remaining few observed values" />
      </div>

      <div class="article mt-8">
        <p>
          So where L4 and L3 overlap, L4 simply <em>is</em> L3. Everything L4 adds is interpolation —
          {{ filledPct.toFixed(0) }}% of its values. That matters in two ways:
        </p>
        <ul>
          <li><strong>Training.</strong> A model trained on L4 would partly learn to reproduce the
            interpolation method, not the ocean.</li>
          <li><strong>Scoring.</strong> Checking a forecast against L4 would partly grade it against
            another estimate. A forecast that resembles the interpolation would look better than it is.</li>
        </ul>
        <p>
          That is the reason for the first ground rule: the experiment forecasts <strong>L3</strong>
          chlorophyll and only scores forecasts on pixels the satellite actually observed. The price is
          fewer days to learn from. L4 is kept only for comparison, in step 07.
        </p>
      </div>
    </section>

    <section id="datasets" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The four datasets</h2>
        <p>
          Chlorophyll history is the main ingredient, but the ocean’s physics may help: temperature
          hints at mixing and the season, and wind stirs the surface layer. The datasets do not cover
          the same years, which limits how they can be combined.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Years covered by each download</div>
        <div class="figure-subtitle">And how the experiment eventually uses them</div>
        <div class="mt-5">
          <DatasetTimeline />
        </div>
        <figcaption class="figure-caption">
          Hover over a bar for resolution and file size. Paler bars: wind was tested and left out of
          the final model (step 05); L4 is used only for comparison. Sizes are for this study area.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The four datasets also come at very different resolutions. Chlorophyll is on a 1 km grid,
          sea temperature on about 5 km, and wind on about 12 km. In step 02 the coarser data is
          copied onto the chlorophyll grid. That makes the tables line up, but it does not create
          detail that was never measured: one temperature value covers about 20 chlorophyll pixels.
        </p>
        <p>
          For wind, the download keeps each measurement’s exact time and quality flags. The time matters
          because a forecast may only use measurements taken before it was issued; the flags let
          step 02 discard measurements that failed the provider’s quality checks.
        </p>
      </div>
    </section>

    <section id="two-versions" class="mt-14 scroll-mt-24 article">
      <h2>Two versions of the same data</h2>
      <p>
        Each dataset exists in two versions. The <strong>multi-year archive</strong> (Copernicus calls it
        “MY”) is carefully reprocessed and consistent over many years, which is what you want for
        training. The <strong>near-real-time</strong> version (“NRT”) is published within hours or a day,
        which is what a live forecast has to use — but it is processed with less information, so its
        values and its gaps can differ slightly.
      </p>
      <p>
        Steps 01–06 use the archive. Step 07 checks the trained model on near-real-time data,
        because a model that only works on reprocessed data would not be much use in practice.
      </p>
      <div class="not-prose overflow-x-auto my-6">
        <table class="data-table">
          <thead>
            <tr><th>Dataset</th><th>Archive (training)</th><th>Near-real-time (live)</th></tr>
          </thead>
          <tbody>
            <tr v-for="d in delivery" :key="d.data">
              <td class="font-semibold text-ink-950">{{ d.data }}</td>
              <td>{{ d.archive }}</td>
              <td>{{ d.live }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        These delivery times decide what a forecast can know. Yesterday’s chlorophyll only arrives at
        about 20:00 UTC, so the experiment issues its forecasts at <strong>20:30 UTC</strong>. At that
        point, today’s sea temperature and yesterday’s wind are also available. Step 04 builds every
        input to respect these delays, even though training uses the archive, where everything is
        available at once.
      </p>
    </section>

    <section id="years" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>How many years?</h2>
        <p>
          The first version of this step downloaded only 2022–2025. That is quick, but it leaves two
          years for training, which is thin for learning how chlorophyll behaves over a year. So the
          download was extended back to 2008 for chlorophyll and temperature. Wind can only go back to
          2019, where its archive starts.
        </p>
        <p>
          More years turned out not to be automatically better. The satellite record is not the same
          throughout: the share of the sea observed each year rises noticeably around 2017, around the
          time a new generation of satellite sensors (Sentinel-3’s OLCI) became part of the merged product.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">How much of the sea the satellites observed, per year</div>
        <div class="figure-subtitle">Share of sea pixel-days with a valid L3 chlorophyll value</div>
        <div class="mt-4">
          <YearCoverageChart :coverage="coverageByYear" :highlight-from="2017" />
        </div>
        <figcaption class="figure-caption">
          The rest of each year is cloud, glint or haze. Hover over a bar for the exact value.
        </figcaption>
      </figure>

      <div class="callout callout-later">
        <div class="label-caps !text-amber-800">Looking ahead · step 05</div>
        <p class="mt-2 text-sm leading-relaxed text-slate-700">
          Step 05 tests this directly. Training on 2017–2023 forecasts 2024 as well as or better than
          training on 2008–2023, with half as much data. The older years also describe higher
          chlorophyll than recent ones, so the final model trains on <strong>2017 onwards</strong>.
          The 2008–2016 download was still worth making: it is the evidence for that decision.
        </p>
      </div>
    </section>

    <section id="reproducible" class="mt-14 scroll-mt-24 article">
      <h2>Keeping it reproducible</h2>
      <p>
        Copernicus updates its products from time to time, and an update can change the values. Each
        download therefore names an exact dataset version, so the same data is fetched every time the
        step runs.
      </p>
      <div class="not-prose overflow-x-auto my-6">
        <table class="data-table">
          <thead>
            <tr><th>Data</th><th>Dataset ID</th><th>Version</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="v in versions" :key="v.data">
              <td class="font-semibold text-ink-950 whitespace-nowrap">{{ v.data }}</td>
              <td class="font-mono text-[11px] break-all">{{ v.id }}</td>
              <td class="font-mono text-[11px]">{{ v.version }}</td>
              <td class="text-xs text-amber-800 whitespace-nowrap">{{ v.note }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p>
        Both chlorophyll versions are due to be retired on 24 November 2026. After that, this step
        must move to their replacements, and every later step needs re-running and re-checking.
      </p>
      <p>
        The downloaded files are not stored in the repository. They are about 450 MB in total, and anyone
        with a free Copernicus Marine account can download them again by running this step’s notebook.
      </p>
    </section>
  </StepLayout>
</template>
