<template>
  <div
    class="p-2 d-flex flex-column"
    style="background-color: #fafafa; min-width: 17rem"
  >
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">USDT资产</span>
      <div class="d-flex">
        <ClickableIcon
          class=""
          icon="arrow-left-right"
          @click="show_transfer = show_transfer ? false : true"
        />
        <RefreshButton :anime="refresh_button_anime" @click="refresh" />
      </div>
    </div>

    <InfoItem header="可用现货" :content="usdt_free" footer="USDT" />
    <div class="d-flex" v-if="show_transfer">
      <TransferInput
        class="mr-1"
        placeholder="转到现货"
        :disabled="disabled_transfer_button"
        v-model="to_main_value"
        @click="transfer_to_main"
      >
        <b-icon icon="box-arrow-up"></b-icon>
      </TransferInput>
      <TransferInput
        class="ml-1"
        placeholder="转到期货"
        :disabled="disabled_transfer_button"
        v-model="to_future_value"
        @click="transfer_to_future"
      >
        <b-icon icon="box-arrow-down"></b-icon>
      </TransferInput>
    </div>
    <InfoItem header="可用期货" :content="usdt_future_free" footer="USDT" />
  </div>
</template>

<script>
import InfoItem from "@/components/InfoItem.vue";
import RefreshButton from "@/components/RefreshButton.vue";
import TransferInput from "@/components/TransferInput.vue";
import ClickableIcon from "@/components/ClickableIcon.vue";

export default {
  name: "Wallet",
  data: function () {
    return {
      usdt_free: "",
      usdt_future_free: "",
      refresh_button_anime: false,

      disabled_transfer_button: false,

      to_main_value: "",
      to_future_value: "",

      show_transfer: false,
    };
  },
  mounted: function () {
    this.refresh();
  },
  methods: {
    // 转账操作
    transfer_to_main(event) {
      this.disabled_transfer_button = true;
      this.showToast().info('开始转账')
      this.method_request("transfer", [
        "UMFUTURE_MAIN",
        "USDT",
        this.to_main_value,
      ])
        .then((res) => {
          this.showToast().success("转账成功");
          this.to_main_value = "";
          this.refresh();
        })
        .catch((err) => {
          this.showToast().error("转账失败");
          this.refresh();
        })
        .finally(() => {
          this.disabled_transfer_button = false;
        });
    },

    transfer_to_future(event) {
      this.disabled_transfer_button = true;
      this.showToast().info('开始转账')
      this.method_request("transfer", [
        "MAIN_UMFUTURE",
        "USDT",
        this.to_future_value,
      ])
        .then((res) => {
          this.showToast().success("转账成功");
          this.to_future_value = "";
          this.refresh();
        })
        .catch((err) => {
          this.showToast().error("转账失败");
          this.refresh();
        })
        .finally(() => {
          this.disabled_transfer_button = false;
        });
    },
    refresh() {
      this.refresh_button_anime = true;

      this.method_request("wallet_money", [])
        .then((res) => {
          this.usdt_free = res["data"]["usdt_free"];
          this.usdt_future_free = res["data"]["usdt_future_free"];

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
    TransferInput,
    ClickableIcon,
  },
};
</script>

<style scoped>
</style>