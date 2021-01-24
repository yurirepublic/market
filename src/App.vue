<template>
  <div class="d-flex flex-column" style="height: 100%">
    <TitleBar style="-webkit-app-region: drag" />
    <div class="d-flex" style="height: 100%">
      <FuncSwitchBar />
      <premium />
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
// 单独改变背景颜色
// document.body.style.backgroundColor = "#f5f5f5";
// document.body.style.height = "100%";

import premium from "@/components/premium.vue";
import TitleBar from "@/components/TitleBar.vue";
import FuncSwitchBar from "@/components/FuncSwitchBar.vue";

export default {
  components: {
    premium,
    TitleBar,
    FuncSwitchBar,
  },
};
</script>


<style>
html,
body {
  height: 100%;
  background-color: #f5f5f5;
}

/* 
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

#nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: #2c3e50;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
} */
</style>