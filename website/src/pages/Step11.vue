<script setup>
import { computed, ref } from 'vue'
import nb11 from '../data/nb11.json'
import { steps, stepPath } from '../data/steps.js'
import StepLayout from '../components/StepLayout.vue'
import GainTable from '../components/GainTable.vue'
import IntervalChart from '../components/IntervalChart.vue'
import StatTile from '../components/StatTile.vue'

const H = [1, 4, 7]
const days = (h) => `+${h} day${h > 1 ? 's' : ''}`
const signed = (v) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}%`
const fmt = (n) => Math.round(n).toLocaleString('en-GB')
const longDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })
const shortDate = (d) => new Date(`${d}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
const monthDay = (md) => shortDate(`2026-${md}`)
const pctChange = (log) => 100 * (10 ** log - 1)
const step07 = steps.find((s) => s.number === '07')
const step10 = steps.find((s) => s.number === '10')
const step12 = steps.find((s) => s.number === '12')

const liveYear = nb11.live_chl_days[1].slice(0, 4)
const unseen = nb11.years_unseen
const inTraining = nb11.years_in_training
const windowText = `${monthDay(nb11.window[0])} – ${monthDay(nb11.window[1])}`

// --- Is it the season? ---------------------------------------------------------------
const windowRow = (data, h) => nb11.window_comparison.find((r) => r.data === data && r.horizon === h)
const LIVE = `Live NRT ${liveYear}`
const UNSEEN = nb11.window_comparison.find((r) => r.data.includes('unseen')).data
const TRAINED = nb11.window_comparison.find((r) => r.data.includes('in training')).data
const windowGroups = [
  { data: LIVE, title: `Live feed, ${liveYear}` },
  { data: UNSEEN, title: `Archive, ${unseen.join(', ')}: a year the model never saw` },
  { data: TRAINED, title: `Archive, ${inTraining[0]}–${inTraining[inTraining.length - 1]}: years it was trained on` },
].map((g) => ({
  title: g.title,
  rows: H.map((h) => windowRow(g.data, h)).filter((r) => r && r.low !== null)
    .map((r) => ({ label: days(r.horizon), value: r.gain, low: r.low, high: r.high })),
}))

const yearRow = (y, h) => nb11.by_year.find((r) => r.year === y && r.horizon === h)
const years = [...new Set(nb11.by_year.map((r) => r.year))]
const yearRows = years.map((y) => ({
  label: y.startsWith('Live') ? `${liveYear}, live` : y,
  note: y.startsWith('Live') ? 'near-real-time feed' : unseen.includes(Number(y)) ? 'archive · unseen' : 'archive · in training',
  emphasis: y.startsWith('Live'),
  values: Object.fromEntries(H.map((h) => [h, yearRow(y, h)?.gain ?? null])),
}))
const archiveYears = years.filter((y) => !y.startsWith('Live'))
const minArchiveGain = (h) => Math.min(...archiveYears.map((y) => yearRow(y, h)?.gain).filter((v) => v !== null && v !== undefined))
const yearsModelWins = (h) => archiveYears.filter((y) => (yearRow(y, h)?.gain ?? -1) > 0).length
const noChange = (y, h) => yearRow(y, h)?.rmse_no_change
const noChangeRange = (h) => {
  const v = archiveYears.map((y) => noChange(y, h)).filter((x) => x !== undefined)
  return [Math.min(...v), Math.max(...v)]
}
const hardestYear = archiveYears.reduce((a, b) => (noChange(b, 1) > noChange(a, 1) ? b : a))

