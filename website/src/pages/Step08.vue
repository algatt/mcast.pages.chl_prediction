<script setup>
import { computed, ref } from 'vue'
import nb08 from '../data/nb08.json'
import { steps, stepPath } from '../data/steps.js'
import StepLayout from '../components/StepLayout.vue'
import StatTile from '../components/StatTile.vue'

const { sources, runs } = nb08
const check = nb08.first_full_check
const SEA_PIXELS = 12380

const longDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const addDays = (d, n) => new Date(Date.parse(`${d}T00:00:00Z`) + n * 86400000).toISOString().slice(0, 10)

// Calendar strip covering everything held.
const allFirst = Object.values(sources).map((s) => s.first).sort()[0]
const allLast = Object.values(sources).map((s) => s.last).sort().slice(-1)[0]
const days = computed(() => {
  const out = []
  for (let d = allFirst; d <= allLast; d = addDays(d, 1)) out.push(d)
  return out
})
const rows = [
  { key: 'chl', label: 'Chlorophyll', note: 'observed (L3)' },
  { key: 'chl_l4', label: 'Chlorophyll', note: 'gap-filled (L4)' },
  { key: 'sst', label: 'Sea temperature', note: 'last 30 days' },
]
const held = (key, d) => d >= sources[key].first && d <= sources[key].last && !sources[key].missing.includes(d)
const chlCoverage = (d) => (sources.chl.valid_pixels[d] ?? 0) / SEA_PIXELS
const hover = ref(null)

const firstRun = runs[0]
const runTime = (r) => `${shortDate(r.retrieved_utc.slice(0, 10))}, ${r.retrieved_utc.slice(11, 16)} UTC`
const step07 = steps.find((s) => s.number === '07')
</script>

