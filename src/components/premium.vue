<template>
  <div class="d-flex justify-content-center p-1">
    <div class="d-flex justify-content-center">
      <div class="">
        <div class="">
          <PremiumTable @click="clickTable" />
        </div>

        <div class="mt-1">
          <PremiumCreater :pair_item="pair_item" />
        </div>
      </div>

      <div class="ml-1">
        <div>
          <Wallet />
        </div>

        <div class="mt-1">
          <BNBWallet />
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
import BNBWallet from "@/components/BNBWallet.vue";

export default {
  name: "premium",
  data: function () {
    return {
      pair_item: {}, // 被选中的对象
      // havingItems: [], // 套利持仓表格

      // free_usdt: "", // 现货剩余usdt
      // free_future_usdt: "", // 期货剩余usdt

      // pair_symbol: "", // 想要套利的交易对
      // create_value: "", // 开仓的总价值
      // create_rate: "", // 开仓的合约杠杆率

      // benefit: 0, // 计算的收益
      // tax: 0, // 计算的手续费
      // quantity: "", // 开仓的币数(需要用于最终下单，所以是字符串)
      // symbol: "", // 开仓的货币符号(仅用于显示)
      // disabled_trade: true, // 是否将下单按钮无效化
    };
  },
  methods: {
    clickTable(event) {
      this.pair_item = event;
    },

    // // 刷新账户余额
    // refreshWallet: function () {
    //   this.free_usdt = "";
    //   this.free_future_usdt = "";
    //   // 获取账户余额
    //   method_request("wallet_money", []).then((res) => {
    //     this.free_usdt = res[0];
    //     this.free_future_usdt = res[1];
    //   });
    // },

    // // 自动填写货币对
    // premiumClickAction: function (pair_symbol) {
    //   console.log(pair_symbol);
    //   // 更新一下要下单的货币种类
    //   this.pair_symbol = pair_symbol;
    //   this.premiumValueChange(); // 主动触发一下事件刷新信息
    // },
  },
  mounted: function () {},
  components: {
    PremiumTable,
    PremiumHaving,
    Wallet,
    PremiumCreater,
    BNBWallet,
  },
};
</script>

<style scoped>
</style>