// --- Different inputs? -------------------------------------------------------------------
const NAMES = {
  sst_anomaly: 'Temperature anomaly', chl_observations_7d: 'Observations in the past week', sst_c: 'Temperature',
  sst_change_7d: 'Temperature change over a week', chl_age_days: 'Age of the latest observation',
  chl_trend_log: 'Recent chlorophyll trend', chl_anomaly_log: 'Chlorophyll anomaly', sst_observed: 'Temperature observed',
  chl_latest: 'Latest chlorophyll', chl_nbr5_yesterday: 'Neighbourhood, yesterday', chl_nbr15_7d: 'Wider neighbourhood, past week',
  chl_mean_7d: 'Chlorophyll, past-week mean',
}
const shifts = nb11.input_shifts.filter((r) => NAMES[r.input]).slice(0, 8)
const fmtMean = (v) => (Math.abs(v) >= 1 ? v.toFixed(2) : v.toPrecision(2)).replace('-', '−')
const fmtRange = (text) => text.replace(/-/g, '−').replace(' to ', ' to ')
const tempRow = (data, h) => nb11.temperature_test.find((r) => r.data === data && r.horizon === h)
const tempLabels = [...new Set(nb11.temperature_test.map((r) => r.data))]
const temperatureRows = tempLabels.map((d) => ({
  label: d.replace('Live NRT', `Live ${liveYear}`).replace('MY', 'Archive'),
  emphasis: d.includes('Live') && d.includes('hidden'),
  values: Object.fromEntries(H.map((h) => [h, tempRow(d, h)?.gain ?? null])),
}))
const liveHidden = (h) => tempRow(tempLabels.find((d) => d.includes('Live') && d.includes('hidden')), h).gain

// --- The same days, twice --------------------------------------------------------------
const coverage = nb11.coverage.filter((d) => d.date <= nb11.overlap_days[1])
const totals = coverage.reduce((t, d) => ({ nrt: t.nrt + d.nrt, my: t.my + d.my, both: t.both + d.both, nrt_only: t.nrt_only + d.nrt_only, my_only: t.my_only + d.my_only }),
  { nrt: 0, my: 0, both: 0, nrt_only: 0, my_only: 0 })
const maxPixels = Math.max(...coverage.map((d) => d.both + d.nrt_only + d.my_only))
const v = nb11.values
const differentDays = v.days.filter((d) => d.within_pct < 95 && d.pixel_days >= 1000)
const hoverDay = ref(null)

// --- Swapping inputs and targets -------------------------------------------------------
const testRow = (i, t, h) => nb11.inputs_targets_test.find((r) => r.inputs === i && r.targets === t && r.horizon === h)
const COMBOS = [
  { i: 'NRT', t: 'NRT', label: 'Live inputs, live targets', note: 'what step 07 measures' },
  { i: 'NRT', t: 'MY', label: 'Live inputs, archive targets', note: 'is the live feed misleading the model?' },
  { i: 'MY', t: 'NRT', label: 'Archive inputs, live targets', note: 'are the live targets penalising it?' },
  { i: 'MY', t: 'MY', label: 'Archive inputs, archive targets', note: 'as in training and testing', emphasis: true },
]
const decisiveRows = [
  ...COMBOS.map((c) => ({ label: c.label, note: c.note, emphasis: c.emphasis,
                          values: Object.fromEntries(H.map((h) => [h, testRow(c.i, c.t, h)?.gain ?? null])) })),
  ...nb11.pipeline_check.length ? [{
    label: 'Archive, with a longer history', note: '25 more days before the first issue day, as in testing',
    values: Object.fromEntries(H.map((h) => [h, nb11.pipeline_check.find((r) => r.horizon === h)?.gain_point ?? null])),
  }] : [],
]
const testDays = (h) => testRow('NRT', 'NRT', h)?.issue_days
const spread = (h) => {
  const g = COMBOS.map((c) => testRow(c.i, c.t, h)?.gain).filter((x) => x !== undefined && x !== null)
  return Math.max(...g) - Math.min(...g)
}

// --- Where the losses come from --------------------------------------------------------
const byDay = nb11.by_day
const modelBetter = byDay.filter((d) => d.better === 'Model').length
const worstDays = [...byDay].sort((a, b) => b.excess_share - a.excess_share).slice(0, 3).sort((a, b) => a.date.localeCompare(b.date))
const worstShare = worstDays.reduce((s, d) => s + d.excess_share, 0)
const maxShare = Math.max(...byDay.map((d) => Math.abs(d.excess_share)))

