<template>
  <div class="d-flex justify-content-center p-1">
    <div class="d-flex justify-content-center">
      <div class="">
        <div class="">
          <PremiumTable />
        </div>

        <div class="mt-1">
          <PremiumCreater />
        </div>
      </div>

      <div class="ml-1">
        <div>
          <Wallet />
        </div>

        <div class="mt-1">
          <PremiumHaving />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// 单独改变背景颜色
document.body.style.backgroundColor = "#f5f5f5";

import PremiumTable from "@/components/PremiumTable.vue";
import PremiumHaving from "@/components/PremiumHaving.vue";
import Wallet from "@/components/Wallet.vue";
import PremiumCreater from "@/components/PremiumCreater.vue";

export default {
  name: "premium",
  data: function () {
    return {
      havingItems: [], // 套利持仓表格

      free_usdt: "", // 现货剩余usdt
      free_further_usdt: "", // 期货剩余usdt

      pair_symbol: "", // 想要套利的交易对
      create_value: "", // 开仓的总价值
      create_rate: "", // 开仓的合约杠杆率

      benefit: 0, // 计算的收益
      tax: 0, // 计算的手续费
      quantity: "", // 开仓的币数(需要用于最终下单，所以是字符串)
      symbol: "", // 开仓的货币符号(仅用于显示)
      disabled_trade: true, // 是否将下单按钮无效化
    };
  },
  methods: {
    // 刷新账户余额
    refreshWallet: function () {
      this.free_usdt = "";
      this.free_further_usdt = "";
      // 获取账户余额
      method_request("wallet_money", []).then((res) => {
        this.free_usdt = res[0];
        this.free_further_usdt = res[1];
      });
    },

    // 自动填写货币对
    premiumClickAction: function (pair_symbol) {
      console.log(pair_symbol);
      // 更新一下要下单的货币种类
      this.pair_symbol = pair_symbol;
      this.premiumValueChange(); // 主动触发一下事件刷新信息
    },

    // 平仓下单
    premiumDestoryClick: function (pair_symbol, quantity) {
      console.log("平仓下单符号", pair_symbol);
      console.log("平仓下单数量", quantity);
      method_request("destroy_premium", [pair_symbol, quantity]);
    },

    // 开仓下单
    primaryTradeClick: function () {
      // 取出要下单的交易对
      let pair_symbol = this.pair_symbol;
      // 取出要下单的数量
      let quantity = this.quantity;
      // 发送开仓指令
      method_request("create_premium", [pair_symbol, quantity]);
    },

    // 自动计算收益
    premiumValueChange: function (event) {
      console.log(this.create_value);
      // 输入数字为空的情况下，清空计算结果
      if (this.create_value == "") {
        this.disabled_trade = true;
        this.benefit = 0;
        this.tax = 0;
        this.quantity = 0;
        this.symbol = "";
        return;
      }
      let side_value = parseFloat(this.create_value) / 2; // 单边开仓价值
      let price = 0; // 等待读取的币价
      let percision = 0; // 等待读取的精度
      let rate = 0; // 等待读取的利率
      this.items.forEach((e) => {
        if (e["symbol"] == this.pair_symbol) {
          price = parseFloat(e["price"]);
          percision = e["percision"];
          rate = e["rate"];
        }
      });
      if (price != 0) {
        let quantity = side_value / price;
        // 将数字乘以精度
        quantity *= Math.pow(10, percision);
        // 向下取整
        quantity = Math.floor(quantity);
        // 将数字除以精度
        // 为什么要这么弄？因为浮点数精度问题不可忽视，最终结果不能出现999999
        quantity /= Math.pow(10, percision);

        this.quantity = quantity.toString();

        // 计算收益和手续费
        let benefit = (side_value * 2 * rate) / 100;
        let tax = (side_value * 2 * 0.075) / 100;

        benefit = Math.round(benefit * 1000) / 1000;
        tax = Math.round(tax * 1000) / 1000;

        this.benefit = benefit;
        this.tax = tax;

        this.symbol = this.pair_symbol.replace("USDT", "");
        this.disabled_trade = false;
      }
    },
  },
  mounted: function () {},
  components: {
    PremiumTable,
    PremiumHaving,
    Wallet,
    PremiumCreater,
  },
};
</script>

<style scoped>
</style>