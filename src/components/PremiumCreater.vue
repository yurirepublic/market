<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="">
      <div class="mb-2">
        <span class="font-weight-bold">下单</span>
      </div>
      <div class="">
        <div>
          <TradeInput
            header="双向交易对"
            placeholder="点击表格"
            disabled="true"
            :value="pair_item['symbol']"
          />
          <TradeInput
            class="mt-2"
            header="双向总金额"
            footer="USDT"
            v-model="want_money"
          />
        </div>
      </div>
      <div class="mt-3">
        <InfoItem header="每边开仓" :content="quantity" :footer="symbol" />
        <InfoItem header="预计8小时收益" :content="benefit" footer="USDT" />
        <InfoItem
          header="预计开仓手续费(以0.075%)"
          :content="tax"
          footer="USDT"
        />
        <div class="d-flex">
          <button
            type="submit"
            class="btn btn-primary mt-3 px-2"
            @click="OpenPosition"
            :disabled="disabled_trade"
            style="background-color: #02c076; border-color: transparent"
          >
            双向开仓
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TradeInput from "@/components/TradeInput.vue";
import InfoItem from "@/components/InfoItem.vue";

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
      want_money: "", // 想要开仓的总价值
      want_rate: "", // 开仓的合约杠杆率

      benefit: 0, // 计算的收益
      tax: 0, // 计算的手续费
      quantity: 0, // 开仓的币数(需要用于最终下单，所以是字符串)
      symbol: "", // 开仓的货币符号(仅用于显示)
      disabled_trade: true, // 是否将下单按钮无效化
    };
  },

  watch: {
    pair_item: function (newItem, oldItem) {
      this.valueChanged();
    },
    want_money: function (newItem, oldItem) {
      this.valueChanged();
    },
  },

  methods: {
    // 开仓下单
    OpenPosition: function () {
      // 取出要下单的交易对
      let pair_symbol = this.pair_item["symbol"];
      // 取出要下单的数量
      let quantity = this.quantity;
      // 发送开仓指令
      this.disabled_trade = true;
      this.method_request("create_premium", [pair_symbol, quantity])
        .then((res) => {
          this.showToast().success("开仓成功");
        })
        .catch((err) => {
          console.log(this.showToast);
          this.showToast().error("开仓失败");
        })
        .finally(() => {
          this.disabled_trade = false;
        });
    },

    // 交易对or开仓数改变时重新计算
    valueChanged: function () {
      // 没有交易对的情况下直接返回
      if (this.pair_item["symbol"] == null) {
        return;
      }

      // 输入数字为空的情况下，清空计算结果
      if (this.want_money == "") {
        this.disabled_trade = true;
        this.benefit = 0;
        this.tax = 0;
        this.quantity = 0;
        this.symbol = "";
        return;
      }

      // 输入非法的情况下，清空计算结果
      if (
        !(this.isNumber(this.want_money) && parseFloat(this.want_money) >= 0)
      ) {
        this.disabled_trade = true;
        this.benefit = 0;
        this.tax = 0;
        this.quantity = 0;
        this.symbol = "";
        return;
      }

      let side_money = parseFloat(this.want_money) / 2; // 单边开仓价值
      let price = parseFloat(this.pair_item["price"]);
      let percision = this.pair_item["percision"];
      let rate = parseFloat(this.pair_item["rate"]);

      let quantity = side_money / price;
      // 将数字乘以精度
      quantity *= Math.pow(10, percision);
      // 向下取整
      quantity = Math.floor(quantity);
      // 将数字除以精度
      // 为什么要这么弄？因为浮点数精度问题不可忽视，最终结果不能出现999999
      quantity /= Math.pow(10, percision);

      this.quantity = quantity.toString();

      // 计算收益和手续费
      let benefit = (side_money * 2 * rate) / 100;
      let tax = (side_money * 2 * 0.075) / 100;

      benefit = Math.round(benefit * 1000) / 1000;
      tax = Math.round(tax * 1000) / 1000;

      this.benefit = benefit;
      this.tax = tax;

      this.symbol = this.pair_item["symbol"].replace("USDT", "");
      this.disabled_trade = false;
    },
  },

  components: {
    TradeInput,
    InfoItem,
  },
};
</script>

<style scoped>
</style>