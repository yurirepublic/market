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
          show: false,
        }
      },
      grid: {
        top: 10,
        right: 10
      },

      sum: 0,
      average: 0,

      ws: null,
      subscribe: null
    }
  },
  methods: {
    fillData: async function() {
      let res = await this.ws.getData(['json', 'fundingFee'])

      // 将每日的统计写入到total当中
      let eachDay = {}
      for (let i = 0; i < res.length; i++) {
        let e = res[i]
        let date = new Date(e['time'])
        let year = date.getFullYear()
        let month = date.getMonth() + 1
        let day = date.getDate()
        let time = year + '-' + month + '-' + day
        let obj = eachDay[time]
        if (obj === undefined) {
          eachDay[time] = 0
        }
        eachDay[time] += parseFloat(e['income'])
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
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()

    setInterval(this.fillData, 2000)

  }

}
</script>

<style scoped>

</style>