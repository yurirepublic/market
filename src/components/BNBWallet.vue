<template>
  <div
      class="p-2 d-flex flex-column"
      style="background-color: #fafafa; min-width: 17rem"
  >
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">BNB资产</span>

      <div class="d-flex">
        <ClickableIcon
            class=""
            name="ri-arrow-left-right-line"
            @click="showTransfer = !showTransfer"
        />
      </div>
    </div>

    <InfoItem header="现货账户" :content="mainBNB" footer="BNB"/>
    <span class="text-muted small align-self-end">≈ {{ Math.floor(mainBNB * BNBPrice * 100) / 100 }} USDT</span>

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

    <InfoItem header="期货账户" :content="futureBNB" footer="BNB"/>
    <span class="text-muted small align-self-end">≈ {{ Math.floor(futureBNB * BNBPrice * 100) / 100 }} USDT</span>

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

    <InfoItem header="全仓账户" :content="marginBNB" footer="BNB"/>
    <span class="text-muted small align-self-end">≈ {{ Math.floor(marginBNB * BNBPrice * 100) / 100 }} USDT</span>

  </div>
</template>

<script>
import InfoItem from "@/components/InfoItem.vue";
import RefreshButton from "@/components/RefreshButton.vue";
import TransferInput from "@/components/TransferInput.vue";
import ClickableIcon from "@/components/ClickableIcon.vue";
import NoBorderButton from "@/components/NoBorderButton";

export default {
  name: "BNBWallet",
  data: function () {
    return {
      mainBNB: "",
      futureBNB: "",
      marginBNB: "",
      BNBPrice: "",

      showTransfer: false,   // 显示转账输入框

      disabled_transfer_button: false,

      main_to_future_value: "",        // 现货转期货数目
      main_to_margin_value: "",
      future_to_main_value: "",        // 期货转现货数目
      margin_to_main_value: "",

      spot_bnb_burn: false,
      interest_bnb_burn: false,
      disabled_bnb_burn_button: false,
    };
  },
  mounted: async function () {
    this.ws = await this.connectDataCenter()
    this.subWs = await this.connectSubscribe()

    this.BNBPrice = await this.ws.getData(['price', 'main', 'BNBUSDT'])
    await this.subWs.precise(['asset', 'main', 'BNB'], msg => {
      this.mainBNB = msg['data']
    })
    await this.subWs.precise(['asset', 'future', 'BNB'], msg => {
      this.futureBNB = msg['data']
    })
    await this.subWs.precise(['asset', 'marin', 'BNB'], msg => {
      this.marginBNB = msg['data']
    })
    this.mainBNB = await this.ws.getData(['asset', 'main', 'BNB'])
    this.futureBNB = await this.ws.getData(['asset', 'future', 'BNB'])
    this.marginBNB = await this.ws.getData(['asset', 'margin', 'BNB'])
  },
  methods: {
    // 转账操作
    Transfer: function (mode, amount) {
      this.disabled_transfer_button = true;
      this.showToast.info("开始转账");
      this.method_request("transfer", [
        mode,
        "BNB",
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
          })
          .finally(() => {
            this.disabled_transfer_button = false;
          });
    },

    BNBBurnClick: function (event) {
      this.disabled_bnb_burn_button = true
      let promise = null
      if (event === 'spot') {
        promise = this.method_request('set_bnb_burn', [!this.spot_bnb_burn, this.interest_bnb_burn])
      } else {
        promise = this.method_request('set_bnb_burn', [this.spot_bnb_burn, !this.interest_bnb_burn])
      }
      promise
          .then(res => {
            this.spot_bnb_burn = res['data']['spotBNBBurn']
            this.interest_bnb_burn = res['data']['interestBNBBurn']
            this.showToast.success("成功设置BNB燃烧状态")
          })
          .catch(err => {
            this.showToast.error('设置BNB燃烧状态失败')
          })
          .finally(() => {
            this.disabled_bnb_burn_button = false
          })
    },

    // 刷新BNB燃烧情况
    RefreshBNBBurn: function () {
      this.disabled_bnb_burn_button = true
      this.method_request('get_bnb_burn', [])
          .then(res => {
            this.spot_bnb_burn = res['data']['spotBNBBurn']
            this.interest_bnb_burn = res['data']['interestBNBBurn']
            this.showToast.success("成功获取BNB燃烧状态")
          })
          .catch(err => {
            this.showToast.error('BNB燃烧状态获取失败')
          })
          .finally(() => {
            this.disabled_bnb_burn_button = false
          })
    }
  },
  components: {
    InfoItem,
    RefreshButton,
    TransferInput,
    ClickableIcon,
    NoBorderButton
  },
};
</script>

<style scoped>
</style>