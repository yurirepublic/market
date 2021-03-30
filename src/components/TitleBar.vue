<template>
  <div class="title-bar d-flex justify-content-end align-items-center">
    <div class="d-flex" style="-webkit-app-region: no-drag">
      <ClickableBox @click="set_minimize">
        <v-icon name="fa-regular-window-minimize" scale="0.8"></v-icon>
      </ClickableBox>
      <ClickableBox @click="set_maximize" v-if="!is_maxmize">
        <v-icon name="fa-regular-window-maximize" scale="0.8"></v-icon>
      </ClickableBox>
      <ClickableBox @click="set_restore" v-if="is_maxmize">
        <v-icon name="fa-regular-window-restore" scale="0.8"></v-icon>
      </ClickableBox>
      <ClickableBox @click="close_window">
        <v-icon name="ri-close-line"></v-icon>
      </ClickableBox>
    </div>
  </div>
</template>

<script>
import ClickableBox from "@/components/ClickableBox.vue";
import { ipcRenderer } from "electron";

export default {
  name: "TitleBar",
  props: {
    title: "",
    minimize: true,
    maxmize: true,
    exit: true,
  },
  data: function () {
    return {
      is_maxmize: false,
    };
  },
  components: {
    ClickableBox,
  },
  methods: {
    set_minimize() {
      ipcRenderer.send("window-minimize");
    },
    set_maximize() {
      this.is_maxmize = true;
      ipcRenderer.send("window-maximize");
    },
    set_restore() {
      this.is_maxmize = false;
      ipcRenderer.send("window-restore");
    },
    close_window() {
      ipcRenderer.send("window-close");
    },
  },
};
</script>

<style scoped>
.title-bar {
  height: 2rem;
  background-color: #cecece;
}
</style>