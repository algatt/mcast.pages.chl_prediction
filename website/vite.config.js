import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// './' keeps asset paths relative, so the build works under the GitHub Pages
// project path; vue-router's hash history (src/router.js) handles the routes.
export default defineConfig({
  base: './',
  plugins: [vue()],
  server: { port: 5173, open: false },
})
