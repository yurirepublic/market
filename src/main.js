import Vue from 'vue'

// 导入Bootstrap样式库
import 'bootstrap/dist/css/bootstrap.css'

// 导入一点官方组件
import App from './App.vue'
import router from './router'
import store from './store'

// 导入VueToast
// 可以自选主题
import VueToast from 'vue-toast-notification'
import 'vue-toast-notification/dist/theme-default.css';
//import 'vue-toast-notification/dist/theme-sugar.css';

Vue.config.productionTip = false

Vue.use(VueToast)

// 导入自制基本组件
import base from './base.js'
Vue.use(base)

// 导入oh-vue-icons
import OhVueIcon from 'oh-vue-icons'

import { RiCloseLine } from 'oh-vue-icons/icons'
import { FaRegularWindowMaximize } from 'oh-vue-icons/icons'
import { FaRegularWindowMinimize } from 'oh-vue-icons/icons'
import { RiArrowLeftRightLine } from 'oh-vue-icons/icons'
import { FaRegularWindowRestore } from 'oh-vue-icons/icons'
import { RiCoinsLine } from 'oh-vue-icons/icons'
import { RiSettings4Line } from 'oh-vue-icons/icons'
import { BiFileEarmarkCode } from 'oh-vue-icons/icons'
import { BiFileEarmarkPlay } from 'oh-vue-icons/icons'
import { RiHistoryLine } from 'oh-vue-icons/icons'
OhVueIcon.add([
  RiCloseLine,
  FaRegularWindowMinimize,
  FaRegularWindowMaximize,
  RiArrowLeftRightLine,
  FaRegularWindowRestore,
  RiCoinsLine,
  RiSettings4Line,
  BiFileEarmarkCode,
  BiFileEarmarkPlay,
  RiHistoryLine,
])

Vue.component('v-icon', OhVueIcon)


new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
