<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="">
      <div class="mb-2">
        <span class="font-weight-bold">下单</span>
      </div>
      <div class="">
        <div>
          <TradeInput
              header="交易对"
              placeholder="点击表格"
              disabled="true"
              :value="pair_item['symbol']"
          />
          <TradeInput
              class="mt-2"
              header="单方开仓金额"
              footer="USDT"
              v-model="want_money"
          />
        </div>
      </div>
      <div class="mt-3 d-flex flex-column">
        <InfoItem header="每边开仓" :content="quantity" :footer="symbol"/>
        <InfoItem header="预计8小时收益" :content="benefit" footer="USDT"/>
        <InfoItem header="总开仓手续费" :content="total_tax" footer="USDT"/>
        <span class="text-muted small align-self-end"
        >现货手续费(以0.075%) {{ tax }} USDT</span
        >
        <span class="text-muted small align-self-end float-right"
        >期货手续费(以0.040%) {{ tax_future }} USDT</span
        >
        <div class="d-flex flex-row justify-content-between mt-2">
          <span class="align-middle text-muted small">现货下单位置</span>
          <div class="d-flex">
            <no-border-button class="btn checkbox ml-2 checkbox-check" v-if="main_mode=='MAIN'"
                              @click="ChangeMainMode('MAIN')">现货
            </no-border-button>
            <no-border-button class="btn checkbox ml-2 checkbox-nocheck" v-if="main_mode!='MAIN'"
                              @click="ChangeMainMode('MAIN')">现货
            </no-border-button>
            <no-border-button class="btn checkbox ml-2 checkbox-check" v-if="main_mode=='MARGIN'"
                              @click="ChangeMainMode('MARGIN')">全仓
            </no-border-button>
            <no-border-button class="btn checkbox ml-2 checkbox-nocheck" v-if="main_mode!='MARGIN'"
                              @click="ChangeMainMode('MARGIN')">全仓
            </no-border-button>
            <no-border-button class="btn checkbox ml-2 checkbox-check" v-if="main_mode=='ISOLATED'"
                              @click="ChangeMainMode('ISOLATED')">逐仓
            </no-border-button>
            <no-border-button class="btn checkbox ml-2 checkbox-nocheck" v-if="main_mode!='ISOLATED'"
                              @click="ChangeMainMode('ISOLATED')">逐仓
            </no-border-button>
          </div>
        </div>
        <div class="d-flex">
          <button
              type="submit"
              class="btn btn-primary mt-3 px-2"
              @click="OpenPosition"
              :disabled="disabled_trade"
              style="background-color: #02c076; border-color: transparent"
          >
            多现货 空期货 (正向)
          </button>
          <button
              type="submit"
              class="btn btn-primary mt-3 px-2 ml-5"
              @click="ClosePosition"
              :disabled="disabled_trade"
              style="background-color: #f84960; border-color: transparent"
          >
            多期货 空现货 (反向)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TradeInput from "@/components/TradeInput.vue";
import InfoItem from "@/components/InfoItem.vue";
import NoBorderButton from "@/components/NoBorderButton";

