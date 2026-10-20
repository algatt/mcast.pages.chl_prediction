<script setup>
import nb03 from '../data/nb03.json'
import { chlLayer, formatChl } from '../data/ramps.js'
import StepLayout from '../components/StepLayout.vue'
import GridMap from '../components/GridMap.vue'
import CoverageHeatmap from '../components/CoverageHeatmap.vue'
import GapBars from '../components/GapBars.vue'
import LineChart from '../components/LineChart.vue'
import StatTile from '../components/StatTile.vue'

const { gaps, gap_summary: gapSummary, cycle, relations, fading, reobserved, grid } = nb03
const monthCoverage = nb03.coverage_by_month_pct

const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const MONTH_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December']

// Era colours match step 01: grey for 2008–2016, teal for 2017 onwards.
const OLD = '#9e9b93'
const RECENT = '#0d9488'
// Season colours: fixed order, every line also labelled directly.
const SEASON_COLORS = { Winter: '#2a78d6', Spring: '#1baf7a', Summer: '#eb6834', Autumn: '#eda100' }

const pctOf = (v) => `${Math.round(v)}%`
const mg = (v) => (v < 0.1 ? v.toFixed(3) : v.toFixed(2))
const asFactor = (logRmse) => Math.round((10 ** logRmse - 1) * 100)

// Coverage heatmap
const coverageSources = [
  { id: 'chl', label: 'Chlorophyll', matrix: nb03.coverage_matrix_pct.chl },
  { id: 'sst', label: 'Sea temperature', matrix: nb03.coverage_matrix_pct.sst },
]
const lowMonth = monthCoverage.indexOf(Math.min(...monthCoverage))
const highMonth = monthCoverage.indexOf(Math.max(...monthCoverage))

// Seasonal cycle
const cycleSeries = [
  { name: '2008–2016', color: OLD, points: cycle['2008–2016'].map((p) => ({ x: p.month, y: p.median, lo: p.q25, hi: p.q75 })) },
  { name: '2017–2025', color: RECENT, points: cycle['2017–2025'].map((p) => ({ x: p.month, y: p.median, lo: p.q25, hi: p.q75 })) },
]
const old = cycle['2008–2016']
const recent = cycle['2017–2025']
const annualOld = nb03.cycle_annual_median['2008–2016']
const annualRecent = nb03.cycle_annual_median['2017–2025']
const marchDrop = Math.round(100 * (1 - recent[2].median / old[2].median))
const peak = recent.reduce((a, b) => (b.median > a.median ? b : a))
const trough = recent.reduce((a, b) => (b.median < a.median ? b : a))

// Seasonal maps
const seasonLayers = ['Winter', 'Spring', 'Summer', 'Autumn'].map((s) =>
  chlLayer({
    id: s,
    label: s,
    values: nb03.season_maps_log1000[s],
    domain: [0.03, 1],
    ticks: [0.03, 0.1, 0.3, 1],
    tickFormat: (t) => (t === 1 ? '≥1' : `${t}`),
    missingLabel: 'No observations',
    showMissing: false,
    format: (v) => `Median ${formatChl(v)}`,
  }),
)

// Relations with temperature and wind
const relationSeries = (key, color) => [{
  name: 'Median day',
  color,
  points: relations[key].bins.map((b) => ({ x: b.x, y: b.median, lo: b.q25, hi: b.q75 })),
}]
const sstRho = relations.sst.spearman
const windRho = relations.wind.spearman
const seasons = ['Winter', 'Spring', 'Summer', 'Autumn']

// Fading similarity
const fadingSeries = seasons.map((s) => ({
  name: s,
  color: SEASON_COLORS[s],
  points: fading[s].map((p) => ({ x: p.lag, y: p.rmse_log10 })),
}))
const lag = (season, k) => fading[season][k - 1].rmse_log10

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'visible', label: 'How often is the sea visible?' },
  { id: 'gaps', label: 'How long are the gaps?' },
  { id: 'normal', label: 'What is a normal year?' },
  { id: 'drivers', label: 'Temperature and wind' },
  { id: 'memory', label: 'How long does today last?' },
  { id: 'lessons', label: 'What this means for the forecast' },
]
</script>

