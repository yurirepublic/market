<template>
  <card-frame>
    <div class='mb-2 d-flex justify-content-between align-items-center' style='width: 30rem'>
      <span class='font-weight-bold'>每日套利金额</span>
      <div>
        <span class='font-weight-bold'>平均 {{ toFixed(average, 2) }}＄</span>
        <span class='font-weight-bold ml-2'>总计 {{ toFixed(sum, 2) }}＄</span>
      </div>

    </div>
    <ve-line-chart :data='chartData' :grid='grid' :settings='chartSettings' />
  </card-frame>

</template>

<script>
import CardFrame from '@/components/CardFrame'

export default {
  name: 'TheFundingFeeChart',
  components: {
    CardFrame
  },
  data: function() {
    return {
      chartData: {},
      chartSettings: {
        legendOptions: {
          show: false
        },
        smooth: true
      },
      grid: {
        top: 10,
        right: 10
      },

      sum: 0,
      average: 0,

      ws: null,
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    await this.ws.subscribePrecise(['json', 'fundingFee'], async msg => {
      await this.fillData(msg)
    }, true)

  },
  methods: {
    // 将传入的数据经过处理后填充到表格
    fillData: async function(msg) {

      // 将每日的统计写入到total当中
      let eachDay = {}
      for (let i = 0; i < msg.length; i++) {
        let e = msg[i]
        let timeStr = this.timestamp2str(e['time'])
        let obj = eachDay[timeStr]
        if (obj === undefined) {
          eachDay[timeStr] = 0
        }
        eachDay[timeStr] += parseFloat(e['income'])
      }

      // 获取全部收入统计
      let sum = 0
      Object.values(eachDay).forEach(e => {
        sum += e
      })
      this.sum = sum

      this.average = sum / Object.values(eachDay).length

      this.chartData = {
        dimensions: {
          name: '日期',
          data: Object.keys(eachDay)
        },
        measures: [
          {
            name: '套利收入',
            data: Object.values(eachDay).map(x => this.toFixed(x, 2))
          }
        ]
      }
    }
  }


}
</script>

<style scoped>

</style>