export default {
  name: "PremiumCreater",

  props: {
    pair_item: {
      type: Object,
      default: {},
    },
  },

  data: function () {
    return {
      // wallet_usdt: 0, // 可用的usdt数量
      // wallet_future_usdt: 0, // 可用的期货usdt数量

      // wallet_bnb_value: 0, // 可用的bnb价值
      // wallet_future_bnb_value: 0, // 可用的期货bnb价值

      want_money: "", // 想要开仓的总价值

      benefit: 0, // 计算的收益
      tax: 0, // 计算的手续费
      tax_future: 0,
      total_tax: 0, // 总开仓手续费
      quantity: 0, // 开仓的币数(需要用于最终下单，所以是字符串)
      symbol: "", // 开仓的货币符号(仅用于显示)
      disabled_trade: true, // 是否将下单按钮无效化

      main_mode: 'MAIN',   // 现货下单模式，可能为MAIN、MARGIN、ISOLATED
    };
  },

  watch: {
    pair_item: function (newItem, oldItem) {
      this.ValueChanged();
    },
    want_money: function (newItem, oldItem) {
      this.ValueChanged();
    },
  },

  methods: {
    // 加仓下单
    OpenPosition: function () {
      // 取出要下单的交易对
      let pair_symbol = this.pair_item["symbol"];
      // 取出要下单的数量
      let quantity = this.quantity;
      // 发送开仓指令
      this.disabled_trade = true;
      this.method_request("trade_premium", [pair_symbol, quantity, 'OPEN', this.main_mode])
          .then((res) => {
            this.showToast().success("加仓成功");
          })
          .catch((err) => {
            console.log(this.showToast);
            this.showToast().error("加仓失败");
          })
          .finally(() => {
            this.disabled_trade = false;
          });
    },

    // 减仓下单
    ClosePosition: function () {
      // 取出要下单的交易对
      let pair_symbol = this.pair_item["symbol"];
      // 取出要下单的数量
      let quantity = this.quantity;
      // 发送指令
      this.disabled_trade = true;
      this.method_request("trade_premium", [pair_symbol, quantity, 'CLOSE', this.main_mode])
          .then((res) => {
            this.showToast().success("减仓成功");
          })
          .catch((err) => {
            console.log(this.showToast);
            this.showToast().error("减仓失败");
          })
          .finally(() => {
            this.disabled_trade = false;
          });
    },

    // 交易对or开仓数改变时重新计算
    ValueChanged: function () {
      // 没有交易对的情况下直接返回
      if (this.pair_item["symbol"] == null) {
        return;
      }

      const CLearOutput = () => {
        this.disabled_trade = true;
        this.benefit = 0;
        this.tax = 0;
        this.tax_future = 0;
        this.total_tax = 0;
        this.quantity = 0;
        this.symbol = "";
      };

      // 输入数字为空的情况下，清空计算结果
      if (this.want_money === "") {
        CLearOutput();
        return;
      }

      // 输入非法的情况下，清空计算结果
      if (
          !(this.isNumber(this.want_money) && parseFloat(this.want_money) >= 0)
      ) {
        CLearOutput();
        return;
      }

      let side_money = parseFloat(this.want_money); // 单边开仓价值
      let price = parseFloat(this.pair_item["price"]); // 交易对单价
      let precision = this.pair_item["precision"]; // 交易对精度
      let rate = parseFloat(this.pair_item["rate"]); // 交易对资金费率

      let quantity = side_money / price;
      // 将数字乘以精度
      quantity *= Math.pow(10, precision);
      // 向下取整
      quantity = Math.floor(quantity);
      // 将数字除以精度
      // 为什么要这么弄？因为浮点数精度问题不可忽视，最终结果不能出现999999
      quantity /= Math.pow(10, precision);

      this.quantity = quantity.toString();

      // 计算收益和手续费
      let benefit = (side_money * rate) / 100;
      let tax = (side_money * 0.075) / 100;
      let tax_future = (side_money * 0.04) / 100;
      let total_tax = tax + tax_future;

      benefit = Math.round(benefit * 1000) / 1000;
      tax = Math.round(tax * 1000) / 1000;

      this.benefit = benefit;
      this.tax = tax;
      this.tax_future = tax_future;
      this.total_tax = total_tax;

      this.symbol = this.pair_item["symbol"].replace("USDT", "");
      this.disabled_trade = false;
    },

    // 切换下单位置
    ChangeMainMode: function (mode) {
      this.main_mode = mode
    },
  },

  components: {
    TradeInput,
    InfoItem,
    NoBorderButton
  },
};
</script>

<style scoped>
.checkbox {
  border-radius: 5px;
  padding: 3px;
}

.checkbox-check {
  background-color: #505050;
  color: #ffffff;
}

.checkbox-nocheck {
  background-color: #e1e1e1;
}
</style>