<template>
  <StepLayout number="08" :sections="[
    { id: 'what', label: 'What this step does' },
    { id: 'rules', label: 'How it works' },
    { id: 'holdings', label: 'What it holds today' },
    { id: 'ahead', label: 'What it makes possible' },
    { id: 'running', label: 'Keeping it going' },
    { id: 'end', label: 'Where the experiment stands' },
  ]">
    <template #lead>
      The live feed forgets. Copernicus keeps only a short, changing window of near-real-time data, so the
      evidence a live forecast needs disappears within days. This last step keeps it: a small notebook,
      run once a day, that saves every new day of live data and never overwrites it.
    </template>

    <section id="what" class="article scroll-mt-24">
      <h2>What this step does</h2>
      <p>
        Step 07 could issue a live forecast but could not score one: checking a 7-day forecast needs 15 consecutive days of
        live chlorophyll, and on 19 October 2026 Copernicus offered only 9. There is nothing wrong with the forecast or the
        model there; the history simply is not kept long enough.
      </p>
      <p>
        So this step builds the history locally. Each time it runs, it looks at what the live feed currently offers for the
        three products step 07 uses — observed chlorophyll, gap-filled chlorophyll and sea temperature — and saves every day
        it does not already have.
      </p>
    </section>

    <section id="rules" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>How it works</h2>
        <p>Five simple rules:</p>
        <ol>
          <li><strong>One file per day, per product.</strong> Each day is saved on its own, named by its date, for the study
            area only.</li>
          <li><strong>Never overwrite.</strong> If a day is already saved, it is skipped, even if Copernicus has since revised
            it. The first copy is what a forecast issued that evening would actually have used.</li>
          <li><strong>Record when.</strong> Every file stores the time it was downloaded, and a log lists every save. Over
            time, that shows when data really arrives, instead of assuming the published schedule.</li>
          <li><strong>Never leave half a file.</strong> Each file is written under a temporary name and renamed only when
            complete, so an interrupted run cannot leave a damaged file that looks finished.</li>
          <li><strong>Temperature: only the last 30 days.</strong> The live temperature product already reaches back to 2008,
            so there is no need to copy all of it.</li>
        </ol>
      </div>

      <div class="my-6 rounded-xl border border-slate-200 bg-white p-4 font-mono text-[12px] leading-relaxed text-slate-700 overflow-x-auto">
        <div>data/raw/nrt_archive/</div>
        <div>├── chl/        <span class="text-slate-400">2026-10-10.nc, 2026-10-11.nc, …</span></div>
        <div>├── chl_l4/     <span class="text-slate-400">2026-10-07.nc, …</span></div>
        <div>├── sst/        <span class="text-slate-400">2026-09-20.nc, …</span></div>
        <div>└── archive_log.csv  <span class="text-slate-400">source, date, saved or skipped, pixels, download time</span></div>
      </div>
    </section>

    <section id="holdings" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What it holds today</h2>
        <p>
          The archive was started on {{ longDate(firstRun.retrieved_utc.slice(0, 10)) }}. Its first run saved everything the live
          feed still offered, {{ firstRun.saved }} days across the three products:
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Days held in the local archive</div>
        <div class="figure-subtitle">{{ shortDate(allFirst) }} – {{ shortDate(allLast) }} 2026; bar height on the first row is the share of the sea observed</div>
        <div class="mt-5 overflow-x-auto">
          <div class="grid grid-cols-[6.5rem_1fr] sm:grid-cols-[8.5rem_1fr] gap-x-3 gap-y-2 items-end">
            <template v-for="r in rows" :key="r.key">
              <div class="text-xs leading-tight pb-0.5">
                <span class="font-semibold text-ink-950">{{ r.label }}</span>
                <span class="block text-[10px] text-slate-500">{{ r.note }}</span>
              </div>
              <div class="flex gap-[2px] items-end h-9">
                <span
                  v-for="d in days"
                  :key="d"
                  class="flex-1 rounded-[2px]"
                  :class="held(r.key, d) ? '' : 'day--empty'"
                  :style="held(r.key, d)
                    ? { background: '#0d9488', height: r.key === 'chl' ? `${Math.max(12, 100 * chlCoverage(d))}%` : '100%',
                        opacity: hover && hover !== d ? 0.6 : 1 }
                    : { height: '100%' }"
                  @mouseenter="hover = d"
                  @mouseleave="hover = null"
                ></span>
              </div>
            </template>
            <span></span>
            <div class="flex justify-between font-mono text-[10px] text-slate-500">
              <span>{{ shortDate(allFirst) }}</span><span>{{ shortDate(addDays(allFirst, Math.floor(days.length / 2))) }}</span><span>{{ shortDate(allLast) }}</span>
            </div>
          </div>
        </div>
        <p class="mt-3 min-h-[1.25rem] text-xs text-slate-600">
          <template v-if="hover">
            <strong class="text-ink-950">{{ longDate(hover) }}:</strong>
            chlorophyll {{ held('chl', hover) ? `held, ${Math.round(100 * chlCoverage(hover))}% of the sea observed` : 'not held' }} ·
            gap-filled {{ held('chl_l4', hover) ? 'held' : 'not held' }} ·
            temperature {{ held('sst', hover) ? 'held' : 'not held' }}
          </template>
          <template v-else>Hover over a day for details.</template>
        </p>
        <figcaption class="figure-caption">
          Empty squares are days the live feed no longer offered when the archive started. No day is missing between the first
          and last day held for any product.
        </figcaption>
      </figure>

      <div class="grid gap-4 sm:grid-cols-3">
        <StatTile label="Observed chlorophyll" :value="`${sources.chl.days} days`" :detail="`${shortDate(sources.chl.first)} – ${shortDate(sources.chl.last)}`" />
        <StatTile label="Gap-filled chlorophyll" :value="`${sources.chl_l4.days} days`" :detail="`${shortDate(sources.chl_l4.first)} – ${shortDate(sources.chl_l4.last)}`" />
        <StatTile label="Sea temperature" :value="`${sources.sst.days} days`" :detail="`${shortDate(sources.sst.first)} – ${shortDate(sources.sst.last)}`" />
      </div>

      <div class="article mt-8">
        <p>
          The windows differ by product: on the same day, the live feed offered 12 days of gap-filled chlorophyll but only 9 of
          observed chlorophyll. That is one more reason to save every day as it appears rather than rely on any product’s
          window. The whole archive so far is about
          {{ Math.round((sources.chl.size_kb + sources.chl_l4.size_kb + sources.sst.size_kb) / 100) / 10 }} MB.
        </p>
      </div>
    </section>

    <section id="ahead" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What it makes possible</h2>
        <p>If the archive is run every day, the checks listed at the end of step 07 become possible one by one:</p>
      </div>

      <div class="my-6 space-y-3">
        <div class="card">
          <div class="label-caps">From {{ longDate(check.available_from) }}</div>
          <div class="mt-1 font-semibold text-ink-950">The first complete live check</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            A forecast issued on {{ longDate(check.issue_date) }} has seven days of archived history behind it, and its 7-day target,
            {{ longDate(check.target_date) }}, is published the following evening. From then on, each new day adds one more fully
            checkable forecast.
          </p>
        </div>
        <div class="card">
          <div class="label-caps">From the second run</div>
          <div class="mt-1 font-semibold text-ink-950">Real delivery times</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The first run saved several days at once, so its download times say nothing about delivery. Every later run saves only
            the days that are new, and their download times show how soon after the satellite pass the data was really available.
            Runs at varied times of day build up the clearest picture.
          </p>
        </div>
        <div class="card">
          <div class="label-caps">After about a month</div>
          <div class="mt-1 font-semibold text-ink-950">Live versus archive values</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The archive’s interim updates run about a month behind. Once they cover the archived days, the two versions of the same
            day can be compared directly: how much the values and the gaps differ, and whether the model behaves differently on each.
          </p>
        </div>
        <div class="card">
          <div class="label-caps">After a winter</div>
          <div class="mt-1 font-semibold text-ink-950">A live score in the season that matters</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Winter and spring are when chlorophyll is highest, changes fastest and is hardest to forecast (steps 03, 05 and 06). A live
            evaluation that covers them is the one that would justify calling the forecast a service.
          </p>
        </div>
      </div>
    </section>

    <section id="running" class="mt-14 scroll-mt-24 article">
      <h2>Keeping it going</h2>
      <ul>
        <li><strong>Run it daily, in the evening.</strong> After 20:00 UTC the previous day’s chlorophyll should be available. Each run
          takes a few minutes, most of it spent connecting to the Copernicus catalogue.</li>
        <li><strong>Missing a day is fine; missing a week is not.</strong> A later run catches up on anything the live feed still offers,
          but once a day falls out of the window (about 9 days for observed chlorophyll at the moment) it is gone for good.</li>
        <li><strong>Back it up.</strong> The archive lives on one computer and is deliberately not in the code repository. Copying the
          folder somewhere safe from time to time protects weeks of collection.</li>
      </ul>
    </section>

    <section id="end" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Where the experiment stands</h2>
        <p>Across the eight steps, the experiment has established three things.</p>
      </div>
      <div class="mt-4 grid gap-4">
        <div class="card">
          <div class="font-semibold text-ink-950">An honest test of an honest forecast</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Forecasts use only data that would have been available at 20:30 UTC, are scored only on real observations, and are judged
            on a year the model never saw (steps 01–05).
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">A useful but modest gain</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Clearly better than “no change”; better than a simple persistence–climatology blend at 1 day, marginally at 4, not
            demonstrably at 7; best in the open channel and in spring and autumn; no skill on blooms (steps 05–06).
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">A working live pipeline, not yet a validated one</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The model runs on the live feed end to end (step 07), and the archive (this step) is collecting what is needed to check it.
            The live scores will be added to this site when there is enough data to make them meaningful.
          </p>
        </div>
      </div>
      <div class="mt-8 flex flex-wrap gap-3">
        <router-link to="/" class="button-light">Back to the overview</router-link>
        <router-link :to="stepPath(step07)" class="button-light">Step 07 · Live data validation</router-link>
      </div>
    </section>
  </StepLayout>
</template>

<style scoped>
.day--empty { background: repeating-linear-gradient(135deg, var(--gap-hatch) 0 1px, var(--gap) 1px 5px); }
</style>
