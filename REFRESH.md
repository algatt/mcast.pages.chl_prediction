# Keeping the experiment and the website up to date

What runs by itself, what to run by hand, and how to publish the website. Commands are run
from the repository root unless a step says otherwise.

| How often | What | Time needed |
|---|---|---|
| Automatic, twice a day | The live archive (step 08) saves new data at 09:00 and 22:15 | — |
| Every few days | Glance at the archive log | 1 min |
| About once a week | Run `07-NRT-Input-Validation.ipynb`, then refresh the website data | ~10 min |
| When you want the site to change | Build, check and deploy the website | ~5 min |
| Every so often | Back up the archive, commit | ~2 min |

---

## The live archive runs by itself

A scheduled job (a macOS *launch agent*) runs `chlforecast/archive.py` — the same code as
`08-NRT-Archive.ipynb` — at **09:00 and 22:15** Malta time. Each run saves any new day the live
Copernicus feed offers, never overwrites a day already saved, and keeps later versions of a day
separately under `revisions/` if Copernicus changes it.

Why those times: Copernicus publishes yesterday's chlorophyll by 20:00 UTC. 22:15 in Malta is
after that all year (20:15 UTC in summer time, 21:15 UTC in winter time), so the complete file
is always saved before it is needed. 09:00 is a safety net.

- **Mac asleep** at a run time: the job runs as soon as it wakes.
- **Mac switched off**: that run is skipped; the next one catches up, as long as no more than
  about a week has passed (the live feed keeps ~9 days of chlorophyll).
- You can still run `08-NRT-Archive.ipynb` by hand at any time; it never duplicates a day.

### Checking that it is working (every few days)

```bash
# The end of the most recent run: what was offered, what was saved, what the archive holds
tail -20 experiment_v2/data/raw/nrt_archive/scheduled_runs.log

# One line per run: how many days each run saved
grep -E "Archive run started|Saved .* new day|Kept .* later version|FAILED" \
  experiment_v2/data/raw/nrt_archive/scheduled_runs.log | tail -20
```

What good looks like: every run ends with the holdings table, **Missing days: None** for every
source, and usually `Saved 1 new day(s)` per product on the evening run. A line with
`Archive run FAILED` gives the reason (often a Copernicus login or network problem; see
*If something goes wrong*).

### Viewing, changing and removing the schedule

The job is defined in `~/Library/LaunchAgents/com.alangatt.chl-archive.plist`.

| To… | Run |
|---|---|
| See whether it is installed | `launchctl list \| grep chl-archive` (prints a line if it is) |
| See its details: times, last exit code, number of runs | `launchctl print gui/$(id -u)/com.alangatt.chl-archive` |
| See the run times only | `grep -A1 -E "Hour\|Minute" ~/Library/LaunchAgents/com.alangatt.chl-archive.plist` |
| Run it right now | `launchctl kickstart gui/$(id -u)/com.alangatt.chl-archive` |
| Pause it (keeps the file) | `launchctl bootout gui/$(id -u)/com.alangatt.chl-archive` |
| Start it again after pausing | `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.alangatt.chl-archive.plist` |
| Remove it completely | pause it (above), then `rm ~/Library/LaunchAgents/com.alangatt.chl-archive.plist` |

In `launchctl print`, **last exit code = 0** means the last run succeeded; anything else means it
failed — the log says why.

**To change the run times:** open the `.plist` file in a text editor, change the `Hour` and
`Minute` numbers (24-hour clock, local time), then pause and start it again so macOS reads the
change:

```bash
launchctl bootout gui/$(id -u)/com.alangatt.chl-archive
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.alangatt.chl-archive.plist
```

Keep one run **after 22:00 Malta time until 24 October 2026** and **after 21:00 from 25 October**
(after 20:00 UTC either way).

---

## About once a week: score the live forecast (step 07)

1. Open `experiment_v2/07-NRT-Input-Validation.ipynb`, check the kernel is the
   `experiment_v2/.venv` one, **Run All**, then **save** (Cmd+S) and shut the kernel down.
2. Step 07 reads everything from the local archive; it does not contact Copernicus. Cell 4
   prints a NOTE if the archive's newest data is older than today — normally the scheduled job
   has already run.
3. What it produces:
   - **Today's live forecast** (cells 4–5), saved in
     `experiment_v2/data/processed/nrt_forecasts/<run time>/`.
   - **Scores of past live forecasts** (cell 6) against what the satellite later saw, for the
     model, the blend rule and "no change". They only count issue days with a complete 7-day
     history in the archive, so the numbers grow over time:
     - **+1 day** is scored from 17 October 2026;
     - **+7 days** from about 25 October;
     - the **95% ranges** appear once a lead time has 10 or more scored issue days (early November).

   Until then the scores are a handful of days and say nothing about skill.

Each run of step 07 creates new `nrt_forecasts/<run time>/` and `nrt_evaluation/<run time>/`
folders. If you ran it several times in one day, delete the extras and keep the last one.

---

## Refreshing the website data

Every number and map on the website comes from a JSON file in `website/src/data/`, made by a
script in `website/scripts/`. Re-run a script when the notebook it reads has been re-run.

**After running step 07** (the usual case):

```bash
experiment_v2/.venv/bin/python website/scripts/build_nb07_data.py
experiment_v2/.venv/bin/python website/scripts/build_nb08_data.py
```

Each prints a short summary — check the dates and day counts look right.

