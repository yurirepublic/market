<template>
  <div class='d-flex flex-column' style='height: 100%'>
    <div class='d-flex' style='height: 100%'>
      <the-page-switch-bar :pages='pages' :focus-page='focusPage' @click='focusPage = $event' />
      <div v-show="focusPage === 'market'">
        <market />
      </div>
      <div v-show="focusPage === 'statistics'">
        <statistics />
      </div>
      <div v-show="focusPage === 'science'">
        <science />
      </div>
      <div v-show="focusPage === 'setting'">
        <setting />
      </div>
      <div v-show="focusPage === 'runningScript'">
        <running-script />
      </div>
      <div v-show="focusPage === 'scriptManage'">
        <script-manage />
      </div>
    </div>
  </div>
  <!-- <div id="app">
    <div id="nav">
      <router-link to="/">Home</router-link> |
      <router-link to="/about">About</router-link>
    </div>
    <router-view/>
  </div> -->
</template>

<script>

import Market from '@/views/Market.vue'
import ThePageSwitchBar from '@/views/ThePageSwitchBar.vue'
import Setting from '@/views/Setting.vue'
import RunningScript from '@/views/RunningScript.vue'
import ScriptManage from '@/views/ScriptManage.vue'
import Statistics from '@/views/Statistics'
import Science from '@/views/Science'

export default {
  components: {
    Market,
    ThePageSwitchBar,
    Setting,
    RunningScript,
    ScriptManage,
    Statistics,
    Science
  },
  data: function() {
    return {
      focusPage: 'market',
      pages: [
        {
          name: 'market',
          icon: 'ri-coins-line'
        },
        {
          name: 'statistics',
          icon: 'fa-regular-chart-bar'
        },
        {
          name: 'science',
          icon: 'fa-flask'
        },
        {
          name: 'runningScript',
          icon: 'fa-regular-play-circle'
        },
        {
          name: 'scriptManage',
          icon: 'fa-regular-list-alt'
        },
        {
          name: 'setting',
          icon: 'ri-settings-4-line'
        }

      ]
    }
  },
  methods: {}

}
</script>


<style>
html,
body {
  height: 100%;
  background-color: #f5f5f5;
}
</style>
