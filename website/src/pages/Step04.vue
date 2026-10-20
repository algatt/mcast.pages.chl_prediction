<script setup>
import nb04 from '../data/nb04.json'
import StepLayout from '../components/StepLayout.vue'
import AvailabilityDiagram from '../components/AvailabilityDiagram.vue'
import PixelExplorer from '../components/PixelExplorer.vue'
import StatTile from '../components/StatTile.vue'

const { splits, qc, example } = nb04
const windAge = nb04.wind_age_hours
const split = Object.fromEntries(splits.map((s) => [s.name, s]))

const fmt = (n) => Math.round(n).toLocaleString('en-GB')
const millions = (n) => `${(n / 1e6).toFixed(1)} million`
const dateLabel = (date) => new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB', {
  day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC',
})
const hours = (h) => `${Math.round(h)} h`

const inputGroups = [
  {
    group: 'Season',
    final: true,
    items: [{ name: 'Day of the year', detail: 'Stored as two smooth numbers, so that 31 December and 1 January sit next to each other.' }],
  },
  {
    group: 'Chlorophyll history',
    final: true,
    items: [
      { name: 'Latest observation', detail: 'The most recent chlorophyll value at this pixel, however old.' },
      { name: 'Age of the latest observation', detail: 'How many days ago it was measured: 1 day at best.' },
      { name: 'Mean of the past 7 days', detail: 'Average of whatever observations the past week had.' },
      { name: 'Observations in the past 7 days', detail: 'From 0 to 7, so the model knows how much to trust the mean.' },
    ],
  },
  {
    group: 'Usual value',
    final: true,
    items: [{ name: 'Normal for this month', detail: 'Median chlorophyll at this pixel in this calendar month, from the training years only.' }],
  },
  {
    group: 'Sea temperature',
    final: true,
    items: [
      { name: 'Last night’s temperature', detail: 'Empty if cloud hid the sea.' },
      { name: 'Temperature observed?', detail: 'Yes or no — missing values are information too.' },
    ],
  },
  {
    group: 'Wind, for each of the two passes',
    final: false,
    items: [
      { name: 'East and north components, speed', detail: 'From the previous day’s morning and evening passes.' },
      { name: 'Wind observed?', detail: 'Yes or no, per pass.' },
      { name: 'Age of the measurement', detail: `About ${hours(windAge.asc[1])} (evening pass) and ${hours(windAge.des[1])} (morning pass) before the forecast.` },
    ],
  },
  {
    group: 'Location',
    final: true,
    items: [{ name: 'Latitude and longitude', detail: 'Lets the model learn that, for example, the Sicilian coast behaves differently from open water.' }],
  },
]

const splitRows = [
  { key: 'train', label: 'Training', use: 'The model learns from these', tone: 'train' },
  { key: 'validation', label: 'Validation', use: 'Used to choose between model versions', tone: 'validate' },
  { key: 'test', label: 'Test', use: 'Used once, at the very end', tone: 'test' },
]
const YEARS = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
const ageBins = ['1', '2', '3', '4–7', '8+']

const sections = [
  { id: 'what', label: 'What this step does' },
  { id: 'clock', label: 'The forecaster’s clock' },
  { id: 'pixel', label: 'One pixel, one forecast' },
  { id: 'inputs', label: 'All the inputs' },
  { id: 'cleaning', label: 'Cleaning first' },
  { id: 'splits', label: 'Training, validation and test' },
  { id: 'leakage', label: 'No peeking at the answer' },
]
</script>