> **Not done yet:** the step 07 page still shows the 7 October check made with the earlier model.
> Once the live scores have a couple of weeks of days (early November), ask Claude to update
> `build_nb07_data.py` and the step 07 page to show the new scores from `nrt_evaluation/`.

**Only if you re-ran notebooks 01–06** (for example after a dataset version change):

| You re-ran | Then run |
|---|---|
| 01 Data Acquisition | `build_nb01_data.py` |
| 02 Collate and Prepare | `build_nb02_data.py`, `build_nb03_data.py` |
| 04 Forecast Preparation | `build_nb04_data.py` |
| 05 Baselines and Modelling (new model) | `build_nb05_data.py`, `build_nb06_data.py` |

The scripts check themselves: `build_nb05_data.py` and `build_nb06_data.py` stop with an error
if their re-run of the model does not reproduce the scores saved in the model file, and
`build_nb04_data.py` stops if the inputs it reads do not match the observations. An error there
means the data and the model are out of step — re-run the notebooks in order (02 → 04 → 05).

**Text on the pages** is written in `website/src/pages/Step0X.vue`. Most numbers in the text are
filled in from the data, but some sentences describe the results in words (e.g. "the model wins
in 10 of 12 months"). After a new model or new live scores, re-read the affected pages, or ask
Claude to check them against the new data.

---

## Checking and publishing the website

```bash
cd website
npm install        # only the first time, or after package.json changes
npm run dev        # preview at http://localhost:5173 — stop with Ctrl+C
```

Look through the pages you expect to have changed (steps 07 and 08 after a live refresh).

When it looks right:

```bash
npm run deploy     # builds the site and publishes it to GitHub Pages
```

The live site is <https://algatt.github.io/mcast.pages.chl_prediction/>. It can take a minute
or two to update; hard-refresh the browser (Cmd+Shift+R) if you still see the old version.

> **First deploy only:** this replaces the old (v1) site that is online now. Its source stays in
> `archive/website_v1/`, but it will no longer be on the web unless it is published separately.

If `npm run build` fails, the error message names the file and line; nothing is published until
the build succeeds.

---

## The shared code

The rules used by every step live in one place, `experiment_v2/chlforecast/`: settings
(`config.py`), the input recipe (`features.py`), the simple rules (`baselines.py`), scoring,
the archive and forecasting. Notebooks 04, 07 and 08 and the scheduled job all import it.

- **After changing anything in `chlforecast/`**, run the check, which rebuilds step 04's inputs
  and step 05's test scores and fails if anything differs:
  ```bash
  cd experiment_v2 && .venv/bin/python scripts/check_shared_code.py
  ```
- **Restart the notebook kernel** after a change to `chlforecast/` — a running kernel keeps the
  old version in memory.
- **Rebuilding the Python environment** (new computer, or after a broken install), from
  `experiment_v2/`:
  ```bash
  uv venv --python 3.14 .venv
  uv pip install --python .venv/bin/python -r requirements.txt
  .venv/bin/copernicusmarine login
  ```
  If the environment is rebuilt, the scheduled job keeps working: it points at
  `experiment_v2/.venv/bin/python`.

---

## Every so often: back up and commit

**Back up the archive.** `experiment_v2/data/raw/nrt_archive/` exists only on this Mac and is
deliberately not in git. Copy the whole folder somewhere safe (cloud drive, external disk) every
week or two. It is small (a few MB a month).

**Commit your work** (notebooks, shared code, website data, website pages):

```bash
git add -A
git status         # check: no .nc files or data/raw/ should be listed
git commit -m "Refresh live forecast and archive"
git push
```

Large data files (`*.nc`, `data/raw/`) are ignored by `.gitignore`, so only the small results,
the code and the website are committed.

---

## Dates to remember

| Date | What |
|---|---|
| **25 October 2026** | Clocks go back. The 22:15 run still lands after 20:00 UTC, so no change is needed (it could move to 21:15). About this date, step 07 can first score a 7-day live forecast. |
| **Early November 2026** | Enough live issue days for step 07's 95% ranges; time to update the step 07 page (see above). |
| **24 November 2026** | The archive (multi-year) chlorophyll versions pinned in `01-Data Acquisition.ipynb` (L3 `202411`, L4 `202311`) are retired. Steps 01–06 need moving to the new versions, re-running in order, the check script, and the website data refreshing. |
| **12 January 2027** | The near-real-time gap-filled chlorophyll (`202207`) and temperature (`202311`) versions are retired. The archive picks up the new versions by itself and records the version in every file, but check the first days after the switch in step 07: compare a few days' values before and after. |
| **After the winter** | Enough live data to score the forecast in the season that matters most — worth a proper write-up on steps 07–08. |

## If something goes wrong

- **The log says `Archive run FAILED` with an authentication error** — in the terminal run
  `experiment_v2/.venv/bin/copernicusmarine login`, then run the job once by hand
  (`launchctl kickstart gui/$(id -u)/com.alangatt.chl-archive`).
- **The holdings table shows "Missing days"** — the archive did not run for more than a week and
  those days fell out of the live feed. They cannot be recovered; the archive keeps working, but
  checks spanning those days will have a gap.
- **"No module named …" in a notebook** — wrong kernel; select the `experiment_v2/.venv` one.
- **`ImportError` for something in `chlforecast`** — a file in `experiment_v2/chlforecast/` is
  missing or out of date, or the kernel was not restarted after a change.
- **The Mac becomes very slow** — several notebook kernels are probably still open and holding
  memory. Shut down kernels you are not using (Activity Monitor → Memory shows "Swap Used").
