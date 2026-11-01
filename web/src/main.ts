import { createApp } from 'vue'
import VChart from 'vue-echarts'
import App from './App.vue'
import './style.css'

createApp(App).component('VChart', VChart).mount('#app')
