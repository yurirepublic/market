<template>
  <card-frame class='p-2 d-flex flex-column' style='width: 25rem' v-if='!loading'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>服务器性能计数器</span>
    </div>

    <div>
      <my-radio :options='radioOptions' :active='radioActive' @click='radioActive=$event' />
    </div>




    <div class='d-flex flex-column' v-for='(value, name) in status' :key='name' v-if='radioActive === name'>
      <ve-line-chart
        :data="value['chartData']"
        :settings='chartSettings'
        :grid='grid'
        :height='200'
      />

      <div>
        <span>CPU：{{ toFixed(value['cpuPercent'], 1) }}%</span>
      </div>

      <div class='mt-1 d-flex flex-column'>
        <span>内存：{{ toFixed(value['ramPercent'], 1) }}%</span>
        <span>内存可用空间：{{ toFixed(value['ramAvailable'] / (1 << 20), 2) }} MB</span>
        <span>内存总大小：{{ toFixed(value['ramTotal'] / (1 << 20), 2) }} MB</span>
      </div>

      <div class='mt-1 d-flex flex-column'>
        <span>硬盘：{{ toFixed(value['diskPercent'], 1) }}%</span>
        <span>硬盘可用空间：{{ toFixed(value['diskFree'] / (1 << 30), 2) }} GB</span>
        <span>硬盘总大小：{{ toFixed(value['diskTotal'] / (1 << 30), 2) }} GB</span>
      </div>


    </div>

  </card-frame>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import MyRadio from '@/components/MyRadio'

export default {
  name: 'TheServerStatus',
  components: {
    CardFrame,
    MyRadio
  },
  data: function() {
    return {
      chartSettings: {
        xAxisLabelShow: false,
        yAxisLabelType: 'percentage',
        percentage: true
      },
      grid: {
        top: 30,
        right: 10,
        bottom: 10
      },

      radioOptions: [],
      radioActive: '',

      chartData: {},
      status: {},   // key是服务器昵称，内是运行状态


      ws: null,
      subscribe: null,

      loading: true
    }
  },
  watch: {
    // radioActive: function(newVal) {
    //   // 将newVal的表单数据填充到变量上
    //   this.chartData = this.status[newVal]['chartData']
    //   console.log('a')
    // }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()

    // 获取有什么服务器
    let msg = await this.ws.getDict(['server', 'status', 'cpu', 'usage', 'percent'])
    this.radioOptions = Object.keys(msg)

    // 默认激活第一个服务器
    this.radioActive = this.radioOptions[0]

    // 对每个服务器都订阅
    for (const nickname of this.radioOptions) {
      this.$set(this.status, nickname, {})

      // 订阅服务器计数器信息
      await this.subscribe.dict(['server', 'status', 'usage', 'cpu', nickname], (msg) => {
        switch (msg['special']) {
          case 'percent':
            this.$set(this.status[nickname], 'cpuPercent', msg['data'])
            break
          case 'percentHistory':
            // 塞入默认数据
            let chartData = {
              dimensions: {
                name: '时间序列',
                data: [...new Array(100).keys()]
              },
              measures: [
                {
                  name: 'CPU',
                  data: msg['data'].map(x => x / 100)
                }
              ]
            }
            this.$set(this.status[nickname], 'chartData', chartData)
            // this.status[nickname]['chartData'] = chartData
            break
        }
      })

      await this.subscribe.dict(['server', 'status', 'usage', 'ram', nickname], (msg) => {
        switch (msg['special']) {
          case 'percent':
            this.$set(this.status[nickname], 'ramPercent', msg['data'])
            break
          case 'total':
            this.$set(this.status[nickname], 'ramTotal', msg['data'])
            break
          case 'available':
            this.$set(this.status[nickname], 'ramAvailable', msg['data'])
            break
        }
      })

      await this.subscribe.dict(['server', 'status', 'usage', 'disk', nickname], (msg) => {
        switch (msg['special']) {
          case 'percent':
            this.$set(this.status[nickname], 'diskPercent', msg['data'])
            break
          case 'total':
            this.$set(this.status[nickname], 'diskTotal', msg['data'])
            break
          case 'free':
            this.$set(this.status[nickname], 'diskFree', msg['data'])
            break
        }
      })
    }

    this.loading = false

    //
    // setInterval(async () => {
    //   // 塞入默认数据
    //   let defaultData = {
    //     dimensions: {
    //       name: 'time',
    //       data: [...new Array(100).keys()]
    //     },
    //
    //     measures: []
    //   }
    //
    //   // 每5s向服务器轮询图表（使用subscribe没法同步获取所有数据）
    //   let msg = await this.ws.getDict(['server', 'status', 'usage', 'percentHistory', 'us1'])
    //   defaultData['measures'].push({
    //     name: 'cpu',
    //     data: msg['cpu'].map(x => x / 100)
    //   })
    //   defaultData['measures'].push({
    //     name: 'ram',
    //     data: msg['ram'].map(x => x / 100)
    //   })
    //   defaultData['measures'].push({
    //     name: 'disk',
    //     data: msg['disk'].map(x => x / 100)
    //   })
    //   this.chartData = defaultData
    //
    // }, 5000)


  }
}
</script>

<style scoped>

</style>