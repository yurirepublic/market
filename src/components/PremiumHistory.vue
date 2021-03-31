<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="mb-2 d-flex justify-content-between">
      <span class="font-weight-bold">100次资金费率图表</span>
      <span>{{ pairSymbol }}</span>
    </div>
    <TrendChart
        :datasets="[
        {
          data: priceHistory,
          smooth: false,
          fill: true,
        },
      ]"
        :labels="{
        yLabels: 5,
        yLabelsTextFormatter: (val) => Math.round(val * 10000) / 100 + '%',
      }"
        :grid="{
        horizontalLines: true,
        horizontalLinesNumber: 5,
        verticalLines: true,
        verticalLinesNumber: 1,
      }"
    >
    </TrendChart>
  </div>
</template>

<script>
import TrendChart from "vue-trend-chart";

export default {
  name: "PremiumHistory",

  props: {
    pairSymbol: ''
  },

  data: function () {
    return {
      priceHistory: [0, 0, 0],
      cache: {},
      ws: null,
    };
  },

  watch: {
    async pairSymbol(newVal) {
      // 获取这个交易对的历史
      if (this.cache[newVal]) {
        this.priceHistory = this.cache[newVal]
      }
      else {
        this.priceHistory = await this.ws.getData(['premium', 'fundingRateHistory', newVal])
      }
    },
  },

  mounted: async function () {
    this.ws = await this.connectDataCenter()
    this.sub = await this.connectSubscribe()
    // 把能拿到的交易对全部拿到做个cache
    this.cache = await this.ws.getDict(['premium', 'fundingRateHistory'])
    // 订阅一下History
    await this.sub.dict(['premium', 'fundingRateHistory'], msg => {
      this.cache[msg['special']] = msg['data']
    })
  },

  methods: {},
  components: {
    TrendChart,
  },
};
</script>

<style scoped>
</style>