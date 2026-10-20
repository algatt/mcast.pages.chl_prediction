// One entry per step of the experiment; each step is one Jupyter notebook in
// experiment_v2/. A page exists only where `ready` is true; the rest are listed
// so readers can see where the story goes.
export const steps = [
  {
    number: '01',
    slug: '01-data-acquisition',
    notebook: '01-Data Acquisition.ipynb',
    title: 'Data acquisition',
    question: 'Which satellite data do we need, and which version of it?',
    ready: true,
  },
  {
    number: '02',
    slug: '02-collate-and-prepare',
    notebook: '02-Collate-and-Prepare.ipynb',
    title: 'Collate and prepare',
    question: 'How do datasets on different grids become one table?',
    ready: true,
  },
  {
    number: '03',
    slug: '03-data-exploration',
    notebook: '03-Data-Exploration.ipynb',
    title: 'Data exploration',
    question: 'How often is the sea actually visible, and what does chlorophyll do over a year?',
    ready: true,
  },
  {
    number: '04',
    slug: '04-forecast-preparation',
    notebook: '04-Forecast-Preparation.ipynb',
    title: 'Forecast preparation',
    question: 'What would a forecaster really know at 20:30 UTC?',
    ready: true,
  },
  {
    number: '05',
    slug: '05-baselines-and-modelling',
    notebook: '05-Baselines-and-Modelling.ipynb',
    title: 'Baselines and modelling',
    question: 'Does a machine-learning model beat simple rules — and by how much?',
    ready: true,
  },
  {
    number: '06',
    slug: '06-forecast-maps',
    notebook: '06-Forecast-Maps.ipynb',
    title: 'Forecast maps',
    question: 'Where and when are the forecasts wrong?',
    ready: true,
  },
  {
    number: '07',
    slug: '07-nrt-input-validation',
    notebook: '07-NRT-Input-Validation.ipynb',
    title: 'Live data validation',
    question: 'Does the model still work on the data a real forecast would receive?',
    ready: true,
  },
  {
    number: '08',
    slug: '08-nrt-archive',
    notebook: '08-NRT-Archive.ipynb',
    title: 'Live data archive',
    question: 'How do we keep the evidence a live forecast needs?',
    ready: true,
  },
]

export const stepPath = (step) => `/steps/${step.slug}`
