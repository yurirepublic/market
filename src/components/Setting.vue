<template>
  <div class="p-1">
    <CardFrame style="min-width: 30rem">
      <div class="mb-2">
        <span class="font-weight-bold">网络连接设置</span>
      </div>
      <div>
        <TradeInput
            header="服务器地址"
            placeholder=""
            v-model="serverUrl"
        ></TradeInput>
        <TradeInput
            class="mt-1"
            header="服务器口令"
            placeholder=""
            v-model="password"
        ></TradeInput>
        <TradeInput
            class="mt-1"
            header="数据中心接口"
            placeholder=""
            v-model="dataUrl"
        ></TradeInput>
        <TradeInput
            class="mt-1"
            header="数据订阅接口"
            placeholder=""
            v-model="subscribeUrl"
        ></TradeInput>
        <button
            class="btn btn-primary mt-3 px-2"
            @click="Save"
            style="background-color: #02c076; border-color: transparent"
        >
          保存
        </button>
      </div>
    </CardFrame>
  </div>
</template>

<script>
import CardFrame from "@/components/CardFrame.vue"
import TradeInput from "@/components/TradeInput.vue"

export default {
  name: "Setting",
  data: function () {
    return {
      serverUrl: '',
      password: '',
      dataUrl: '',
      subscribeUrl: ''
    };
  },
  mounted: async function () {
    this.serverUrl = localStorage.serverUrl
    this.password = localStorage.password
    this.dataUrl = localStorage.dataUrl
    this.subscribeUrl = localStorage.subscribUrl
  },
  methods: {
    Save: function () {
      try {
        localStorage.serverUrl = this.serverUrl
        localStorage.password = this.password
        localStorage.dataUrl = this.dataUrl
        localStorage.subscribUrl = this.subscribeUrl
        this.showToast().success('成功保存设置')
      } catch (e) {
        this.showToast().error('保存设置失败')
      }
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