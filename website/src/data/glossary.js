// A–Z glossary. Every entry has:
//   slug     – kebab-case anchor + tooltip key
//   term     – display name
//   aliases  – other spellings (used to auto-match text with <Term>)
//   short    – 1-line tooltip definition
//   long     – multi-paragraph full definition
//   example  – concrete plain-English example (optional)
//   category – one of: ocean | data | ml | stats | region
//   seeAlso  – slugs of related terms

export const glossary = [
  // ────────────────────── OCEAN / DOMAIN ──────────────────────
  {
    slug: 'chl-a', term: 'Chlorophyll-a', aliases: ['chl-a', 'chlorophyll'], category: 'ocean',
    short: 'The green pigment that phytoplankton use to photosynthesise. Its concentration in seawater tells you how much microscopic plant life is there.',
    long: 'Chlorophyll-a is the green pigment that microscopic ocean plants (phytoplankton) use to turn sunlight into food. When there is a lot of phytoplankton, there is a lot of chlorophyll-a, so measuring chlorophyll from a satellite tells us how alive the ocean is. It is the bottom of the marine food web and the biological signal you can see from space.',
    example: 'A typical open-Mediterranean value is 0.05–0.5 milligrams per cubic metre of seawater. A bloom can push it above 5.',
    seeAlso: ['phytoplankton', 'bloom', 'ocean-colour'],
  },
  {
    slug: 'phytoplankton', term: 'Phytoplankton', category: 'ocean',
    short: 'Microscopic single-celled plants that drift near the ocean surface. Chlorophyll-a is the standard proxy for their abundance.',
    long: 'Phytoplankton are microscopic, single-celled plants that float near the sunlit surface of the ocean. They photosynthesise, produce roughly half the world\'s oxygen, and are the foundation of the marine food web. Everything from zooplankton to whales ultimately depends on them.',
    seeAlso: ['chl-a', 'bloom'],
  },
  {
    slug: 'bloom', term: 'Bloom', aliases: ['algal bloom'], category: 'ocean',
    short: 'A rapid, temporary increase in phytoplankton in an area — visible from space as a big spike in chlorophyll.',
    long: 'A bloom is a burst of phytoplankton growth in a patch of ocean. Blooms happen when conditions become favourable — nutrients get mixed up from below, sunlight is plentiful, temperature is right. In the Mediterranean the main annual bloom is in winter, when storms mix nutrient-rich deep water into the surface. Some blooms are useful; some are harmful (red tides, cyanobacteria) and matter for fisheries, aquaculture and public health.',
    example: 'A bloom might raise CHL from 0.1 to 2 mg m⁻³ in a few days over a patch of hundreds of square kilometres.',
    seeAlso: ['chl-a', 'phytoplankton'],
  },
  {
    slug: 'oligotrophic', term: 'Oligotrophic', category: 'ocean',
    short: 'A body of water low in nutrients and biological productivity. The open Mediterranean is oligotrophic — clear, blue, low-CHL.',
    long: 'Oligotrophic means "few nutrients". Oligotrophic waters are clear, blue, and support little phytoplankton — chlorophyll values stay low year-round. The opposite is eutrophic (nutrient-rich, green, high productivity). The Mediterranean is one of the most oligotrophic seas in the world, which is why even small blooms show up strongly against the low background.',
    seeAlso: ['chl-a', 'bloom'],
  },
  {
    slug: 'ocean-colour', term: 'Ocean colour', category: 'ocean',
    short: 'The wavelength (blue vs green) of light reflected from the ocean surface. Satellites use it to estimate what is in the water — mainly chlorophyll.',
    long: 'Ocean colour is what satellites see when they look at the sea. Clear open ocean is blue; water full of phytoplankton is greener. By carefully measuring the ratio of light at different wavelengths, algorithms turn colour into an estimate of chlorophyll-a concentration.',
    seeAlso: ['chl-a', 'l3'],
  },
  {
    slug: 'sst', term: 'Sea-surface temperature', aliases: ['SST'], category: 'ocean',
    short: 'How warm the very top layer of the ocean is. Cold water = mixing = nutrients = more plankton; warm water = stratified = fewer nutrients = less plankton.',
    long: 'Sea-surface temperature (SST) is the temperature of the top few metres of the ocean. It matters for chlorophyll because warmer surface water floats on top of colder deep water — this "stratification" keeps nutrients trapped below, so less phytoplankton growth. Colder surface water lets mixing happen and brings nutrients up. In the Mediterranean, SST ranges from ~13 °C in winter to ~28 °C in summer.',
    seeAlso: ['mld', 'chl-a'],
  },
  {
    slug: 'bathymetry', term: 'Bathymetry', category: 'ocean',
    short: 'The topography of the sea floor. How deep is the water at each point.',
    long: 'Bathymetry is the underwater equivalent of a topographic map — it tells you the depth at every location. It matters for chlorophyll because shallow water behaves differently from deep water: coastal shelves get more nutrient input from land, and shelf-break regions have distinctive current dynamics.',
    example: 'The Malta plateau sits at ~150 m, the Sicilian shelf at ~100 m, and the deep Ionian basin south of the plateau plunges to ~3000 m.',
    seeAlso: ['upwelling'],
  },
  {
    slug: 'mld', term: 'Mixed-layer depth', aliases: ['MLD'], category: 'ocean',
    short: 'How deep the surface layer of well-mixed water is. Deep MLD in winter = nutrients brought up; shallow MLD in summer = trapped below.',
    long: 'The mixed layer is the top layer of the ocean where wind and cooling have stirred the water into a uniform slab. MLD is how deep that layer goes. In summer, the top few metres warm up and stratify — MLD is shallow (10–20 m). In winter, storms and cooling deepen the mixing to 100+ m, dragging nutrients from below up into the sunlit zone. That is what triggers winter blooms.',
    seeAlso: ['bloom', 'sst'],
  },
  {
    slug: 'salinity', term: 'Salinity', category: 'ocean',
    short: 'How salty the seawater is (roughly 37 practical salinity units in the Mediterranean).',
    long: 'Salinity is the concentration of dissolved salt in seawater. It matters for chl-a forecasting because different water masses have different salinities — for example, Atlantic-origin water flowing into the Mediterranean is a bit fresher than resident Mediterranean water. Tracking salinity helps track which water mass is at each point.',
    seeAlso: ['ais', 'currents'],
  },
  {
    slug: 'currents', term: 'Currents', category: 'ocean',
    short: 'The horizontal movement of water. Currents carry phytoplankton, nutrients and heat around.',
    long: 'Ocean currents move water — and everything in it, including phytoplankton — from place to place. In our region, the Atlantic-Ionian Stream flows east along the Sicilian shelf, carrying Atlantic-origin water into the eastern Mediterranean. Tracking currents helps explain why chlorophyll patches move from where they start.',
    seeAlso: ['ais', 'ssh'],
  },
  {
    slug: 'ssh', term: 'Sea-surface height', aliases: ['SSH'], category: 'ocean',
    short: 'The height of the ocean surface above a reference level. Small variations (a few centimetres) reveal currents and eddies.',
    long: 'Sea-surface height (SSH) is the height of the ocean surface, measured to a few centimetres by satellite altimeters. Small bumps and dips reflect currents flowing around them (fast currents = tilted surface). SSH is the standard proxy for large-scale ocean circulation — including our Atlantic-Ionian Stream.',
    seeAlso: ['currents', 'ais'],
  },
  {
    slug: 'ais', term: 'Atlantic-Ionian Stream', aliases: ['AIS'], category: 'region',
    short: 'A current that flows east through the Sicily Strait, carrying Atlantic-origin water into the eastern Mediterranean.',
    long: 'The Atlantic-Ionian Stream (AIS) is the main current in our study area. It moves west-to-east through the Sicily Strait, carrying relatively fresh Atlantic-origin water that has already crossed the western Mediterranean. It creates a front — a sharp boundary — between Atlantic-origin and resident Ionian waters. Chlorophyll patches near the front are shaped by the AIS.',
    seeAlso: ['currents', 'salinity', 'ssh'],
  },
  {
    slug: 'upwelling', term: 'Upwelling', category: 'ocean',
    short: 'When wind pushes surface water away from a coast, deeper (colder, nutrient-rich) water rises to replace it. Great for phytoplankton.',
    long: 'Upwelling is the ocean equivalent of stirring the bottom of the pot. When wind blows along a coast in the right direction, the top layer of water gets pushed offshore. Cold, nutrient-rich water rises from below to fill the gap. That extra nutrient supply feeds phytoplankton, so upwelling coastlines are hotspots of ocean productivity. The Sicilian south coast has intermittent upwelling driven by summer easterly winds.',
    example: 'A three-day burst of easterly wind can trigger visible chlorophyll increases along the Sicilian coast a few days later.',
    seeAlso: ['wind-stress', 'bloom'],
  },
  {
    slug: 'wind-stress', term: 'Wind stress', category: 'ocean',
    short: 'The drag force wind puts on the ocean surface. What actually pushes water around.',
    long: 'Wind stress is the force wind exerts on the ocean, roughly proportional to wind speed squared. It is what physically moves water — driving currents, mixing, upwelling. In our model we use ERA5 wind speed and derivatives (like wind-stress curl, the twist of the stress field, which is what triggers upwelling).',
    seeAlso: ['upwelling', 'era5'],
  },
  {
    slug: 'kd490', term: 'KD490', category: 'ocean',
    short: 'How much light at 490 nm gets absorbed as it travels down through the water. High KD490 = murky water = often lots of chlorophyll.',
    long: 'KD490 measures how quickly blue-green light (at 490 nanometres wavelength) is attenuated as it travels down through the water column. Clear ocean has low KD490; water full of phytoplankton or sediment has high KD490. It is an ocean-colour product like chlorophyll itself, and correlates with chl-a strongly.',
    seeAlso: ['ocean-colour', 'chl-a'],
  },
  {
    slug: 'par', term: 'Photosynthetically active radiation', aliases: ['PAR'], category: 'ocean',
    short: 'Sunlight in the wavelengths plants can use (400–700 nm). Drives photosynthesis and therefore chlorophyll growth.',
    long: 'PAR is the amount of sunlight in the wavelengths that photosynthesis actually uses — 400 to 700 nanometres, essentially visible light. It varies with time of day, season, latitude, and cloud cover. More PAR at the surface means more light for phytoplankton to use.',
    seeAlso: ['chl-a', 'era5'],
  },
  {
    slug: 'mediterranean', term: 'Mediterranean Sea', aliases: ['Med'], category: 'region',
    short: 'The semi-enclosed sea between Europe and North Africa. Warm, salty, oligotrophic.',
    long: 'The Mediterranean is a semi-enclosed sea connecting to the Atlantic only through the narrow Strait of Gibraltar. It is warm, salty, low in nutrients, and generally low in productivity compared to the open ocean. It has strong seasonal cycles: a winter mixing / bloom period followed by a stratified oligotrophic summer.',
    seeAlso: ['oligotrophic', 'malta-sicily'],
  },
  {
    slug: 'malta-sicily', term: 'Malta–Sicily Channel', category: 'region',
    short: 'The stretch of sea between Sicily and Malta. Our study area — a 280 × 220 km box with shelf, frontal and open-basin dynamics.',
    long: 'The Malta–Sicily Channel is the passage between Sicily to the north and the Maltese archipelago to the south. It packs three ocean regimes into one box: the Sicilian shelf (shallow, coastal), the Atlantic-Ionian Stream front (mid-depth, fast-flowing), and the deep Ionian basin (offshore, ~3000 m). This mix is why it is scientifically interesting — a small area with multiple ocean physics regimes.',
    seeAlso: ['mediterranean', 'ais'],
  },

  // ────────────────────── DATA / SATELLITE ──────────────────────
  {
    slug: 'l3', term: 'Level 3 (L3)', aliases: ['L3'], category: 'data',
    short: 'Satellite ocean-colour data that has been gridded onto a regular map, but not gap-filled. Cloudy pixels are missing.',
    long: 'Satellite data comes in "levels" that reflect how processed it is. Level 3 (L3) is the "raw-ish" gridded version: individual satellite passes have been binned onto a regular map (say, 1 km × 1 km squares, one per day), but pixels blocked by clouds are just marked missing. So an L3 daily chlorophyll map looks like Swiss cheese — a mix of real values and holes.',
    example: 'On a typical winter day in the Malta–Sicily Channel, ~40% of L3 chlorophyll pixels are cloud-blocked.',
    seeAlso: ['l4', 'cmems', 'multi-sensor'],
  },
  {
    slug: 'l4', term: 'Level 4 (L4)', aliases: ['L4'], category: 'data',
    short: 'Satellite data with cloud gaps filled in by an algorithm (like DINEOF). Looks pretty; contains synthetic values.',
    long: 'Level 4 (L4) is the "polished" version of the same satellite data. An algorithm — most commonly DINEOF, sometimes optimal interpolation — has looked at the L3 Swiss cheese and filled in the missing pixels with estimates based on nearby valid data. The result is a clean, gap-free map that looks great. The tradeoff: about half of what you see might be an educated guess rather than a real observation.',
    seeAlso: ['l3', 'dineof'],
  },
  {
    slug: 'dineof', term: 'DINEOF', category: 'data',
    short: 'A statistical method that fills in missing satellite pixels using patterns from the rest of the dataset. Standard tool for making L4 products.',
    long: 'DINEOF stands for Data Interpolating Empirical Orthogonal Functions. It is a widely-used method for gap-filling: it decomposes the whole time series into spatial and temporal patterns, then uses those patterns to guess what the missing pixels should have been. It is very good at producing smooth, plausible maps — but the smoothness itself is a bias the model imposes.',
    seeAlso: ['l4', 'l3'],
  },
  {
    slug: 'multi-sensor', term: 'Multi-sensor merge', category: 'data',
    short: 'Combining observations from multiple satellites into one daily product. Fewer cloud gaps than any single satellite alone.',
    long: 'Different ocean-colour satellites (MODIS, VIIRS, OLCI, etc.) each pass over a given point at different times of day, from different angles, with different cloud patterns. Merging them means fewer joint clouds — one satellite might miss a spot the other catches. The multi-sensor merged product (what we use) has ~40–60% daily coverage; single-sensor products are worse.',
    seeAlso: ['l3', 'coverage'],
  },
  {
    slug: 'coverage', term: 'Coverage', category: 'data',
    short: 'The fraction of pixels in a map that have valid (non-cloudy) data on a given day. 40% coverage = 60% clouds.',
    long: 'Coverage is the accountancy of missing data. If your map has 100 pixels and 40 of them have real values on a given day (the other 60 are cloud-blocked), coverage is 40%. In our region it varies from ~40% in winter to ~63% in summer.',
    seeAlso: ['l3', 'nan'],
  },
  {
    slug: 'cmems', term: 'CMEMS', category: 'data',
    short: 'The Copernicus Marine Environment Monitoring Service. The EU-run source for most of our satellite and model data.',
    long: 'CMEMS (data.marine.copernicus.eu) is the European Union\'s ocean-monitoring data hub. It publishes free, quality-controlled satellite observations, model outputs and reanalyses of ocean state. We pulled our chlorophyll, SST, salinity, currents, SSH, MLD and KD490 from here.',
    seeAlso: ['reanalysis'],
  },
  {
    slug: 'era5', term: 'ERA5', category: 'data',
    short: 'A weather reanalysis from ECMWF — the best-available gridded record of past atmospheric conditions.',
    long: 'ERA5 is the fifth-generation atmospheric reanalysis produced by the European Centre for Medium-Range Weather Forecasts (ECMWF). It combines observations and a weather model to produce a consistent hourly record of atmospheric conditions (wind, temperature, radiation, etc.) at ~31 km resolution back to 1940. We use it for wind.',
    seeAlso: ['reanalysis', 'wind-stress'],
  },
  {
    slug: 'reanalysis', term: 'Reanalysis', category: 'data',
    short: 'A modelled reconstruction of the past that combines observations and physics. Gap-free, consistent, but modelled.',
    long: 'A reanalysis is what you get when you take a physical model (of the atmosphere, or the ocean, etc.) and force it with every available past observation. The output is a consistent, gap-free reconstruction of what conditions probably were. It is not raw observation — it is model plus observations. For predictors (inputs to a model) this is fine; for the target (thing you predict) it can be circular.',
    seeAlso: ['era5', 'l4'],
  },
  {
    slug: 'grid', term: 'Grid', aliases: ['pixel'], category: 'data',
    short: 'A regular array of cells (pixels) covering an area. Each satellite product has a native grid — we regrid them all onto the finest one for our model.',
    long: 'Ocean data is stored on grids — regular arrays of cells covering a region. Each cell (pixel) has one value per variable per time step. Different products have different grids: chlorophyll is 1 km, SST is 5 km, wind is 31 km. To combine them, we interpolate everything onto the finest grid (chlorophyll\'s 1 km).',
    seeAlso: ['regridding', 'coverage'],
  },
  {
    slug: 'regridding', term: 'Regridding', category: 'data',
    short: 'Interpolating a coarse grid onto a fine grid so multiple datasets align cell-for-cell.',
    long: 'When you need to combine a 5-km product and a 1-km product, you re-project one onto the other. This is regridding. For a tree-based model, regridding a 31-km wind field onto a 1-km grid does not invent 1-km wind detail — it just makes the arrays addressable together. Each 1-km chlorophyll pixel just gets tagged with the same wind value as its surrounding 31-km cell.',
    seeAlso: ['grid'],
  },
  {
    slug: 'etopo', term: 'ETOPO 2022', category: 'data',
    short: 'NOAA\'s global bathymetry / topography dataset. We use it for water depth in the study area.',
    long: 'ETOPO 2022 is a NOAA global gridded dataset of land elevation and sea-floor depth, at 15 arc-second resolution (about 460 m). We use it for water depth, which becomes the `depth_m` feature the model can read.',
    seeAlso: ['bathymetry'],
  },
  {
    slug: 'netcdf', term: 'NetCDF', category: 'data',
    short: 'The standard file format for multidimensional scientific data. Every satellite product we pull is a NetCDF file.',
    long: 'NetCDF (Network Common Data Form) is the workhorse file format for ocean, atmosphere, and climate data. It stores multi-dimensional arrays (time × latitude × longitude × depth × ...) with metadata attached. Every download in this project produces a .nc file that xarray then reads into Python.',
    seeAlso: ['grid'],
  },

  // ────────────────────── ML / STATS ──────────────────────
  {
    slug: 'forecast-horizon', term: 'Forecast horizon', aliases: ['horizon', 'H+1', 'H+7'], category: 'ml',
    short: 'How far into the future the model predicts. H+1 means "one day ahead"; H+7 means "seven days ahead".',
    long: 'The forecast horizon is the lead time between "now" and "the prediction". H+1 means "given data through today, predict tomorrow\'s chlorophyll". H+7 is a week out. Longer horizons are harder — the further ahead you look, the less today\'s conditions determine the outcome.',
    example: 'A weather forecast for tomorrow is horizon +1 day; a forecast for next Sunday is +7 days.',
    seeAlso: ['persistence'],
  },
  {
    slug: 'feature', term: 'Feature', aliases: ['predictor', 'input', 'covariate'], category: 'ml',
    short: 'An input variable the model reads to make a prediction — like SST at time t, or salinity at time t-1.',
    long: 'A feature is one column in the model\'s input table. In our project, features include current chlorophyll, chlorophyll at lag 1/2/3/7/14 days, current SST, wind speed, mixed-layer depth, and so on. The model learns from many features together how to predict the target.',
    seeAlso: ['target'],
  },
  {
    slug: 'target', term: 'Target', aliases: ['label', 'y'], category: 'ml',
    short: 'The thing the model is trying to predict. For us: log10 chlorophyll at t+h days.',
    long: 'The target is the "y" — the value the model tries to predict. For horizon +3, our target is the chlorophyll value 3 days ahead at the same pixel. During training, the model sees a lot of (features, target) pairs and learns the mapping.',
    seeAlso: ['feature'],
  },
  {
    slug: 'train-val-test', term: 'Train / validation / test split', aliases: ['train', 'val', 'test'], category: 'ml',
    short: 'Slice data into three chunks. Train on one, tune on the second, score on the third. Never mix them.',
    long: 'Standard ML practice: split your data into three non-overlapping subsets. The model is fit on the training set. Hyperparameters (like when to stop training) are picked on the validation set. The final quality number comes from scoring on the test set, which the model has never seen. Mixing sets leaks information from the future into the past and inflates scores.',
    seeAlso: ['leakage', 'walk-forward'],
  },
  {
    slug: 'chronological-split', term: 'Chronological split', category: 'ml',
    short: 'When your data is a time series, cut it by time — never shuffle. Train on the past; test on the future.',
    long: 'In a time series, random shuffling of the split ruins everything. If you randomly assign days to train/test, the model sees data from Wednesday in training and Tuesday in test — Tuesday is "future" relative to the test day, so the model peeks. The right thing is to draw a date line: everything before is train, everything after is test.',
    seeAlso: ['train-val-test', 'leakage'],
  },
  {
    slug: 'walk-forward', term: 'Walk-forward validation', category: 'ml',
    short: 'Do multiple chronological splits, each with a slightly different test window. Gives you error bars, not a single number.',
    long: 'Instead of drawing one date line and getting one test number, walk-forward draws many lines. Fold 1: train on Q1–Q4 2021, test on Q1 2022. Fold 2: train on Q1 2021–Q1 2022, test on Q2 2022. And so on. You get 8 test numbers instead of 1, so you can report mean ± std. That is what makes a claim publication-grade — it is robust to the specific window you happened to hold out.',
    example: 'Judging a violinist from one concert is a single split. Judging them from 8 concerts across a year is walk-forward.',
    seeAlso: ['train-val-test', 'chronological-split'],
  },
  {
    slug: 'leakage', term: 'Leakage', category: 'ml',
    short: 'When information from the future accidentally sneaks into training. Produces impressive-looking scores that mean nothing.',
    long: 'Leakage is when the model has access to data during training that it would not have in the real world. Random shuffling of a time series is one form (future days leak into the training window). Building a normalisation using the whole dataset (including test) is another. A leaky model reports high scores that vanish the moment you deploy it. Our Gate 4 explicitly checks for leakage.',
    seeAlso: ['chronological-split', 'gate'],
  },
  {
    slug: 'baseline', term: 'Baseline', category: 'ml',
    short: 'The simplest possible predictor. Your fancy model has to beat it, or it is not doing anything useful.',
    long: 'A baseline is a stupid-simple predictor whose only job is to set the floor. For forecasting we use persistence ("tomorrow = today") and climatology ("tomorrow = seasonal average"). A machine-learning model that cannot beat both is worthless — you would be better off with the stupid predictor.',
    seeAlso: ['persistence', 'climatology'],
  },
  {
    slug: 'persistence', term: 'Persistence baseline', aliases: ['persistence'], category: 'ml',
    short: 'Predict tomorrow = today. Shockingly hard to beat at short horizons for slowly-changing systems.',
    long: 'The persistence baseline says: whatever chlorophyll is today, that is what it will be tomorrow. Zero parameters, zero training. It is surprisingly hard to beat at H+1 because chlorophyll changes slowly day-to-day. As the horizon grows, "today = tomorrow" gets less true and persistence degrades — that is where the model must show its edge.',
    seeAlso: ['baseline', 'climatology'],
  },
  {
    slug: 'climatology', term: 'Climatology baseline', aliases: ['climatology'], category: 'ml',
    short: 'Predict tomorrow = the historical average for tomorrow\'s date. Flat across horizons; useful at long leads.',
    long: 'The climatology baseline says: for this pixel on this day-of-year, the historical average is X. Predict X, always. It ignores what happened yesterday, and its accuracy does not depend on horizon (it is the same seasonal average whether you predict 1 day or 7 days ahead). It beats persistence at very long horizons because "average" is more reliable than "yesterday" once yesterday is too far away.',
    seeAlso: ['baseline', 'persistence'],
  },
  {
    slug: 'xgboost', term: 'XGBoost', category: 'ml',
    short: 'A gradient-boosted decision-tree library. Fast, accurate on tabular data, handles missing values natively.',
    long: 'XGBoost is a widely-used library that builds an ensemble of decision trees, each one trained to correct the mistakes of the previous. It is the go-to choice for tabular data where you want fast, accurate, well-behaved models. Crucially for us, it handles NaN values natively — the tree learns which direction to send missing data at each split.',
    seeAlso: ['nan', 'gradient-boosting'],
  },
  {
    slug: 'gradient-boosting', term: 'Gradient boosting', category: 'ml',
    short: 'Building a strong model by adding many weak models, each correcting the previous one\'s errors.',
    long: 'Gradient boosting is an ensemble method: you start with a bad predictor, look at where it is wrong, then train a second model to specifically fix those errors, then a third to fix what the first two got wrong, and so on. After hundreds or thousands of tiny corrections, the ensemble is very accurate. XGBoost is a fast, popular implementation.',
    seeAlso: ['xgboost'],
  },
  {
    slug: 'nan', term: 'NaN', aliases: ['missing', 'NA'], category: 'ml',
    short: '"Not a Number" — the code for "we do not know this value". Cloud gaps are NaN.',
    long: 'NaN literally stands for "Not a Number" — a floating-point convention for "this value is missing". In our L3 chlorophyll data, every cloud-blocked pixel is NaN. Most ML methods refuse to eat NaN and require you to impute it (replace it with a made-up value). XGBoost is different: it treats NaN as a valid state and learns what to do with it.',
    seeAlso: ['l3', 'xgboost', 'imputation'],
  },
  {
    slug: 'imputation', term: 'Imputation', category: 'ml',
    short: 'Replacing missing values with guesses (mean, interpolation, etc.). Convenient for the model, dishonest about the data.',
    long: 'Imputation is filling in missing values so a model can consume the data. Common strategies: replace with the mean, with the median, or with an interpolated value from neighbours. It is often necessary — but it means the model is training on partly-invented data, which is exactly the problem L4 has and the reason we avoid it.',
    seeAlso: ['l4', 'nan'],
  },
  {
    slug: 'feature-importance', term: 'Feature importance', category: 'ml',
    short: 'How much each feature contributes to the model. Two rigorous ways: permutation (shuffle it, see how much RMSE grows) and ablation (remove it, retrain, see how much R² drops).',
    long: 'Feature importance is any method for asking "which features matter". Naive tree-based importance (default gain) is unreliable when features are correlated. Better options: permutation importance (shuffle a feature\'s column and measure the score drop) and ablation (drop the feature entirely, retrain, measure the score drop). These two often disagree — which is itself informative.',
    seeAlso: ['permutation', 'ablation', 'shap'],
  },
  {
    slug: 'permutation', term: 'Permutation importance', category: 'ml',
    short: 'Shuffle a feature\'s column randomly on the validation set. How much did RMSE grow? That is its importance.',
    long: 'Permutation importance: take the trained model, take the validation set, randomly reshuffle one column (breaking its link to the target while keeping its overall distribution). Predict again. The bigger the drop in score, the more the model was leaning on that column. Do it in groups (shuffle all wind columns together) to see joint contributions.',
    seeAlso: ['feature-importance', 'ablation'],
  },
  {
    slug: 'ablation', term: 'Ablation', category: 'ml',
    short: 'Remove a feature (or group of features) entirely, retrain the model, see how much worse it gets. The rigorous test of essentiality.',
    long: 'Ablation: literally amputate the feature. Take it out of the input table entirely. Retrain the model from scratch. Measure the new score. The difference from baseline is what removing that feature costs. Ablation often disagrees with permutation because it lets substitute features step up. A feature that looks essential by permutation might be redundant in ablation (some other feature filled in).',
    seeAlso: ['permutation', 'feature-importance'],
  },
  {
    slug: 'shap', term: 'SHAP', category: 'ml',
    short: 'A method that assigns each feature a per-row "contribution" score using game-theory. Explains individual predictions, not just averages.',
    long: 'SHAP (SHapley Additive exPlanations) is an importance method with a rigorous theoretical foundation (Shapley values from cooperative game theory). It assigns each feature a signed contribution for each prediction, so you can say "for this specific pixel on this specific day, the model raised its prediction by 0.12 log-units because SST was low". Averaging absolute SHAP values over many rows gives a whole-model importance ranking.',
    seeAlso: ['feature-importance'],
  },
  {
    slug: 'autoregressive', term: 'Autoregressive', aliases: ['lag features'], category: 'ml',
    short: 'Using past values of the same variable to predict its future. Lag-1 chlorophyll = chlorophyll one day ago at the same pixel.',
    long: 'Autoregressive means the feature is a past value of the target itself. Our features include lag-1, lag-2, lag-3, lag-7 and lag-14 chlorophyll. Autoregression is powerful in slowly-changing systems: what happened recently is a strong hint about what happens next. It also creates a persistent baseline that is hard to beat.',
    seeAlso: ['persistence', 'rolling'],
  },
  {
    slug: 'rolling', term: 'Rolling statistics', category: 'ml',
    short: 'Aggregates over a moving window. rolling(7).mean() is the 7-day average, updated each day.',
    long: 'A rolling statistic slides a window along the time axis and computes something (mean, std, min, max) inside it. Our features include 7-day rolling mean of log-chlorophyll and 7-day rolling std. They smooth out day-to-day noise and expose short-term trends.',
    seeAlso: ['autoregressive'],
  },
  {
    slug: 'log-scale', term: 'log10 scale', aliases: ['log-transform'], category: 'stats',
    short: 'Squishing a variable that spans many orders of magnitude by taking its base-10 logarithm. Chlorophyll is skewed; log-chl is symmetric.',
    long: 'Chlorophyll values span 0.01 to 10+ mg/m³ — three orders of magnitude, heavily skewed. Taking log10 turns that into a range from -2 to +1 that behaves symmetrically. It also makes errors multiplicative rather than additive: an RMSE of 0.1 in log-space means "about ±26% in the raw scale", regardless of whether you are at low or high chlorophyll. Every serious ocean-colour paper works in log space.',
    example: 'log10(0.1) = -1; log10(1) = 0; log10(10) = 1. Each step of 1 is a factor of 10 in the raw value.',
    seeAlso: ['rmse'],
  },
  {
    slug: 'r-squared', term: 'R²', aliases: ['R-squared', 'coefficient of determination'], category: 'stats',
    short: 'How much of the variation the model explains, from 0 (nothing) to 1 (perfect). "R² = 0.8" means the model explains 80% of the variance.',
    long: 'R² is the standard "how good is the fit" score for regression. It compares the model\'s errors to the errors of just always predicting the mean. R² = 1 is perfect; R² = 0 is no better than predicting the mean; R² < 0 is worse than the mean. For chlorophyll forecasting, R² around 0.7–0.85 at H+1 is realistic.',
    example: 'R² = 0.86 means the model captures 86% of the variance in log-chlorophyll that a mean-only predictor would leave unexplained.',
    seeAlso: ['rmse'],
  },
  {
    slug: 'rmse', term: 'RMSE', aliases: ['Root Mean Squared Error'], category: 'stats',
    short: 'The typical size of the model\'s error, in the same units as the target. Smaller is better.',
    long: 'Root Mean Squared Error: the square root of the average squared error. It has the same units as the target. In log10 space, an RMSE of 0.10 means "typical error factor of 10^0.10 ≈ 1.26" — the prediction is typically within ±26% of the true chlorophyll value.',
    example: 'RMSE = 0.10 in log-space ≈ ±26% error in linear chlorophyll.',
    seeAlso: ['r-squared', 'log-scale'],
  },
  {
    slug: 'std', term: 'Standard deviation', aliases: ['σ', 'sigma'], category: 'stats',
    short: 'A measure of spread. If R² = 0.65 ± 0.12 over folds, the σ = 0.12 tells you how much the score varies across folds.',
    long: 'The standard deviation (σ) is the classical measure of "how spread out are these numbers around their mean". For our walk-forward folds, we report R² as "mean ± std" — e.g. 0.65 ± 0.12 means most folds fall between 0.53 and 0.77.',
    seeAlso: ['walk-forward'],
  },
  {
    slug: 'correlation', term: 'Correlation (ρ)', aliases: ['ρ', 'rho', 'Spearman'], category: 'stats',
    short: 'How strongly two variables move together. ρ = 1: perfect positive; ρ = 0: no relationship; ρ = −1: perfect opposite.',
    long: 'Correlation quantifies whether two variables tend to rise and fall together. Spearman correlation is the rank-based version (works for non-linear monotonic relationships). When two of our features have |ρ| > 0.9 they carry essentially the same information — the feature-importance measures will get confused unless we handle them as a group.',
    seeAlso: ['permutation', 'ablation'],
  },
  {
    slug: 'doy', term: 'Day of year (DOY)', aliases: ['doy', 'day-of-year'], category: 'stats',
    short: 'Which day of the year it is, from 1 (Jan 1) to 365/366 (Dec 31). We encode it as sin/cos so the model sees it as cyclic.',
    long: 'DOY runs from 1 to 366. The tricky bit for a model is that DOY 365 and DOY 1 are next to each other in real time — the calendar wraps. To let the model use that, we replace DOY with two features: sin(2π · DOY / 365) and cos(2π · DOY / 365). Now Jan 1 and Dec 31 have similar values and the model sees the seasonal cycle correctly.',
    seeAlso: ['climatology'],
  },

  // ────────────────────── BLOOM DETECTION METRICS ──────────────────────
  {
    slug: 'pod', term: 'POD (Probability of Detection)', category: 'stats',
    short: 'Of the real blooms that happened, what fraction did we correctly flag? POD = TP / (TP + FN).',
    long: 'POD, also called recall or sensitivity, answers: "of all the blooms that actually happened, what fraction did the model catch?" It goes from 0 (missed everything) to 1 (caught everything). POD is a hit rate.',
    seeAlso: ['far', 'f1'],
  },
  {
    slug: 'far', term: 'FAR (False-Alarm Ratio)', category: 'stats',
    short: 'Of the alarms we raised, what fraction were wrong? FAR = FP / (TP + FP). Lower is better.',
    long: 'FAR (false-alarm ratio) answers: "of all the blooms the model predicted, what fraction were actually not real?" FAR = 0 means every alarm was a real bloom (great); FAR = 1 means every alarm was a false alarm (terrible). Note: FAR is not the same as false-positive rate.',
    seeAlso: ['pod', 'f1'],
  },
  {
    slug: 'csi', term: 'CSI (Critical Success Index)', category: 'stats',
    short: 'The Jaccard overlap between predicted blooms and real blooms. CSI = TP / (TP + FN + FP).',
    long: 'CSI (also called Jaccard, or Threat Score) rewards a model that both catches real blooms and does not raise false alarms. It goes from 0 (nothing overlaps) to 1 (perfect agreement). CSI is a single-number summary that balances misses and false alarms.',
    seeAlso: ['pod', 'far', 'f1'],
  },
  {
    slug: 'f1', term: 'F1 score', category: 'stats',
    short: 'The harmonic mean of precision and recall. Single-number summary of binary classification skill. F1 ≥ 0.5 is the operational bar.',
    long: 'F1 combines precision (of the alarms you raised, how many were real) and recall (of the real events, how many did you catch). Because it is a harmonic mean, it penalises being terrible at either one. F1 = 1 is perfect; F1 = 0 is useless. The convention in event-detection literature is that F1 ≥ 0.5 makes the detector operationally useful.',
    seeAlso: ['pod', 'far'],
  },
  {
    slug: 'true-positive', term: 'TP / FP / TN / FN', category: 'stats',
    short: 'The 2×2 counting behind every binary detection metric. TP = we said yes AND it was yes; FP = we said yes BUT it was no; etc.',
    long: 'For any yes/no prediction, you can count four outcomes: True Positive (predicted yes, was yes), False Positive (predicted yes, was no — a false alarm), True Negative (predicted no, was no), False Negative (predicted no, was yes — a miss). Every classification metric — precision, recall, POD, FAR, F1, CSI — is built from these four counts.',
    seeAlso: ['f1', 'pod', 'far'],
  },
  {
    slug: 'gate', term: 'Validation gate', category: 'ml',
    short: 'A programmatic check at the end of each pipeline stage. Must pass before the next stage begins.',
    long: 'A validation gate is a numeric assertion — "R² > 0.6", "leakage assertion passes", "at least one bloom definition clears F1 = 0.5" — that has to hold before we move on. Gates are the scientific contract. A gate that fails is a finding to investigate, not a rug to sweep it under. This project has 12 gates, one per notebook, and all 12 pass.',
    seeAlso: ['leakage'],
  },

  // ────────────────────── MISC ──────────────────────
  {
    slug: 'unit-mg-m3', term: 'mg m⁻³', category: 'stats',
    short: 'Milligrams per cubic metre — the unit for chlorophyll concentration. Roughly equivalent to μg/L.',
    long: 'The concentration unit for chlorophyll-a. One cubic metre of seawater is one tonne; open-Mediterranean chlorophyll of 0.1 mg m⁻³ means 0.1 milligrams of chlorophyll in one tonne of water. Very dilute. Blooms push it to several mg m⁻³.',
    seeAlso: ['chl-a'],
  },
]

export function findTerm(query) {
  const q = query.toLowerCase()
  return glossary.find(g => g.slug === q || g.term.toLowerCase() === q ||
    (g.aliases || []).some(a => a.toLowerCase() === q))
}

export function byCategory() {
  return glossary.reduce((acc, g) => {
    (acc[g.category] = acc[g.category] || []).push(g); return acc
  }, {})
}

export const categoryLabels = {
  ocean:  'Oceanography',
  region: 'Region-specific',
  data:   'Satellite & data products',
  ml:     'Machine learning',
  stats:  'Statistics & metrics',
}
