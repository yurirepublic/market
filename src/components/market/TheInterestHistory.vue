<template>
  <card-frame>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>利息历史</span>
    </div>
    <ve-line-chart :data='chartData'
                   :grid='grid'
                   :settings='chartSettings'
                   :height='180'
                   empty-text='等待查询' />
  </card-frame>


</template>

<script>
import CardFrame from '@/components/CardFrame'

export default {
  name: 'TheInterestHistory',
  components: {
    CardFrame
  },
  props: {
    historyData: {}

  },
  watch: {
    historyData: function(newVal) {
      // 先对数据进行分离处理
      let rate = []
      let timestamp = []
      for (const e of newVal) {
        rate.unshift(e['dailyInterestRate'])
        timestamp.unshift(this.timestamp2str(e['timestamp'], true))
      }


      this.chartData = {
        dimensions: {
          name: '日期',
          data: timestamp
        },
        measures: [{
          name: '日利息',
          data: rate
        }]
      }
    }
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
      }
    }
  },
  methods: {}
}
</script>

<style scoped>

</style>