import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js'
import './style.css'

// Register Chart.js components once, globally, so any chart component can import
// { Line, Bar, Scatter } from 'vue-chartjs' and just use them.
import {
  Chart as ChartJS,
  Title, Tooltip, Legend, Filler,
  LineElement, PointElement, BarElement,
  CategoryScale, LinearScale,
} from 'chart.js'

ChartJS.register(
  Title, Tooltip, Legend, Filler,
  LineElement, PointElement, BarElement,
  CategoryScale, LinearScale,
)

createApp(App).use(router).mount('#app')
