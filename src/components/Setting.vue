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
            v-model="config['server_url']"
        ></TradeInput>
        <TradeInput
            class="mt-1"
            header="服务器口令"
            placeholder=""
            v-model="config['password']"
        ></TradeInput>
        <TradeInput
            class="mt-1"
            header="数据中心接口"
            placeholder=""
            v-model="config['data_center_url']"
        ></TradeInput>
        <TradeInput
            class="mt-1"
            header="数据订阅接口"
            placeholder=""
            v-model="config['data_center_subscribe_url']"
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
      config: {},
    };
  },
  mounted: async function () {
    this.config = await this.readConfig()
  },
  methods: {
    Save: async function () {
      try {
        await this.saveConfig(this.config)
        this.showToast().success('成功保存设置，重启生效')
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