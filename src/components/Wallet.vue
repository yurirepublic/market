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
            @click="showTransfer = !showTransfer"
        />
      </div>
    </div>

    <InfoItem header="可用现货" :content="mainFree" footer="USDT"/>
    <div class="d-flex" v-if="showTransfer">
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
    <InfoItem header="可用期货" :content="futureFree" footer="USDT"/>
    <div class="d-flex" v-if="showTransfer">
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
    <InfoItem header="可用全仓" :content="marginFree" footer="USDT"/>
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
      mainFree: NaN,
      futureFree: NaN,
      marginFree: NaN,

      disabled_transfer_button: false,

      transferAmount: "",

      future_to_main_value: "",
      main_to_future_value: "",

      margin_to_main_value: '',
      main_to_margin_value: '',

      showTransfer: false,

      ws: null,
      subWs: null
    };
  },
  mounted: async function () {
    this.ws = await this.connectDataCenter()
    this.subWs = await this.connectSubscribe()
    // 订阅资产变动
    await this.subWs.precise(['asset', 'main', 'USDT'], msg => {
      this.mainFree = msg['data']
    })
    await this.subWs.precise(['asset', 'future', 'USDT'], msg => {
      this.futureFree = msg['data']
    })
    await this.subWs.precise(['asset', 'margin', 'USDT'], msg => {
      this.marginFree = msg['data']
    })
    this.mainFree = await this.ws.getData(['asset', 'main', 'USDT'])
    this.futureFree = await this.ws.getData(['asset', 'future', 'USDT'])
    this.marginFree = await this.ws.getData(['asset', 'margin', 'USDT'])
  },
  methods: {
    // 转账操作
    Transfer: function (mode, amount) {
      this.disabled_transfer_button = true;
      this.showToast.info("开始转账");
      this.method_request("transfer", [
        mode,
        "USDT",
        amount,
      ])
          .then((res) => {
            this.showToast.success("转账成功");
            // 转账成功了清空一下输入
            this.main_to_future_value = ""
            this.main_to_margin_value = ""
            this.future_to_main_value = ""
            this.margin_to_main_value = ""
          })
          .catch((err) => {
            this.showToast.error("转账失败");
            this.refresh();
          })
          .finally(() => {
            this.disabled_transfer_button = false;
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