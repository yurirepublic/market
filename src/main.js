import Vue from 'vue'
import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import store from './store'

Vue.config.productionTip = false

// 导入Bootstrap样式库
import 'bootstrap/dist/css/bootstrap.css'

// 导入VueToast
import VueToast from 'vue-toast-notification'
import 'vue-toast-notification/dist/theme-default.css'   // 两个主题可选
//import 'vue-toast-notification/dist/theme-sugar.css'
Vue.use(VueToast)

// 导入自制基本组件
import base from './base.js'

Vue.use(base)

// 导入ve-charts
import VeCharts from 've-charts'

Vue.use(VeCharts)

// 导入oh-vue-icons
import OhVueIcon from 'oh-vue-icons'

import { RiArrowLeftRightLine } from 'oh-vue-icons/icons'
import { RiCoinsLine } from 'oh-vue-icons/icons'
import { RiSettings4Line } from 'oh-vue-icons/icons'
import { RiHistoryLine } from 'oh-vue-icons/icons'
import { RiCloseCircleLine } from 'oh-vue-icons/icons'
import { RiCheckboxCircleLine } from 'oh-vue-icons/icons'
import { BiArrowRight } from 'oh-vue-icons/icons'
import { RiLoader4Line } from 'oh-vue-icons/icons'
import { RiErrorWarningLine } from 'oh-vue-icons/icons'
import { FaRegularChartBar } from 'oh-vue-icons/icons'
import { FaRegularPlayCircle } from 'oh-vue-icons/icons'
import { FaRegularListAlt } from 'oh-vue-icons/icons'
import { RiRefreshLine } from 'oh-vue-icons/icons'
import { FaFlask } from 'oh-vue-icons/icons'
import { FaGlobeAmericas } from 'oh-vue-icons/icons'

OhVueIcon.add(
  RiArrowLeftRightLine,
  RiCoinsLine,
  RiSettings4Line,
  RiHistoryLine,
  RiCloseCircleLine,
  RiCheckboxCircleLine,
  BiArrowRight,
  RiLoader4Line,
  RiErrorWarningLine,
  FaRegularChartBar,
  FaRegularPlayCircle,
  FaRegularListAlt,
  RiRefreshLine,
  FaFlask,
  FaGlobeAmericas
)
Vue.component('v-icon', OhVueIcon)


new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
