<template>
  <div
    class="p-2 d-flex flex-column"
    style="background-color: #fafafa; min-width: 17rem"
  >
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">USDT资产</span>
      <RefreshButton :anime="refresh_button_anime" @click="refresh" />
    </div>

    <InfoItem header="可用现货" :content="usdt_free" footer="USDT" />
    <InfoItem header="可用期货" :content="usdt_further_free" footer="USDT" />

    <!-- <div class="d-flex justify-content-between">
      <span>资金充足率</span>
      <span class="ml-2 text-primary text-monospace"
        >{{ free_further_usdt }}%</span
      >
    </div> -->
    <!-- <div class="">
      <button
        class="btn btn-secondary btn-sm float-right"
        type="button"
        @click="refresh"
        @click.stop
      >
        刷新
      </button>
    </div> -->
  </div>
</template>

<script>
import InfoItem from "@/components/InfoItem.vue";
import RefreshButton from "@/components/RefreshButton.vue";

export default {
  name: "Wallet",
  data: function () {
    return {
      usdt_free: "",
      usdt_further_free: "",
      refresh_button_anime: false,
    };
  },
  mounted: function () {
    this.refresh();
  },
  methods: {
    refresh() {
      this.refresh_button_anime = true;

      this.method_request("wallet_money", [])
        .then((res) => {
          this.usdt_free = res["data"]["usdt_free"];
          this.usdt_further_free = res["data"]["usdt_further_free"];

          this.$toast.open({
            message: "成功获取钱包金额",
            type: "success",
          });
        })
        .catch((error) => {
          this.$toast.open({
            message: "钱包金额获取失败",
            type: "error",
          });
        })
        .finally(() => {
          this.refresh_button_anime = false;
        });
    },
  },
  components: {
    InfoItem,
    RefreshButton,
  },
};
</script>

<style scoped>
  
</style>