const sections = [
  { id: 'puzzle', label: 'The puzzle' },
  { id: 'season', label: 'Is it the season?' },
  { id: 'inputs', label: 'Different inputs?' },
  { id: 'same-days', label: 'The same days, twice' },
  { id: 'swap', label: 'Swapping inputs and targets' },
  { id: 'days', label: 'Where the losses come from' },
  { id: 'meaning', label: 'What it means' },
]
</script>

<template>
  <StepLayout number="11" :sections="sections">
    <template #lead>
      On live data the model has fallen behind a simple rule it beat in every test. This step looks for the reason, one
      suspect at a time, and finds that it is not the live data at all.
    </template>

    <section id="puzzle" class="article scroll-mt-24">
      <h2>The puzzle</h2>
      <p>
        In the 2025 test (step 09) the model beat the blend rule, a mix of the latest observation and the usual value for the month,
        at every lead time. Scored live from {{ longDate(nb11.first_issue_day) }}
        (<router-link :to="stepPath(step07)" class="font-semibold text-teal-800 hover:underline">step 07</router-link>), it fell
        behind it: {{ H.map((h) => `${signed(windowRow(LIVE, h).gain)} at ${days(h)}`).join(', ') }}.
      </p>
      <p>There are four natural suspects, and this step tests each in turn:</p>
      <ol>
        <li><strong>The season.</strong> The live record is three weeks of late autumn, not a whole year.</li>
        <li><strong>The inputs.</strong> Live temperature comes from a different product, on a coarser grid.</li>
        <li><strong>The live chlorophyll itself.</strong> It is processed in a hurry, with less information than the archive.</li>
        <li><strong>The live code.</strong> The live calendar starts with the archive, so the first forecasts have a shorter history.</li>
      </ol>
      <p>
        Two notebooks do the work: the first compares the live weeks with the same weeks of every earlier year; the second compares the
        live feed with the archive on the same days, which became possible once the archive’s interim updates, about ten days behind,
        covered the live record.
      </p>
    </section>

    <section id="season" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Is it the season?</h2>
        <p>
          If late autumn is simply a bad time for the model, it should also lose in the same weeks of earlier years. So the model, the
          blend rule and “no change” were scored on the archive for exactly the live window, issue days from {{ windowText }}, in every year
          from {{ years[0] }}, with the same rules as step 07.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">The model against the blend rule, {{ windowText }}</div>
        <div class="figure-subtitle">Reduction in typical log error; dot = estimate, line = 95% range from resampling whole days</div>
        <div class="mt-5">
          <IntervalChart :groups="windowGroups" />
        </div>
        <figcaption class="figure-caption">
          The model was trained on issue days up to {{ longDate(nb11.trained_until) }}, so only {{ unseen.join(', ') }} is a fair test;
          earlier years flatter it. Each panel has its own scale.
        </figcaption>
      </figure>

      <figure class="figure">
        <div class="figure-title">Year by year, the same weeks</div>
        <div class="figure-subtitle">Gain of the model over the blend rule; teal = model better</div>
        <div class="mt-5">
          <GainTable :rows="yearRows" />
        </div>
        <figcaption class="figure-caption">
          A dash: fewer than 10 scored issue days, too few for a reliable figure.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          In the archive the model wins at 1 and 4 days in all {{ archiveYears.length }} years, by at least
          {{ Math.min(minArchiveGain(1), minArchiveGain(4)).toFixed(0) }}%; at 7 days it wins in {{ yearsModelWins(7) }} of them. The live
          result is outside anything seen before at 1 and 4 days.
        </p>
        <p>
          Nor was this autumn unusually hard. The error of “no change” measures how much chlorophyll changed from day to day, independent of
          any model. Live it was {{ noChange(years.find((y) => y.startsWith('Live')), 1).toFixed(3) }} at 1 day, inside the archive’s range of
          {{ noChangeRange(1)[0].toFixed(3) }}–{{ noChangeRange(1)[1].toFixed(3) }}. In {{ hardestYear }}, the hardest year
          ({{ noChange(hardestYear, 1).toFixed(3) }}), the model still beat the blend rule by {{ yearRow(hardestYear, 1).gain.toFixed(0) }}%.
          The season is not the answer.
        </p>
      </div>
    </section>

    <section id="inputs" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Different inputs?</h2>
        <p>
          The blend rule uses only the latest chlorophyll. The model also uses temperature and inputs derived from chlorophyll, such as its
          neighbourhood and recent trend. An input that looks different live would hurt the model and not the blend. Each input’s live average
          was compared with the same weeks in the archive:
        </p>
      </div>

      <div class="overflow-x-auto my-6">
        <table class="data-table">
          <thead><tr><th>Input</th><th class="text-right">Live</th><th class="text-right">Archive</th>
            <th class="text-right">Archive, yearly averages</th><th class="text-right">Shift</th></tr></thead>
          <tbody>
            <tr v-for="r in shifts" :key="r.input">
              <td class="font-semibold text-ink-950">{{ NAMES[r.input] }}</td>
              <td class="num">{{ fmtMean(r.live_mean) }}</td>
              <td class="num">{{ fmtMean(r.my_mean) }}</td>
              <td class="num">{{ fmtRange(r.my_yearly) }}</td>
              <td class="num">{{ r.shift_sd > 0 ? '+' : '−' }}{{ Math.abs(r.shift_sd).toFixed(2) }} s.d.</td>
            </tr>
          </tbody>
        </table>
        <p class="mt-2 text-xs text-slate-500">
          The inputs that differ most, over pixels with a usable latest observation; shift = live minus archive, in archive standard deviations.
          Temperatures in °C.
        </p>
      </div>

      <div class="article">
        <p>
          The live autumn was cool and cloudier than most (fewer observations in the past week), but every average lies within, or at the very
          edge of, the range of earlier years. Nothing stands out. Temperature remained a suspect, being a different product, so the model was
          re-scored with temperature hidden, as on a fully cloudy day:
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">With and without temperature, {{ windowText }}</div>
        <div class="figure-subtitle">Gain of the model over the blend rule</div>
        <div class="mt-5">
          <GainTable :rows="temperatureRows" />
        </div>
      </figure>

      <div class="article">
        <p>
          Hiding temperature costs the model a little in the archive, as it should, and changes the live result little at 1 and 4 days
          ({{ signed(liveHidden(1)) }} and {{ signed(liveHidden(4)) }}). It is not the cause.
        </p>
      </div>
    </section>

    <section id="same-days" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>The same days, twice</h2>
        <p>
          The archive’s interim updates run about ten days behind real time, much sooner than the month documented. By
          {{ longDate(nb11.my_retrieved_utc.slice(0, 10)) }} they covered {{ shortDate(nb11.overlap_days[0]) }} – {{ shortDate(nb11.overlap_days[1]) }},
          so the live chlorophyll and the archive chlorophyll could be compared for the same pixels on the same days.
        </p>
      </div>

      <div class="grid gap-4 sm:grid-cols-4">
        <StatTile label="Coverage" :value="`${((100 * totals.nrt) / totals.my).toFixed(0)}%`"
                  :detail="`live pixel-days as a share of the archive’s (${fmt(totals.nrt)} of ${fmt(totals.my)})`" />
        <StatTile label="Typical difference" :value="v.rmsd.toFixed(3)"
                  :detail="`in log10, where both observed; about ${pctChange(v.rmsd).toFixed(0)}%`" />
        <StatTile label="Correlation" :value="v.correlation.toFixed(3)" :detail="`over ${fmt(v.pixel_days)} pixel-days`" />
        <StatTile label="Near-identical" :value="`${v.within_pct.toFixed(0)}%`" detail="of pixel-days within ±0.05 in log10 (±12%)" />
      </div>

      <figure class="figure">
        <div class="figure-title">Pixels observed each day, live feed and archive</div>
        <div class="figure-subtitle">Grey: seen by both. Blue: archive only. Red: live feed only</div>
        <div class="mt-5">
          <div class="flex items-end gap-[3px] h-40" role="img" aria-label="Daily pixels observed by each product">
            <div v-for="d in coverage" :key="d.date" class="flex-1 flex flex-col justify-end h-full cursor-default"
                 @mouseenter="hoverDay = d" @mouseleave="hoverDay = null">
              <div class="bg-[#e34948]" :style="{ height: `${(100 * d.nrt_only) / maxPixels}%` }"></div>
              <div class="bg-[#3987e5]" :style="{ height: `${(100 * d.my_only) / maxPixels}%` }"></div>
              <div class="bg-[#9e9b93] rounded-b-sm" :style="{ height: `${Math.max((100 * d.both) / maxPixels, d.both ? 0.8 : 0)}%` }"></div>
            </div>
          </div>
          <div class="mt-1 flex justify-between font-mono text-[10px] text-slate-500">
            <span>{{ shortDate(coverage[0].date) }}</span><span>{{ shortDate(coverage[coverage.length - 1].date) }}</span>
          </div>
          <div class="mt-2 h-5 text-xs text-slate-600 tabular-nums">
            <template v-if="hoverDay">
              <span class="font-semibold text-ink-950">{{ longDate(hoverDay.date) }}</span>:
              {{ fmt(hoverDay.both) }} by both, {{ fmt(hoverDay.my_only) }} archive only, {{ fmt(hoverDay.nrt_only) }} live only
            </template>
            <template v-else>Hover over a day for its numbers.</template>
          </div>
        </div>
        <figcaption class="figure-caption">
          Low bars are cloudy days. On most days the two products see the same pixels; the archive adds a few on a handful of days.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          The two versions are practically the same product. Where both observed, the live value is within 12% of the archive’s on
          {{ v.within_pct.toFixed(0) }}% of pixel-days, with no overall bias ({{ v.bias > 0 ? '+' : '−' }}{{ Math.abs(v.bias).toFixed(3) }} in log10).
          <template v-if="differentDays.length">
            The differences are concentrated on a few days ({{ differentDays.map((d) => shortDate(d.date)).join(', ') }}), when the archive’s
            reprocessing changed values and, on some of them, added pixels.
          </template>
        </p>
      </div>
    </section>

    <section id="swap" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Swapping inputs and targets</h2>
        <p>
          The decisive test. On the overlapping days, the model and the blend rule were run with chlorophyll inputs from either product, and
          scored against targets from either product, always on the same pixel-days. If the live feed were to blame, the archive rows would
          recover.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Where the chlorophyll comes from makes no difference</div>
        <div class="figure-subtitle">Gain of the model over the blend rule, {{ shortDate(nb11.first_issue_day) }} – {{ shortDate(nb11.overlap_days[1]) }}</div>
        <div class="mt-5">
          <GainTable :rows="decisiveRows" />
        </div>
        <figcaption class="figure-caption">
          {{ testDays(1) }}, {{ testDays(4) }} and {{ testDays(7) }} scored issue days at 1, 4 and 7 days: too few for reliable 95% ranges, but every row is
          scored on the same pixel-days. Temperature is from the live feed throughout.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          All four combinations agree to within {{ Math.max(...H.map(spread)).toFixed(0) }} percentage points. Even with archive inputs and
          archive targets, exactly as in testing, the model falls behind the blend rule in these weeks. Giving the archive run a longer history
          changes nothing either, which clears the live code. The live feed and the pipeline are both cleared: the model really did worse than the
          blend rule on these particular days.
        </p>
      </div>
    </section>

    <section id="days" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>Where the losses come from</h2>
        <p>
          Looking at the live {{ days(nb11.by_day_horizon) }} forecasts one issue day at a time, the model was better than the blend rule on
          {{ modelBetter }} of {{ byDay.length }} days. Its overall loss comes from a few days, because errors are squared and a single large miss
          outweighs several small wins.
        </p>
      </div>

      <figure class="figure">
        <div class="figure-title">Live {{ days(nb11.by_day_horizon) }} forecasts, day by day</div>
        <div class="figure-subtitle">Share of the model’s extra squared error, compared with the blend rule, by issue day</div>
        <div class="mt-5 overflow-x-auto">
          <table class="data-table">
            <thead><tr><th>Issue day</th><th class="text-right">Next-day change</th><th class="text-right">Model error</th>
              <th class="text-right">Blend error</th><th class="min-w-[10rem]">Share of the extra error</th></tr></thead>
            <tbody>
              <tr v-for="d in byDay" :key="d.date" :class="worstDays.includes(d) ? 'bg-rose-50/60' : ''">
                <td class="font-semibold text-ink-950 whitespace-nowrap">{{ shortDate(d.date) }}</td>
                <td class="num">{{ signed(pctChange(d.change)) }}</td>
                <td class="num" :class="d.better === 'Model' ? 'font-semibold text-ink-950' : 'text-slate-500'">{{ d.rmse_model.toFixed(3) }}</td>
                <td class="num" :class="d.better === 'Blend' ? 'font-semibold text-ink-950' : 'text-slate-500'">{{ d.rmse_blend.toFixed(3) }}</td>
                <td>
                  <div class="grid grid-cols-2 items-center">
                    <span class="h-2.5 flex justify-end">
                      <span v-if="d.excess_share < 0" class="h-full rounded-l bg-[#0d9488]" :style="{ width: `${(100 * -d.excess_share) / maxShare}%` }"></span>
                    </span>
                    <span class="h-2.5 flex border-l border-slate-300">
                      <span v-if="d.excess_share > 0" class="h-full rounded-r bg-[#e34948]" :style="{ width: `${(100 * d.excess_share) / maxShare}%` }"></span>
                    </span>
                  </div>
                  <div class="text-center text-[11px] tabular-nums text-slate-500">{{ signed(d.excess_share) }}</div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <figcaption class="figure-caption">
          Next-day change: the average change in observed chlorophyll from the latest observation to the target. Errors are typical log errors.
          Red: the model lost ground that day; teal: it gained. The shares add up to 100%.
        </figcaption>
      </figure>

      <div class="article">
        <p>
          Three days, {{ worstDays.map((d) => `${shortDate(d.date)} (${signed(pctChange(d.change))})`).join(', ') }}, account for
          {{ Math.round(worstShare) }}% of the extra error; the model’s good days win part of it back. Each was a day of sudden change. On the
          falls, the model forecast higher than the blend rule; on the rise, lower. In both cases it stayed closer to the recent level or trend than
          the blend rule did, and missed by more.
        </p>
      </div>
    </section>

    <section id="meaning" class="mt-14 scroll-mt-24">
      <div class="article">
        <h2>What it means</h2>
      </div>
      <div class="mt-4 grid gap-4">
        <div class="card">
          <div class="font-semibold text-ink-950">The live feed is as good as the archive</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The worry behind steps 07 and 08 was that near-real-time chlorophyll, processed in a hurry, would be worse than the archive the
            model learnt from. Around Malta it is practically the same. The model does not need retraining on live data.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">The weakness is sudden change</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            The model wins on ordinary days and loses heavily on a few days when chlorophyll jumps or drops sharply, by
            {{ Math.round(Math.min(...worstDays.map((d) => Math.abs(pctChange(d.change))))) }}–{{ Math.round(Math.max(...worstDays.map((d) => Math.abs(pctChange(d.change))))) }}% on the three worst days. The
            bloom forecasts (<router-link :to="stepPath(step10)" class="font-semibold text-teal-800 hover:underline">step 10</router-link>, now run
            live) struggle on the same days. Nothing in the current inputs announces such a change. Step 05 found that daily wind adds little on
            average, but <router-link :to="stepPath(step12)" class="font-semibold text-teal-800 hover:underline">step 12</router-link> has
            since found that wind <em>events</em>, a few days of strong wind that mix the water, do come before these
            changes, though they do not say which way chlorophyll will move.
          </p>
        </div>
        <div class="card">
          <div class="font-semibold text-ink-950">Still a small sample</div>
          <p class="mt-1 text-sm text-slate-600 leading-relaxed">
            Three weeks of one autumn. The overlap grows by about a day each day, so this step can be re-run every week or two. Whether to
            publish the model, the blend rule or a hedge of the two is now settled by a trial with a rule fixed in advance
            (<router-link :to="stepPath(step07)" class="font-semibold text-teal-800 hover:underline">step 07</router-link>).
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
