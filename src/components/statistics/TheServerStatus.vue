<template>
  <card-frame class='p-2 d-flex flex-column' style='width: 25rem'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>服务器性能计数器</span>
    </div>

    <ve-line-chart :data='chartData' :settings='chartSettings' :grid='grid' :height='200'></ve-line-chart>

    <div>
      <span>CPU：{{ toFixed(cpuPercent, 1) }}%</span>
    </div>

    <div class='mt-1 d-flex flex-column'>
      <span>内存：{{ toFixed(ramPercent, 1) }}%</span>
      <span>内存可用空间：{{ toFixed(ramAvailable / (1 << 20), 2) }} MB</span>
      <span>内存总大小：{{ toFixed(ramTotal / (1 << 20), 2) }} MB</span>
    </div>

    <div class='mt-1 d-flex flex-column'>
      <span>硬盘：{{ toFixed(diskPercent, 1) }}%</span>
      <span>硬盘可用空间：{{ toFixed(diskFree / (1 << 30), 2) }} GB</span>
      <span>硬盘总大小：{{ toFixed(diskTotal / (1 << 30), 2) }} GB</span>
    </div>

  </card-frame>
</template>

<script>
import CardFrame from '@/components/CardFrame'

export default {
  name: 'TheServerStatus',
  components: {
    CardFrame
  },
  data: function() {
    return {
      chartData: {},
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

      cpuPercent: 0,
      cpuObj: null,   // 图表的对象，在mounted有初始化

      ramPercent: 0,
      ramTotal: 0,
      ramAvailable: 0,
      ramObj: null,

      diskPercent: 0,
      diskTotal: 0,
      diskFree: 0,
      diskObj: null,

      chartInterval: null,

      ws: null,
      subscribe: null
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()
    if (this.chartInterval !== null) {
      clearInterval(this.chartInterval)
    }

    setInterval(async () => {
      // 塞入默认数据
      let defaultData = {
        dimensions: {
          name: 'time',
          data: [...new Array(100).keys()]
        },

        measures: []
      }

      // 每5s向服务器轮询图表（使用subscribe没法同步获取所有数据）
      let msg = await this.ws.getDict(['server', 'status', 'usage', 'percentHistory', 'us1'])
      defaultData['measures'].push({
        name: 'cpu',
        data: msg['cpu'].map(x => x / 100)
      })
      defaultData['measures'].push({
        name: 'ram',
        data: msg['ram'].map(x => x / 100)
      })
      defaultData['measures'].push({
        name: 'disk',
        data: msg['disk'].map(x => x / 100)
      })
      this.chartData = defaultData

    }, 5000)


    // 订阅服务器计数器信息
    await this.subscribe.dict(['server', 'status', 'usage', 'cpu', 'us1'], (msg) => {
      switch (msg['special']) {
        case 'percent':
          this.cpuPercent = msg['data']
          break
      }
    })

    await this.subscribe.dict(['server', 'status', 'usage', 'ram', 'us1'], (msg) => {
      switch (msg['special']) {
        case 'percent':
          this.ramPercent = msg['data']
          break
        case 'total':
          this.ramTotal = msg['data']
          break
        case 'available':
          this.ramAvailable = msg['data']
          break
      }
    })

    await this.subscribe.dict(['server', 'status', 'usage', 'disk', 'us1'], (msg) => {
      switch (msg['special']) {
        case 'percent':
          this.diskPercent = msg['data']
          break
        case 'total':
          this.diskTotal = msg['data']
          break
        case 'free':
          this.diskFree = msg['data']
          break
      }
    })

  }
}
</script>

<style scoped>

</style>