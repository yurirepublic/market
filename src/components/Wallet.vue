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
            name="ri-arrow-left-right-line"
            @click="show_transfer = show_transfer ? false : true"
        />
        <RefreshButton :anime="refresh_button_anime" @click="refresh"/>
      </div>
    </div>

    <InfoItem header="可用现货" :content="main_free" footer="USDT"/>
    <div class="d-flex" v-if="show_transfer">
      <TransferInput
          class="mr-1"
          placeholder="转到现货"
          :disabled="disabled_transfer_button"
          v-model="future_to_main_value"
          @click="Transfer('UMFUTURE_MAIN', future_to_main_value)"
      >
        <b-icon icon="box-arrow-up"></b-icon>
      </TransferInput>
      <TransferInput
          class="ml-1"
          placeholder="转到期货"
          :disabled="disabled_transfer_button"
          v-model="main_to_future_value"
          @click="Transfer('MAIN_UMFUTURE', main_to_future_value)"
      >
        <b-icon icon="box-arrow-down"></b-icon>
      </TransferInput>
    </div>
    <InfoItem header="可用期货" :content="future_free" footer="USDT"/>
    <div class="d-flex" v-if="show_transfer">
      <TransferInput
          class="mr-1"
          placeholder="转到现货"
          :disabled="disabled_transfer_button"
          v-model="margin_to_main_value"
          @click="Transfer('MARGIN_MAIN', margin_to_main_value)"
      >
        <b-icon icon="box-arrow-up"></b-icon>
      </TransferInput>
      <TransferInput
          class="ml-1"
          placeholder="转到全仓"
          :disabled="disabled_transfer_button"
          v-model="main_to_margin_value"
          @click="Transfer('MAIN_MARGIN', main_to_margin_value)"
      >
        <b-icon icon="box-arrow-down"></b-icon>
      </TransferInput>
    </div>
    <InfoItem header="可用全仓" :content="margin_free" footer="USDT"/>
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
      main_free: "",
      future_free: "",
      margin_free: '',
      refresh_button_anime: false,

      disabled_transfer_button: false,

      future_to_main_value: "",
      main_to_future_value: "",

      margin_to_main_value: '',
      main_to_margin_value: '',

      show_transfer: false,
    };
  },
  mounted: function () {
    this.refresh();
  },
  methods: {
    // 转账操作
    Transfer: function (mode, amount) {
      this.disabled_transfer_button = true;
      this.showToast().info("开始转账");
      this.method_request("transfer", [
        mode,
        "USDT",
        amount,
      ])
          .then((res) => {
            this.showToast().success("转账成功");
            // 转账成功了清空一下输入
            this.main_to_future_value = ""
            this.main_to_margin_value = ""
            this.future_to_main_value = ""
            this.margin_to_main_value = ""

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
            this.main_free = res["data"]["main_free"];
            this.future_free = res["data"]["future_free"];
            this.margin_free = res['data']['margin_free'];

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