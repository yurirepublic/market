import Vue from 'vue'
import App from './App.vue'
import './registerServiceWorker'
import router from './router'
import store from './store'

Vue.config.productionTip = false

// 导入Bootstrap样式库
import 'bootstrap/dist/css/bootstrap.css'

// 导入Bootstrap-vue
import {BootstrapVue, IconsPlugin} from 'bootstrap-vue'

Vue.use(BootstrapVue)
Vue.use(IconsPlugin)

// 导入VueToast
import VueToast from 'vue-toast-notification'
import 'vue-toast-notification/dist/theme-default.css'   // 两个主题可选
//import 'vue-toast-notification/dist/theme-sugar.css'
Vue.use(VueToast)

// 导入自制基本组件
import base from './base.js'

Vue.use(base)

// 导入oh-vue-icons
import OhVueIcon from 'oh-vue-icons'

import {FaRegularWindowMaximize, RiCloseLine} from 'oh-vue-icons/icons'
import {FaRegularWindowMinimize} from 'oh-vue-icons/icons'
import {RiArrowLeftRightLine} from 'oh-vue-icons/icons'
import {FaRegularWindowRestore} from 'oh-vue-icons/icons'
import {RiCoinsLine} from 'oh-vue-icons/icons'
import {RiSettings4Line} from 'oh-vue-icons/icons'
import {BiFileEarmarkCode} from 'oh-vue-icons/icons'
import {BiFileEarmarkPlay} from 'oh-vue-icons/icons'
import {RiHistoryLine} from 'oh-vue-icons/icons'
import {RiCloseCircleLine} from 'oh-vue-icons/icons'
import {RiCheckboxCircleLine} from 'oh-vue-icons/icons'
import {BiArrowRight} from 'oh-vue-icons/icons'

OhVueIcon.add(
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
  RiCloseCircleLine,
  RiCheckboxCircleLine,
  BiArrowRight
)
Vue.component('v-icon', OhVueIcon)


new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app')
