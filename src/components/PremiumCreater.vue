<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="">
      <div class="mb-2">
        <span class="font-weight-bold">下单</span>
      </div>
      <div class="">
        <div>
          <TradeInput header="双向交易对" placeholder="点击表格" v-model="pair_symbol" />
          <TradeInput
            class="mt-2"
            type="number"
            header="双向总金额"
            footer="USDT"
          />
        </div>
      </div>
      <div class="mt-3">
				<InfoItem header="每边开仓" :conent="quantity" :footer="symbol" />
				<InfoItem header="预计8小时收益" :conent="benefit" footer="USDT" />
				<InfoItem header="预计开仓手续费(以0.075%)" :conent="tax" footer="USDT" />
        <button
          type="submit"
          class="btn btn-primary mt-3"
          @click="primaryTradeClick"
          :disabled="disabled_trade"
					style="background-color: #02C076; border-color: transparent;"
        >
					双向开仓
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import TradeInput from "@/components/TradeInput.vue";
import InfoItem from "@/components/InfoItem.vue";

export default {
	name: "PremiumCreater",
	
	data: function () {
		return {
			pair_symbol: "", // 想要套利的交易对
      create_value: "", // 开仓的总价值
      create_rate: "", // 开仓的合约杠杆率

      benefit: 0, // 计算的收益
      tax: 0, // 计算的手续费
      quantity: "", // 开仓的币数(需要用于最终下单，所以是字符串)
      symbol: "", // 开仓的货币符号(仅用于显示)
      disabled_trade: true, // 是否将下单按钮无效化
		}
	},

  components: {
    TradeInput,
    InfoItem,
  },
};
</script>

<style scoped>
</style>