<template>
  <StepLayout number="03" :sections="sections">
    <template #lead>
      Before building a forecast, it pays to look hard at the data. This step asks five simple
      questions: how often the satellites can see the sea, how long they are blind for, what a normal
      year looks like, whether temperature or wind move with chlorophyll, and how quickly today’s
      chlorophyll stops telling us about the days ahead.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Nothing in this step changes the data. It produces maps, charts and a few tables from the combined
        file of step 02, covering {{ nb03.period[0].slice(0, 4) }}–{{ nb03.period[1].slice(0, 4) }} and the
        {{ nb03.sea_pixels.toLocaleString('en-GB') }} sea pixels of the study area. The answers decide several
        things later: which inputs are worth trying, how missing data is handled, which years define “normal”,
        and what a forecast has to beat.
      </p>
      <p>
        The charts here use the same quality rule as step 04, so the impossible chlorophyll value found in
        step 02 is already removed.
      </p>
    </section>

    <section id="visible" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>How often is the sea visible?</h2>
        <p>
          Each square below is one month of one year, shaded by how much of the sea the satellites saw on an
          average day. Two patterns stand out. Winter is cloudy: in {{ MONTH_LONG[lowMonth] }} only
          {{ pctOf(monthCoverage[lowMonth]) }} of the sea is observed on a typical day, against
          {{ pctOf(monthCoverage[highMonth]) }} in {{ MONTH_LONG[highMonth] }}. And the rows get darker from
          2017, when an extra generation of satellites joined the record (step 01).
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Average daily coverage, by year and month</div>
        <div class="figure-subtitle">Share of sea pixels with a valid observation</div>
        <div class="mt-5">
          <CoverageHeatmap :sources="coverageSources" />
        </div>
        <figcaption class="figure-caption">
          Temperature is measured at night by an infrared sensor, which is also blocked by cloud, so its gaps
          follow the same seasons. Hover over a square for the exact value.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The cloudiest months are also when chlorophyll is highest and changes most, as the next sections
          show. So the forecast has the least information exactly when it matters most.
        </p>
      </div>
    </section>

    <section id="gaps" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>How long are the gaps?</h2>
        <p>
          For every pixel, the step measures each run of consecutive days without an observation. Most gaps are
          short. But a few long gaps contain a large share of all the missing days, and those are the periods
          where the last observation is old by the time a forecast is made.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Length of gaps in the chlorophyll record</div>
        <div class="figure-subtitle">{{ (gapSummary.events / 1e6).toFixed(1) }} million gaps across all sea pixels, 2008–2025</div>
        <div class="mt-5">
          <GapBars :gaps="gaps" />
        </div>
        <figcaption class="figure-caption">
          Only gaps with an observation on both sides are counted. Hover over a row to compare the two panels.
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="One-day gaps" :value="pctOf(gapSummary.share_one_day_pct)" detail="of all gaps last a single day" />
        <StatTile label="Long gaps" :value="pctOf(gapSummary.share_over_week_missing_days_pct)"
                  detail="of missing days fall in gaps longer than a week" />
        <StatTile label="Seen again tomorrow" :value="pctOf(reobserved[0].pct)"
                  detail="of pixels observed today are observed again the next day" />
      </div>

      <div class="article mt-8">
        <p>
          The last number matters most for forecasting. Even when a pixel is visible today, there is roughly a
          one-in-three chance it will be cloudy tomorrow. A forecast must therefore work from “the most recent
          observation, however old”, and know how old it is. Step 04 builds exactly that.
        </p>
      </div>
    </section>

    <section id="normal" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What is a normal year?</h2>
        <p>
          Chlorophyll follows a strong yearly cycle. In winter, storms mix the water and bring nutrients up to
          the sunlit surface, so phytoplankton grow; in summer the surface is warm, calm and starved of
          nutrients. Here the typical day peaks at about {{ mg(peak.median) }} mg/m³ in
          {{ MONTH_LONG[peak.month - 1] }} and falls to about {{ mg(trough.median) }} mg/m³ in
          {{ MONTH_LONG[trough.month - 1] }}.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">The yearly chlorophyll cycle, in two eras</div>
        <div class="figure-subtitle">Median of daily regional medians; shaded band covers the middle half of days</div>
        <div class="mt-4">
          <LineChart
            :series="cycleSeries"
            :x-domain="[1, 12]"
            :y-domain="[0, 0.2]"
            :x-ticks="MONTH_SHORT.map((label, i) => ({ value: i + 1, label }))"
            :y-ticks="[0, 0.05, 0.1, 0.15, 0.2]"
            :y-format="(v) => v.toFixed(2)"
            :value-format="mg"
            :x-format="(m) => MONTH_LONG[m - 1]"
            y-title="Chlorophyll, typical day (mg/m³)"
            aria-label="Line chart of median chlorophyll by month, comparing 2008–2016 with 2017–2025"
          />
        </div>
        <figcaption class="figure-caption">
          A day counts only if at least 5% of the sea was observed. Hover for each month’s values and range.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The two eras are not the same. Across the year, the typical day in 2017–2025 is about
          {{ Math.round(100 * (1 - annualRecent / annualOld)) }}% lower than in 2008–2016, and the spring
          decline arrives earlier: March is {{ marchDrop }}% lower. Whether that is a real change in the sea,
          a change in the satellites, or both, this data cannot say. It does mean the older years describe a
          “normal” that no longer applies, which is why step 05 ends up training on 2017 onwards.
        </p>
        <p>The cycle also has a geography. Switch between the seasons:</p>
      </div>

      <figure class="figure">
        <div class="figure-title">Where chlorophyll is high, season by season</div>
        <div class="figure-subtitle">Median of all observations at each pixel, 2008–2025</div>
        <div class="mt-5">
          <GridMap :latitude="grid.latitude" :longitude="grid.longitude" :sea="grid.sea"
                   :layers="seasonLayers" aria-label="Seasonal median chlorophyll map" />
        </div>
        <figcaption class="figure-caption">
          The Sicilian coast is high in every season; the open channel and the waters around Malta swing from
          winter highs to very clear summer water. All four maps share one colour scale.
        </figcaption>
      </figure>
    </section>

    <section id="drivers" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Do temperature and wind move with chlorophyll?</h2>
        <p>
          A forecast can only use other variables if they carry information. The step compares the typical
          chlorophyll of each day with that day’s typical temperature, and with the morning wind.
        </p>
      </div>

      <div class="grid gap-6 md:grid-cols-2">
        <figure class="figure !my-0">
          <div class="figure-title">Against sea temperature</div>
          <div class="figure-subtitle">{{ relations.sst.days.toLocaleString('en-GB') }} days</div>
          <div class="mt-3">
            <LineChart :series="relationSeries('sst', '#cc5a26')" :x-domain="[14, 30]" :y-domain="[0, 0.16]"
                       :x-ticks="[14, 18, 22, 26, 30].map((v) => ({ value: v, label: `${v}` }))"
                       :y-ticks="[0, 0.04, 0.08, 0.12, 0.16]" :y-format="(v) => v.toFixed(2)" :value-format="mg"
                       :x-format="(v) => `${(v - 0.5).toFixed(0)}–${(v + 0.5).toFixed(0)} °C`"
                       x-title="Sea temperature (°C)" y-title="Chlorophyll (mg/m³)" :height="230" :show-legend="false" :show-end-labels="false"
                       aria-label="Typical chlorophyll against sea temperature" />
          </div>
        </figure>
        <figure class="figure !my-0">
          <div class="figure-title">Against morning wind speed</div>
          <div class="figure-subtitle">{{ relations.wind.days.toLocaleString('en-GB') }} days, 2019–2025</div>
          <div class="mt-3">
            <LineChart :series="relationSeries('wind', '#5f51c9')" :x-domain="[1, 12]" :y-domain="[0, 0.16]"
                       :x-ticks="[2, 4, 6, 8, 10, 12].map((v) => ({ value: v, label: `${v}` }))"
                       :y-ticks="[0, 0.04, 0.08, 0.12, 0.16]" :y-format="(v) => v.toFixed(2)" :value-format="mg"
                       :x-format="(v) => `${(v - 0.5).toFixed(0)}–${(v + 0.5).toFixed(0)} m/s`"
                       x-title="Wind speed (m/s)" y-title="Chlorophyll (mg/m³)" :height="230" :show-legend="false" :show-end-labels="false"
                       aria-label="Typical chlorophyll against wind speed" />
          </div>
        </figure>
      </div>
      <p class="mt-3 text-xs text-slate-500">
        Line: median chlorophyll of the days in each 1-unit bin; band: middle half of those days. Bins with fewer
        than 15 days are left out. Both charts use daily medians over the pixels where both values exist.
      </p>

      <div class="article mt-8">
        <p>
          Both charts show a clear trend: colder water and stronger wind go with more chlorophyll. But both
          are partly the same story told twice. Winter is cold, windy <em>and</em> high in chlorophyll, so
          any winter feature will look related. The fairer test is whether the relationship holds
          <em>within</em> a season:
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead>
            <tr><th>Relationship with chlorophyll</th><th class="text-right">All days</th>
              <th v-for="s in seasons" :key="s" class="text-right">{{ s }}</th></tr>
          </thead>
          <tbody>
            <tr>
              <td class="font-semibold text-ink-950">Sea temperature</td>
              <td class="num">{{ sstRho.all.toFixed(2) }}</td>
              <td v-for="s in seasons" :key="s" class="num">{{ sstRho[s].toFixed(2) }}</td>
            </tr>
            <tr>
              <td class="font-semibold text-ink-950">Morning wind speed</td>
              <td class="num">{{ windRho.all.toFixed(2) }}</td>
              <td v-for="s in seasons" :key="s" class="num">{{ windRho[s].toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">
          Rank correlation between daily values: −1 means perfectly opposite, 0 means no relationship, +1 means
          they rise together.
        </p>
      </div>

      <div class="article">
        <p>
          Temperature keeps a real relationship inside every season, strongest in spring
          ({{ sstRho.Spring.toFixed(2) }}), when the sea warms and the bloom ends. Wind almost loses its
          relationship in winter and summer ({{ windRho.Winter.toFixed(2) }} and {{ windRho.Summer.toFixed(2) }}).
          Most of what wind appears to say is “it is winter”, which the season already tells us. That is an
          early hint of a later result: in step 05, temperature helps the forecast a little and wind hardly at all.
        </p>
      </div>
    </section>

    <section id="memory" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>How long does today’s chlorophyll stay informative?</h2>
        <p>
          The simplest forecast is “it will stay as it is”. How good is that? For every pixel observed on two
          days, the step measures how different the two values are, for days 1 to 7 apart. The chart shows the
          typical difference on a log scale: 0.1 means the later value is typically about 26% higher or lower,
          0.2 about 58%.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">How different chlorophyll is k days later, by season</div>
        <div class="figure-subtitle">Typical difference between two observations of the same pixel (root-mean-square, log10)</div>
        <div class="mt-4">
          <LineChart :series="fadingSeries" :x-domain="[1, 7]" :y-domain="[0, 0.25]"
                     :x-ticks="[1, 2, 3, 4, 5, 6, 7].map((v) => ({ value: v, label: `${v}` }))"
                     :y-ticks="[0, 0.05, 0.1, 0.15, 0.2, 0.25]" :y-format="(v) => v.toFixed(2)"
                     :value-format="(v) => `${v.toFixed(3)} (≈${asFactor(v)}%)`"
                     :x-format="(v) => `${v} day${v > 1 ? 's' : ''} later`"
                     x-title="Days between the two observations" :height="280"
                     aria-label="Line chart of day-to-day chlorophyll difference by season and days apart" />
        </div>
        <figcaption class="figure-caption">
          Seasons are of the first of the two days. Hover to read each season’s value; the percentage is the
          equivalent typical change.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The difference grows with every day, quickly at first and then more slowly. Winter changes fastest:
          a 1-day gap already means a typical difference of about {{ asFactor(lag('Winter', 1)) }}%, rising to
          about {{ asFactor(lag('Winter', 7)) }}% after a week. Summer is the most stable, at
          {{ asFactor(lag('Summer', 1)) }}% and {{ asFactor(lag('Summer', 7)) }}%.
        </p>
        <p>
          Not all of this is real change in the sea. The satellite estimate itself has some noise from day to
          day, so even a perfect forecast would not reach zero here. These numbers are, in effect, the score of
          the “no change” forecast that every model in step 05 is compared with.
        </p>
      </div>
    </section>

    <section id="lessons" class="mt-14 scroll-mt-24 article">
      <h2>What this means for the forecast</h2>
      <ul>
        <li><strong>Missing data is normal, not an exception.</strong> Inputs are built from the most recent
          observation, together with how old it is and how many observations the past week had (step 04).</li>
        <li><strong>The season carries a lot of information.</strong> The day of the year is a model input, and
          the usual value for the month is tested both as an input and as a baseline.</li>
        <li><strong>Recent years define normal.</strong> The drop since 2017 is the first sign that training on
          every available year may not help (tested in step 05).</li>
        <li><strong>Temperature is worth trying; wind may not be.</strong> Both are tested in step 05.</li>
        <li><strong>The bar to beat is “no change”</strong> — and the gap between today and a week ahead shows how
          much room a forecast has to improve on it.</li>
      </ul>
    </section>
  </StepLayout>
</template>
