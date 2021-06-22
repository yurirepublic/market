<template>
  <div class='p-2' style='background-color: #fafafa'>
    <div class='mb-2 d-flex justify-content-between'>
      <span class='font-weight-bold'>100次资金费率图表</span>
      <span>{{ pairSymbol }}</span>
    </div>
    <ve-line-chart :data='chartData'
                   :grid='grid'
                   :settings='chartSettings'
                   :height='180'
                   :empty-text='emptyText' />

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
        yAxisLabelDigits: 2
      },
      grid: {
        top: 10,
        bottom: 10,
        left: 50,
        right: 10
      },
      emptyText: '请点击表格',

      // priceHistory: [0, 0, 0],
      cache: {},
      ws: null
    }
  },

  watch: {
    async pairSymbol(newSymbol) {
      // 获取这个交易对的历史
      if (this.cache[newSymbol] !== undefined) {
        let history = this.cache[newSymbol]['rate']
        let timestamp = this.cache[newSymbol]['timestamp']
        if (history !== undefined && timestamp !== undefined) {
          this.chartData = {
            dimensions: {
              name: '日期',
              data: timestamp
            },
            measures: [{
              name: '费率',
              data: history
            }]
          }
          return
        }
      }
      this.emptyText = '无历史数据'
    },

    async priceHistory(newVal) {
      this.chartData = {
        dimensions: {
          name: '日期',
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

    // 订阅一下History
    await this.sub.dict(['premium', 'fundingRateHistory'], msg => {
      for (const key of Object.keys(msg)) {
        if (this.cache[key] === undefined) {
          this.cache[key] = {}
        }
        this.cache[key]['rate'] = msg[key]
      }

    }, true)
    await this.sub.dict(['premium', 'fundingRateHistory', 'timestamp'], msg => {
      for (const key of Object.keys(msg)) {
        if (this.cache[key] === undefined) {
          this.cache[key] = {}
        }
        let timestamp = []
        for (const e of msg[key]) {
          timestamp.push(this.timestamp2str(e, true))
        }
        this.cache[key]['timestamp'] = timestamp
      }

    }, true)
  },

  methods: {}

}
</script>

<style scoped>
</style>