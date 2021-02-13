import Vue from 'vue'

// 导入Bootstrap样式库
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import store from './store'

// 导入BootstrapVue (我觉得这玩意太垃圾了，考虑删掉)
import { BootstrapVue, IconsPlugin } from 'bootstrap-vue'

// 导入VueToast
// 可以自选主题
import VueToast from 'vue-toast-notification'
import 'vue-toast-notification/dist/theme-default.css';
//import 'vue-toast-notification/dist/theme-sugar.css';



Vue.config.productionTip = false

Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
Vue.use(VueToast)

import base from './base.js'

Vue.use(base)

import OhVueIcon from 'oh-vue-icons/components/Icon'

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