<template>
  <div class="p-1">
    <CardFrame style="min-width: 17rem">
      <div class="mb-2">
        <span class="font-weight-bold">网络连接设置</span>
      </div>
      <div>
        <TradeInput
          header="服务器地址"
          placeholder=""
          v-model="server_url"
        ></TradeInput>
        <TradeInput
          class="mt-1"
          header="服务器口令"
          placeholder="在服务端设置的字符串"
          v-model="password"
        ></TradeInput>
        <TradeInput
          class="mt-1"
          header="HTTP代理地址"
          placeholder="通过代理连接到自己的服务器"
          v-model="proxy_url"
        ></TradeInput>
        <button
          class="btn btn-primary mt-3 px-2"
          @click="saveConfig"
          style="background-color: #02c076; border-color: transparent"
        >
          保存
        </button>
      </div>
    </CardFrame>
  </div>
</template>

<script>
import CardFrame from "@/components/CardFrame.vue";
import TradeInput from "@/components/TradeInput.vue";
import { ipcRenderer } from "electron";
import Vue from "vue";

ipcRenderer.on("save-config-reply", (event, args) => {
  if (args == "success") {
    Vue.$toast.open({
      type: "success",
      message: "保存成功",
    });
  }
  if (args == "fail") {
    Vue.$toast.open({
      type: "error",
      message: "保存失败",
    });
  }
});

export default {
  name: "Setting",
  data: function () {
    return {
      server_url: "",
      password: "",
      proxy_url: "",
    };
  },
  mounted: function () {
    ipcRenderer.on("read-config-reply", (event, arg) => {
      this.server_url = arg["server_url"];
      this.password = arg["password"];
      this.proxy_url = arg["proxy_url"];
    });
    ipcRenderer.send("read-config");
  },
  methods: {
    saveConfig: function () {
      ipcRenderer.send("save-config", {
        server_url: this.server_url,
        password: this.password,
        proxy_url: this.proxy_url,
      });
    },
  },
  components: {
    CardFrame,
    TradeInput,
  },
};
</script>

<style scoped>
</style>