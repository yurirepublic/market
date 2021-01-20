<template>
  <div
    class="p-2 d-flex flex-column"
    style="background-color: #fafafa; min-width: 17rem"
  >
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">BNB资产</span>

      <div class="flex">
        <RefreshButton :anime="refresh_button_anime" @click="refresh" />
        <ClickableIcon
          class=""
          icon="arrow-left-right"
          @click="show_transfer = show_transfer ? false : true"
        />
      </div>
    </div>

    <InfoItem header="现货账户" :content="bnb_free" footer="BNB" />
    <span class="text-muted small align-self-end">{{ bnb_usdt }}</span>

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

    <InfoItem header="期货账户" :content="bnb_further_free" footer="BNB" />
    <span class="text-muted small align-self-end">{{ bnb_further_usdt }}</span>
  </div>
</template>

<script>
import InfoItem from "@/components/InfoItem.vue";
import RefreshButton from "@/components/RefreshButton.vue";
import TransferInput from "@/components/TransferInput.vue";
import ClickableIcon from "@/components/ClickableIcon.vue";

export default {
  name: "BNBWallet",
  data: function () {
    return {
      bnb_free: "",
      bnb_further_free: "",

      bnb_usdt: "",
      bnb_further_usdt: "",

      show_transfer: false,

      refresh_button_anime: false,
      disabled_transfer_button: false,

      to_main_value: "",
      to_future_value: "",
    };
  },
  mounted: function () {
    this.refresh();
  },
  methods: {
    // 转账操作
    transfer_to_main(event) {
      this.disabled_transfer_button = true;
      this.showToast().info("开始转账");
      this.method_request("transfer", [
        "UMFUTURE_MAIN",
        "BNB",
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
      this.showToast().info("开始转账");
      this.method_request("transfer", [
        "MAIN_UMFUTURE",
        "BNB",
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

    // 刷新余额操作
    refresh() {
      this.refresh_button_anime = true;

      this.method_request("bnb_asset", [])
        .then((res) => {
          this.bnb_free = res["data"]["asset"];
          this.bnb_further_free = res["data"]["asset_further"];

          this.bnb_usdt = "≈ " + res["data"]["asset_usdt"] + " USDT";
          this.bnb_further_usdt =
            "≈ " + res["data"]["asset_further_usdt"] + " USDT";
          this.showToast().success("成功获取BNB资产");
        })
        .catch((error) => {
          this.showToast().error("BNB资产获取失败");
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