<template>
  <StepLayout number="04" :sections="sections">
    <template #lead>
      A forecast is only honest if it uses what would really have been known when it was made. This step
      turns the daily observations into forecasting examples — one for every pixel and every day — built
      exactly as a forecaster would see them at 20:30 UTC, and paired with what the satellite observed
      1, 4 and 7 days later.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Each forecasting example is one pixel on one <em>issue day</em>, the day the forecast is made. It has
        two parts:
      </p>
      <ul>
        <li><strong>Inputs:</strong> everything known about that pixel at 20:30 UTC on the issue day — recent
          chlorophyll, temperature, wind, the season and the location.</li>
        <li><strong>Targets:</strong> the chlorophyll the satellite actually observed 1, 4 and 7 days later.
          When the satellite did not see the pixel on that day, there is simply no target, and that forecast is
          not scored.</li>
      </ul>
      <p>
        The step also cleans the data, decides which pixels to model, and divides the years into training,
        validation and test periods. Its output is a single file of about 0.8 GB, ready for step 05.
      </p>
    </section>

    <section id="clock" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The forecaster’s clock</h2>
        <p>
          The archive used for training has every dataset complete and on time. A real forecaster does not: each
          dataset is published with a delay (step 01). This step re-creates those delays, so the model only ever
          learns from information it would have had.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">What is known at 20:30 UTC on issue day D</div>
        <div class="figure-subtitle">Each column is one day; D is the day the forecast is made</div>
        <div class="mt-5">
          <AvailabilityDiagram />
        </div>
        <figcaption class="figure-caption">
          Publication times follow the Copernicus near-real-time schedules. The archive data used for training is
          shifted by these same delays.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          So the newest chlorophyll is always from yesterday, at best, and the newest wind is between about
          {{ hours(windAge.asc[0]) }} and {{ hours(windAge.des[2]) }} old. Temperature is the freshest input:
          last night’s measurement, published at midday. The issue time of 20:30 UTC was chosen to land just after
          yesterday’s chlorophyll arrives at 20:00. That leaves only 30 minutes to spare, which a live service would
          need to watch.
        </p>
      </div>
    </section>

    <section id="pixel" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>One pixel, one forecast</h2>
        <p>
          The clearest way to see what the model receives is to follow one pixel. The chart shows about ten winter
          weeks of chlorophyll in the open channel, north of Malta
          ({{ example.latitude.toFixed(2) }}° N, {{ example.longitude.toFixed(2) }}° E). Move the slider to change
          the issue day.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Inputs and targets for one pixel, winter 2024</div>
        <div class="figure-subtitle">Observed chlorophyll (mg/m³); gaps are cloudy days</div>
        <div class="mt-5">
          <PixelExplorer :example="example" />
        </div>
        <figcaption class="figure-caption">
          All values are those step 04 computed for this pixel. The day of the issue itself is never an input:
          its chlorophyll is only published the following evening.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          A few things become visible as you move the slider. After a cloudy spell the latest observation can be
          several days old, and the model is told so. The weekly mean is sometimes based on one observation, sometimes
          on seven, and the model is told that too. And some targets simply do not exist: if it is cloudy on the
          target day, there is nothing to score against.
        </p>
      </div>
    </section>

    <section id="inputs" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>All the inputs</h2>
        <p>
          In total the step prepares {{ nb04.feature_names.length }} inputs per example. Not all of them end up in
          the final model: step 05 tests which ones actually help, and wind does not make the cut.
        </p>
      </div>

      <div class="my-6 space-y-3">
        <div v-for="g in inputGroups" :key="g.group" class="rounded-xl border bg-white p-4"
             :class="g.final ? 'border-slate-200' : 'border-dashed border-slate-300'">
          <div class="flex flex-wrap items-baseline justify-between gap-2">
            <div class="font-semibold text-ink-950">{{ g.group }}</div>
            <span class="font-mono text-[10px] uppercase tracking-[0.12em]"
                  :class="g.final ? 'text-teal-700' : 'text-slate-500'">
              {{ g.final ? 'In the final model' : 'Tested, then left out' }}
            </span>
          </div>
          <ul class="mt-2 space-y-1.5 text-sm">
            <li v-for="item in g.items" :key="item.name" class="grid sm:grid-cols-[14rem_1fr] gap-x-4">
              <span class="text-ink-950">{{ item.name }}</span>
              <span class="text-slate-600">{{ item.detail }}</span>
            </li>
          </ul>
        </div>
      </div>

      <div class="article">
        <p>
          Missing values are kept as missing. The model used in step 05 can handle an empty input directly, and
          learns what “no temperature tonight” tends to mean, instead of being given a made-up number.
        </p>
      </div>
    </section>

    <section id="cleaning" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Cleaning first</h2>
        <p>
          Two quality rules are applied before any example is built, so they affect inputs and targets alike:
        </p>
      </div>
      <div class="my-6 grid gap-4 sm:grid-cols-2">
        <StatTile label="Implausible values removed" :value="fmt(qc.values_removed)"
                  :detail="`chlorophyll values above 10 mg/m³, out of ${millions(qc.valid_values)} — including the 22,928 mg/m³ found in step 02`" />
        <StatTile label="Rarely observed pixels left out" :value="fmt(qc.pixels_rarely_observed)"
                  :detail="`seen fewer than 200 times in the training years; the typical pixel was seen ${fmt(qc.median_training_observations)} times`" />
      </div>
      <div class="article">
        <p>
          Every pixel left out lies within about 2 km of the coast of Malta, Gozo or Sicily. Near the shore, a 1 km
          pixel can mix sea with land, surf or shallow sea floor, and the colour-based chlorophyll estimate becomes
          unreliable. That leaves {{ fmt(qc.pixels_included) }} pixels to forecast.
        </p>
      </div>
    </section>

    <section id="splits" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Training, validation and test</h2>
        <p>
          The years are split by time, never at random. Earlier years train the model, 2024 is used to compare
          versions of it, and 2025 is kept aside until the very end, as the one honest check of how well it works
          on a year it has never seen.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">How the years are split</div>
        <div class="figure-subtitle">Issue days in each period, and how many have an observed +1-day target</div>
        <div class="mt-5 overflow-x-auto">
          <div class="min-w-[30rem]">
            <div class="grid grid-cols-9 font-mono text-[10px] text-slate-500 mb-1">
              <span v-for="y in YEARS" :key="y" class="text-center">{{ y }}</span>
            </div>
            <div class="grid grid-cols-9 gap-[2px] h-9">
              <div class="col-span-7 rounded split--train grid place-items-center text-xs font-semibold">Training</div>
              <div class="rounded split--validate grid place-items-center text-xs font-semibold">Validation</div>
              <div class="rounded split--test grid place-items-center text-xs font-semibold">Test</div>
            </div>
          </div>
        </div>
        <div class="mt-5 overflow-x-auto">
          <table class="data-table">
            <thead><tr><th>Period</th><th>Issue days</th><th class="text-right">Days</th>
              <th class="text-right">Observed +1-day targets</th><th class="text-right">Share of pixel-days</th></tr></thead>
            <tbody>
              <tr v-for="r in splitRows" :key="r.key">
                <td><span class="font-semibold text-ink-950">{{ r.label }}</span>
                  <span class="block text-[11px] text-slate-500">{{ r.use }}</span></td>
                <td class="whitespace-nowrap">{{ dateLabel(split[r.key].first) }} – {{ dateLabel(split[r.key].last) }}</td>
                <td class="num">{{ fmt(split[r.key].issue_days) }}</td>
                <td class="num">{{ millions(split[r.key].targets[1].count) }}</td>
                <td class="num">{{ split[r.key].targets[1].coverage_pct.toFixed(0) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
        <figcaption class="figure-caption">
          Each period stops issuing forecasts on 24 December, so that a 7-day target never falls in the next period.
          The +4 and +7-day counts are within 1% of the +1-day counts.
        </figcaption>
      </figure>

      <div class="callout callout-later">
        <div class="label-caps !text-amber-800">Decided in step 05</div>
        <p class="mt-2 text-sm leading-relaxed text-slate-700">
          This step first trained on 2008–2023. Step 05 then showed that the years before 2017 do not help (step 03
          shows why: chlorophyll was higher then), so training now starts in 2017. The monthly “normal” and the list of
          pixels to model are recalculated from the same years.
        </p>
      </div>
    </section>

    <section id="leakage" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>No peeking at the answer</h2>
        <p>
          The easiest way to fool yourself with a forecast is to let information from the future slip into the
          inputs. It rarely looks like cheating; it looks like a detail. This step guards against five such details:
        </p>
        <ol>
          <li><strong>Publication delays.</strong> Every input is shifted by the time the real data takes to arrive
            (above), even though the archive has it sooner.</li>
          <li><strong>Training years only.</strong> The monthly normal and the choice of pixels use only the training
            years, never 2024 or 2025.</li>
          <li><strong>Split by time.</strong> Neighbouring pixels on the same day are almost identical. If examples
            were split at random, the test set would be full of near-copies of training examples, and the score would
            look far better than any real forecast.</li>
          <li><strong>A week between periods.</strong> No training example has a target inside the validation or test
            period.</li>
          <li><strong>No filled targets.</strong> Forecasts are scored only on real observations (step 01).</li>
        </ol>
        <p>
          The price of these rules is visible in the data: on most forecasts the latest chlorophyll is a day old,
          but in the training years about one in five forecasts had to work from chlorophyll three days old or more.
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>Age of the latest observation</th>
            <th v-for="b in ageBins" :key="b" class="text-right">{{ b }} day{{ b === '1' ? '' : 's' }}</th></tr></thead>
          <tbody>
            <tr v-for="r in splitRows" :key="r.key">
              <td class="font-semibold text-ink-950">{{ r.label }}</td>
              <td v-for="b in ageBins" :key="b" class="num">{{ split[r.key].age_pct[b].toFixed(0) }}%</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">Share of +1-day forecasts with an observed target, by how old their latest chlorophyll is.</p>
      </div>
    </section>
  </StepLayout>
</template>

<style scoped>
.split--train { background: #ccebe5; color: #0a4842; }
.split--validate { background: #6cc2b1; color: #07171e; }
.split--test { background: #0b665d; color: #ffffff; }
</style>
