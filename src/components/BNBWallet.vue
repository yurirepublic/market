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
            @click="show_transfer = !show_transfer"
        />
        <RefreshButton :anime="refresh_button_anime" @click="RefreshWallet"/>
      </div>
    </div>

    <InfoItem header="现货账户" :content="main_bnb" footer="BNB"/>
    <span class="text-muted small align-self-end">≈ {{ Math.floor(main_bnb * bnb_price * 100) / 100 }} USDT</span>

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

    <InfoItem header="期货账户" :content="future_bnb" footer="BNB"/>
    <span class="text-muted small align-self-end">≈ {{ Math.floor(future_bnb * bnb_price * 100) / 100 }} USDT</span>

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


    <InfoItem header="全仓账户" :content="margin_bnb" footer="BNB"/>
    <span class="text-muted small align-self-end">≈ {{ Math.floor(margin_bnb * bnb_price * 100) / 100 }} USDT</span>

    <div class="d-flex">
      <no-border-button @click="BNBBurnClick('spot')" :disabled="disabled_bnb_burn_button">
        <input class="align-middle" type="checkbox" :checked="spot_bnb_burn"/>
        <span class="text-muted small ml-1 align-middle">手续费BNB燃烧</span>
      </no-border-button>

      <no-border-button @click="BNBBurnClick('interest')" :disabled="disabled_bnb_burn_button">
        <input class="align-middle" type="checkbox" :checked="interest_bnb_burn"/>
        <span class="text-muted small ml-1 align-middle">利息BNB燃烧</span>
      </no-border-button>


    </div>

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
      main_bnb: "",
      future_bnb: "",
      margin_bnb: "",
      bnb_price: "",

      show_transfer: false,   // 显示转账输入框

      refresh_button_anime: false,
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
  mounted: function () {
    this.RefreshWallet()
    this.RefreshBNBBurn()
  },
  methods: {
    // 转账操作
    // 转账操作
    Transfer: function (mode, amount) {
      this.disabled_transfer_button = true;
      this.showToast().info("开始转账");
      this.method_request("transfer", [
        mode,
        "BNB",
        amount,
      ])
          .then((res) => {
            this.showToast().success("转账成功");
            // 转账成功了清空一下输入
            this.main_to_future_value = ""
            this.main_to_margin_value = ""
            this.future_to_main_value = ""
            this.margin_to_main_value = ""

            this.RefreshWallet();
          })
          .catch((err) => {
            this.showToast().error("转账失败");
            this.RefreshWallet();
          })
          .finally(() => {
            this.disabled_transfer_button = false;
          });
    },

    // 刷新余额操作
    RefreshWallet: function () {
      this.refresh_button_anime = true;

      this.method_request("bnb_asset", [])
          .then((res) => {
            this.main_bnb = res['data']['main_bnb']
            this.future_bnb = res['data']['future_bnb']
            this.margin_bnb = res['data']['margin_bnb']
            this.bnb_price = res['data']['bnb_price']
            //
            // this.bnb_usdt = "≈ " + res["data"]["asset_usdt"] + " USDT";
            // this.bnb_future_usdt =
            //     "≈ " + res["data"]["asset_future_usdt"] + " USDT";
            this.showToast().success("成功获取BNB资产");
          })
          .catch((error) => {
            this.showToast().error("BNB资产获取失败");
          })
          .finally(() => {
            this.refresh_button_anime = false;
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
            this.showToast().success("成功设置BNB燃烧状态")
          })
          .catch(err => {
            this.showToast().error('设置BNB燃烧状态失败')
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
            this.showToast().success("成功获取BNB燃烧状态")
          })
          .catch(err => {
            this.showToast().error('BNB燃烧状态获取失败')
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