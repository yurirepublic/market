<template>
  <div class='p-2' style='background-color: #fafafa'>
    <div class='mb-2 d-flex justify-content-between'>
      <span class='font-weight-bold'>100次资金费率图表</span>
      <span>{{ pairSymbol }}</span>
    </div>
    <ve-line-chart :data='chartData'
                   :grid='grid'
                   :tooltip-visible='false'
                   :settings='chartSettings'
                   :height='180'
                   empty-text='请点击表格' />

  </div>
</template>

<script>

export default {
  name: 'TheFundingRateHistory',
  components: {},

  props: {
    pairSymbol: ''
  },

  data: function() {
    return {
      chartData: null,
      chartSettings: {
        legendOptions: {
          show: false
        },
        xAxisLabelShow: false,
        yAxisLabelType: 'percentage',
        yAxisLabelDigits: 2,

      },
      grid: {
        top: 10,
        bottom: 10,
        left: 50,
        right: 10
      },

      priceHistory: [0, 0, 0],
      cache: {},
      ws: null
    }
  },

  watch: {
    async pairSymbol(newSymbol) {
      // 获取这个交易对的历史
      if (this.cache[newSymbol]) {
        this.priceHistory = this.cache[newSymbol]
      } else {
        let history = await this.ws.getData(['premium', 'fundingRateHistory', newSymbol])
        if (history === null) {
          this.priceHistory = [0, 0, 0]
        }
      }
    },

    async priceHistory(newVal) {
      this.chartData = {
        dimensions: {
          name: 'time',
          data: [...Object.keys(newVal)]
        },
        measures: [{
          name: '费率',
          data: newVal
        }]
      }
    }
  },

  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.sub = await this.connectSubscribe()
    // 把能拿到的交易对全部拿到做个cache
    this.cache = await this.ws.getDict(['premium', 'fundingRateHistory'])
    // 订阅一下History
    await this.sub.dict(['premium', 'fundingRateHistory'], msg => {
      this.cache[msg['special']] = msg['data']
    })
  },

  methods: {}

}
</script>

<style scoped>
</style>