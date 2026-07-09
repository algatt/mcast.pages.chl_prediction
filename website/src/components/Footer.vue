<script setup>
  // TODO: fill in your repo URL when the project is pushed to GitHub.
  const REPO_URL = "https://algatt.github.io/mcast.pages.chl_prediction";
  const links = [
    { label: "PLAN.md", href: "../experiment/PLAN.md" },
    { label: "EXPLANATION.md", href: "../experiment/EXPLANATION.md" },
    { label: "GitHub", href: REPO_URL },
  ];
</script>

<template>
  <footer class="border-t border-slate-200 bg-white mt-16">
    <div
      class="container-page py-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-slate-500"
    >
      <p>
        <span class="font-medium text-slate-700">Chl-a Forecasting</span> ·
        Malta–Sicily Channel
        <span class="text-slate-400 mx-1">·</span>
        Methodology explained.
      </p>
      <div class="flex items-center gap-4">
        <a
          v-for="l in links"
          :key="l.label"
          :href="l.href"
          class="hover:text-ocean-700 transition-colors"
        >
          {{ l.label }}
        </a>
      </div>
    </div>
  </footer>
</template>
