<script setup>
import SectionHeader from '../components/SectionHeader.vue'
import Term from '../components/Term.vue'
import ExplainerBox from '../components/ExplainerBox.vue'
</script>

<template>
  <div class="container-page py-12 md:py-16">
    <SectionHeader
      eyebrow="Start here"
      title="A friendly guide to everything on this site"
      lead="If any of the finding pages felt dense — this page unpacks it all in plain English. No prior background assumed."
    />

    <!-- What we're doing -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">What are we actually doing?</h2>
      <p class="text-lg text-slate-700 leading-relaxed">
        We built a computer program that looks at satellite pictures of the sea near Malta and Sicily,
        then makes a prediction: <em>how much microscopic plant life will be there tomorrow, and the day after, and the day after that</em>
        — out to a week ahead.
      </p>
      <p class="text-slate-700 leading-relaxed mt-3">
        "How much plant life" is measured by
        <Term slug="chl-a">chlorophyll-a</Term> — the green pigment those plants use to photosynthesise.
        More chlorophyll means more <Term slug="phytoplankton">phytoplankton</Term>, which are the microscopic
        floating plants at the bottom of the marine food web. Their concentration matters for fisheries,
        for climate, for algal-bloom early warning, and just for basic scientific understanding of the ocean.
      </p>

      <ExplainerBox title="Why should anyone care?" tone="primer">
        <p>
          Chlorophyll changes over time reveal a lot: unusual warmth, coastal pollution, harmful blooms,
          shifts in fish populations, changes in how the ocean absorbs carbon from the atmosphere. A
          reliable forecast a few days ahead is useful for:
        </p>
        <ul>
          <li><strong>Fisheries and aquaculture</strong>: predict where fish concentrations will be, or when
            a harmful bloom might hit a fish farm.</li>
          <li><strong>Coastal management</strong>: early warning for beaches, water treatment intake.</li>
          <li><strong>Climate science</strong>: chlorophyll is a proxy for how much carbon phytoplankton
            are pulling out of the atmosphere.</li>
        </ul>
      </ExplainerBox>
    </section>

    <!-- The Region -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">Where — the Malta–Sicily Channel</h2>
      <div class="grid md:grid-cols-3 gap-6 items-start">
        <div class="md:col-span-2">
          <p class="text-slate-700 leading-relaxed">
            Our study area is the stretch of Mediterranean sea between Sicily to the north and the Maltese
            islands to the south — a roughly <strong>280 × 220 kilometre box</strong> in the central
            Mediterranean.
          </p>
          <p class="text-slate-700 leading-relaxed mt-3">
            It is scientifically interesting because it packs together three completely different ocean
            regimes:
          </p>
          <ul class="mt-2 space-y-2 text-slate-700">
            <li>🏖️ The <strong>Sicilian shelf</strong> — shallow coastal water with intermittent wind-driven
              <Term slug="upwelling">upwelling</Term> (colder water rising up from below).</li>
            <li>🌊 The <Term slug="ais">Atlantic-Ionian Stream</Term> — a fast current carrying Atlantic-origin
              water eastward through the middle of our box.</li>
            <li>🌐 The <strong>deep Ionian basin</strong> — offshore water going down to ~3000 metres, with
              its own slow-moving open-ocean dynamics.</li>
          </ul>
        </div>
        <img :src="'figs/02_coverage_map.png'" alt="Map of the region"
             class="rounded-lg border border-slate-200 w-full h-auto" />
      </div>
    </section>

    <!-- The Bet: L3 vs L4 -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">The big methodological bet — L3 vs L4</h2>
      <p class="text-slate-700 leading-relaxed mb-4">
        Every day, satellites orbiting the Earth photograph the ocean's colour. From the colour, an
        algorithm estimates the chlorophyll concentration at every pixel of a 1 km × 1 km grid. But
        there is one big problem: <strong>clouds</strong>. Wherever there is a cloud between the
        satellite and the ocean, there is no measurement — the pixel is missing.
      </p>

      <div class="grid md:grid-cols-2 gap-4 my-6">
        <div class="card">
          <div class="flex items-center gap-2 mb-2">
            <span class="badge badge-info">L3</span>
            <h3 class="font-bold text-slate-900">Level 3 — the honest version</h3>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">
            A <Term slug="l3">Level 3</Term> product is what you get straight from the satellite, gridded
            onto a map. Every cloud-blocked pixel is left <strong>missing</strong> — a hole where there is no data.
          </p>
          <p class="text-sm text-slate-500 mt-2 italic">
            Looks like Swiss cheese. About 40–60% of pixels are missing on any given day.
          </p>
        </div>
        <div class="card">
          <div class="flex items-center gap-2 mb-2">
            <span class="badge badge-warn">L4</span>
            <h3 class="font-bold text-slate-900">Level 4 — the "fixed up" version</h3>
          </div>
          <p class="text-sm text-slate-700 leading-relaxed">
            A <Term slug="l4">Level 4</Term> product takes L3 and runs a gap-filling algorithm (usually
            <Term slug="dineof">DINEOF</Term>) to fill in the holes with statistically-plausible guesses.
          </p>
          <p class="text-sm text-slate-500 mt-2 italic">
            Looks like a beautiful smooth map. About half of what you see is invented, not observed.
          </p>
        </div>
      </div>

      <p class="text-slate-700 leading-relaxed">
        <strong>Most published research uses L4</strong> because it is convenient — no holes to worry about.
        The problem: when you train a computer model on L4, the model is partly learning to
        <em>agree with the gap-filler</em>, not just to model ocean physics. In real-time operation, no
        magical gap-filler is going to save you — so a model trained on L4 has been trained under
        unrealistically pleasant conditions.
      </p>

      <ExplainerBox title="An analogy for the L3 vs L4 choice" tone="primer">
        <p>
          Imagine training a chef by giving them only perfectly-organised ingredients, pre-measured,
          labelled, arranged in the right order. Then on their first day at the restaurant, the pantry
          is a real pantry — messy, half-empty, some things missing. The perfectly-trained chef panics.
        </p>
        <p>
          <strong>L3 is training the chef in a real pantry from day one.</strong> The chef learns to work
          with missing ingredients. Some dishes come out well; some are compromises. But nothing is a
          surprise on day one at the restaurant.
        </p>
        <p>
          Our bet was: this approach costs us nothing in the top-line score, and gains us honesty about
          what the model will actually do on cloudy days. <router-link to="/findings/l3-vs-l4" class="text-ocean-700 font-semibold">See Finding 01</router-link> for the numbers.
        </p>
      </ExplainerBox>
    </section>

    <!-- The Model -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">The model — why XGBoost, and how it handles gaps</h2>
      <p class="text-slate-700 leading-relaxed">
        Given L3 chlorophyll as our target, we need a machine-learning method that can eat missing
        values without throwing a tantrum. <Term slug="xgboost">XGBoost</Term> is exactly that.
      </p>
      <p class="text-slate-700 leading-relaxed mt-3">
        XGBoost builds a large collection of <strong>decision trees</strong> — like a flowchart of
        yes/no questions. At each question ("is SST above 18 °C?"), the tree splits the data into two
        groups. What XGBoost does uniquely is learn what to do at every question when the answer is
        <Term slug="nan">"we don't know"</Term> (i.e., NaN): it tries sending the missing values left
        or right, and picks whichever gives better predictions. So a cloud gap is not a problem —
        it is a valid state the model has learned to route.
      </p>

      <ExplainerBox title="What does 'gradient boosting' mean?" tone="primer">
        <p>
          <Term slug="gradient-boosting">Gradient boosting</Term> is the training strategy. Start with a
          bad predictor (e.g. "always predict the mean"). Look at where it is wrong. Train a second tree
          specifically to correct those errors. Then a third to correct what the first two missed. And so
          on — hundreds of tiny corrections.
        </p>
        <p>
          After the corrections have accumulated, the whole ensemble is very accurate. XGBoost is one
          fast, popular implementation. It is the go-to tool for tabular data forecasting problems.
        </p>
      </ExplainerBox>
    </section>

    <!-- Baselines & horizons -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">How we know the model is doing something useful — baselines</h2>
      <p class="text-slate-700 leading-relaxed">
        A model that predicts chlorophyll with R² = 0.8 sounds impressive — until you find out that
        "assume tomorrow will be exactly like today" also gets R² = 0.8. The model added zero.
      </p>
      <p class="text-slate-700 leading-relaxed mt-3">
        This is why every forecasting project needs
        <Term slug="baseline">baselines</Term>. We use two:
      </p>
      <ul class="mt-3 space-y-2 text-slate-700">
        <li><strong><Term slug="persistence">Persistence</Term></strong> — "tomorrow's chlorophyll = today's
          chlorophyll". Zero parameters, zero training. Shockingly hard to beat at H+1.</li>
        <li><strong><Term slug="climatology">Climatology</Term></strong> — "tomorrow's chlorophyll = the
          historical average for that date". Also zero parameters. Ignores what happened yesterday. Beats
          persistence at very long horizons.</li>
      </ul>
      <p class="text-slate-700 leading-relaxed mt-3">
        The XGBoost model has to beat both, at every horizon we care about. That is the bar.
      </p>

      <ExplainerBox title="What is a 'forecast horizon'?" tone="primer">
        <p>
          The <Term slug="forecast-horizon">forecast horizon</Term> is how far into the future you predict.
          We use "H+1" for one day ahead, "H+3" for three, "H+7" for seven.
        </p>
        <p>
          Longer horizons are harder — the further you look ahead, the less today's data determines the
          outcome. A H+1 forecast is usually excellent (things change slowly); H+7 is much harder.
        </p>
      </ExplainerBox>
    </section>

    <!-- R² in plain English -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">What R² actually means</h2>
      <p class="text-slate-700 leading-relaxed">
        We use <Term slug="r-squared">R²</Term> (pronounced "R-squared") as our main score. It runs
        from 0 to 1:
      </p>
      <ul class="mt-3 space-y-2 text-slate-700">
        <li><strong>R² = 1.0</strong> — the model predicts perfectly. Every prediction matches reality.</li>
        <li><strong>R² = 0.5</strong> — the model explains half of the variation you see in the data. Half
          of the mystery is solved.</li>
        <li><strong>R² = 0.0</strong> — the model does no better than always guessing the average. It has
          learned nothing.</li>
        <li><strong>R² &lt; 0</strong> — the model is actively worse than the average. You should feel
          bad.</li>
      </ul>
      <p class="text-slate-700 leading-relaxed mt-3">
        Our top result is R² ≈ 0.78 at H+1 (walk-forward average). That means <strong>the model explains
        about 78% of the day-to-day variation in chlorophyll</strong>. Not perfect, but not bad — and
        considerably above what you would guess without a model.
      </p>

      <ExplainerBox title="What does '±' mean in our results?" tone="primer">
        <p>
          When we write "R² = 0.65 ± 0.12", the number after ± is the
          <Term slug="std">standard deviation</Term> across our 8 walk-forward folds. It says how much
          the score varies from window to window. A small ± means the model is stable; a large ± means
          the model's skill depends heavily on which season you test on.
        </p>
        <p>
          Rule of thumb: most of the folds fall within ± of the mean. So 0.65 ± 0.12 means most folds
          score between 0.53 and 0.77. That range is itself a finding — see
          <router-link to="/findings/walk-forward" class="text-ocean-700 font-semibold">Finding 03</router-link>.
        </p>
      </ExplainerBox>
    </section>

    <!-- Validation gates -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">Twelve validation gates — the scientific contract</h2>
      <p class="text-slate-700 leading-relaxed">
        Every stage of our pipeline ends with a <Term slug="gate">validation gate</Term> — an automated
        check that has to pass before the next stage can begin. Gates encode assumptions like:
      </p>
      <ul class="mt-3 space-y-2 text-slate-700">
        <li>"The target and features are aligned in time — no <Term slug="leakage">leakage</Term>." (Gate 4)</li>
        <li>"The model beats <Term slug="persistence">persistence</Term> at H+3 and beyond." (Gate 6)</li>
        <li>"Every covariate group makes the model measurably better." (Gate 8b)</li>
        <li>"The walk-forward score is consistent, with reasonable error bars." (Gate 10)</li>
      </ul>
      <p class="text-slate-700 leading-relaxed mt-3">
        Gates are not there to be silently passed — a gate that fails is a finding to investigate.
        This project has 12 gates and all 12 pass. See <router-link to="/methodology"
        class="text-ocean-700 font-semibold">the Methodology page</router-link> for the full walkthrough.
      </p>
    </section>

    <!-- The four findings in short -->
    <section class="mb-12">
      <h2 class="text-2xl font-bold text-slate-900 mb-6">The four findings, briefly</h2>
      <div class="space-y-4">
        <div class="card">
          <div class="flex items-baseline gap-3 mb-2">
            <span class="badge badge-info font-mono">01</span>
            <h3 class="text-xl font-bold text-slate-900">L3 + native NaN matches L4</h3>
          </div>
          <p class="text-slate-700 leading-relaxed">
            Using honest cloud gaps (L3) and letting XGBoost handle them natively, we score R² = 0.86 at
            H+1 — matching the ≈ 0.85 reported by L4-based systems that use gap-filled data. The
            methodological upgrade costs nothing in headline skill.
            <router-link to="/findings/l3-vs-l4" class="text-ocean-700 font-semibold ml-1">Full analysis →</router-link>
          </p>
        </div>

        <div class="card">
          <div class="flex items-baseline gap-3 mb-2">
            <span class="badge badge-info font-mono">02</span>
            <h3 class="text-xl font-bold text-slate-900">Every group helps, no silver bullet</h3>
          </div>
          <p class="text-slate-700 leading-relaxed">
            We tested each family of predictors (wind, currents, salinity, etc.) two ways. No single new
            group revolutionises the model — but each contributes a little, and collectively they lift
            R² by +0.024 at H+3. The story is "physics matters collectively", not "wind is the key".
            <router-link to="/findings/group-ablation" class="text-ocean-700 font-semibold ml-1">Full analysis →</router-link>
          </p>
        </div>

        <div class="card">
          <div class="flex items-baseline gap-3 mb-2">
            <span class="badge badge-info font-mono">03</span>
            <h3 class="text-xl font-bold text-slate-900">The single split was systematically lucky</h3>
          </div>
          <p class="text-slate-700 leading-relaxed">
            Testing on eight different windows across the year showed the earlier "single-split" score
            was optimistic by 0.09–0.22. Winter quarters are much harder to forecast than autumn — and the
            single split happened to land on autumn. The honest number, with error bars, is what to
            report.
            <router-link to="/findings/walk-forward" class="text-ocean-700 font-semibold ml-1">Full analysis →</router-link>
          </p>
        </div>

        <div class="card">
          <div class="flex items-baseline gap-3 mb-2">
            <span class="badge badge-info font-mono">04</span>
            <h3 class="text-xl font-bold text-slate-900">Bloom detection works, three definitions</h3>
          </div>
          <p class="text-slate-700 leading-relaxed">
            We tested three independent ways of saying "there is a bloom" and all of them work reliably
            — <Term slug="f1">F1 score</Term> stays above 0.59 at every horizon. Operationally, the
            system catches about two-thirds of real bloom days with a false-alarm rate below 45%.
            <router-link to="/findings/bloom-detection" class="text-ocean-700 font-semibold ml-1">Full analysis →</router-link>
          </p>
        </div>
      </div>
    </section>

    <!-- Where to go next -->
    <section class="mb-4">
      <h2 class="text-2xl font-bold text-slate-900 mb-3">Where to go from here</h2>
      <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <router-link to="/methodology" class="card card-hover">
          <div class="font-semibold text-ocean-700 mb-1">Methodology</div>
          <div class="text-sm text-slate-600">All 12 stages, one at a time, with the gate outcomes.</div>
        </router-link>
        <router-link to="/data" class="card card-hover">
          <div class="font-semibold text-ocean-700 mb-1">Data sources</div>
          <div class="text-sm text-slate-600">Every dataset, resolution, and coverage number.</div>
        </router-link>
        <router-link to="/findings/l3-vs-l4" class="card card-hover">
          <div class="font-semibold text-ocean-700 mb-1">Findings</div>
          <div class="text-sm text-slate-600">The four claims, unpacked with interactive charts.</div>
        </router-link>
        <router-link to="/glossary" class="card card-hover">
          <div class="font-semibold text-ocean-700 mb-1">Glossary</div>
          <div class="text-sm text-slate-600">Every acronym and technical term defined.</div>
        </router-link>
      </div>
    </section>
  </div>
</template>
