<template>
  <card-frame class='p-2 d-flex flex-column' style='width: 18rem' v-if='!loading'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>服务器性能计数器</span>
    </div>

    <div class='d-flex justify-content-between align-content-center'>
      <span class='small'>选择服务器</span>
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
        <info-item header='CPU' footer='%'>{{ toFixed(value['cpuPercent'], 1) }}</info-item>
      </div>

      <div class='mt-1 d-flex flex-column'>

        <info-item header='内存' footer='%'>{{ toFixed(value['ramPercent'], 1) }}</info-item>
        <info-item header='内存可用空间' footer='MB'>{{ toFixed(value['ramAvailable'] / (1 << 20), 2) }}</info-item>
        <info-item header='内存总大小' footer='MB'>{{ toFixed(value['ramTotal'] / (1 << 20), 2) }}</info-item>
      </div>

      <div class='mt-1 d-flex flex-column'>
        <info-item header='硬盘' footer='%'>{{ toFixed(value['diskPercent'], 1) }}</info-item>
        <info-item header='硬盘可用空间' footer='GB'>{{ toFixed(value['diskFree'] / (1 << 30), 2) }}</info-item>
        <info-item header='硬盘总大小' footer='GB'>{{ toFixed(value['diskTotal'] / (1 << 30), 2) }}</info-item>
      </div>


    </div>

  </card-frame>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import MyRadio from '@/components/MyRadio'
import InfoItem from '@/components/InfoItem'

export default {
  name: 'TheServerStatus',
  components: {
    CardFrame,
    MyRadio,
    InfoItem
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
        left: 40,
        bottom: 10
      },

      radioOptions: [],
      radioActive: '',

      status: {},   // key是服务器昵称，内是运行状态


      ws: null,
      subscribe: null,

      loading: true
    }
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

      // 初始化图表
      this.status[nickname]['chartData'] = {
        dimensions: {
          name: '时间序列',
          data: [...new Array(100).keys()]
        },
        measures: [
          {
            name: 'CPU',
            data: [...new Array(100).values()]
          },
          {
            name: '内存',
            data: [...new Array(100).values()]
          }
        ]
      }


      // 订阅服务器计数器信息
      await this.subscribe.dict(['server', 'status', 'usage', 'cpu', nickname], (msg) => {
        switch (msg['special']) {
          case 'percent':
            this.status[nickname]['cpuPercent'] = msg['data']
            break
          case 'percentHistory':
            this.status[nickname]['chartData']['measures'][0]['data'] = msg['data'].map(x => parseFloat(this.toFixed(x / 100, 2)))
            // chart需要使用浅拷贝再赋值才能刷新图表
            let obj = Object.assign({}, this.status[nickname]['chartData'])
            this.$set(this.status[nickname], 'chartData', obj)
            this.$set(this.status, 'nickname', this.status[nickname])
            break
        }
      })

      await this.subscribe.dict(['server', 'status', 'usage', 'ram', nickname], (msg) => {
        switch (msg['special']) {
          case 'percent':
            this.status[nickname]['ramPercent'] = msg['data']
            break
          case 'total':
            this.status[nickname]['ramTotal'] = msg['data']
            break
          case 'available':
            this.status[nickname]['ramAvailable'] = msg['data']
            break
          case 'percentHistory':
            this.status[nickname]['chartData']['measures'][1]['data'] = msg['data'].map(x => parseFloat(this.toFixed(x / 100, 2)))
            break
        }
      })

      await this.subscribe.dict(['server', 'status', 'usage', 'disk', nickname], (msg) => {
        switch (msg['special']) {
          case 'percent':
            this.status[nickname]['diskPercent'] = msg['data']
            break
          case 'total':
            this.status[nickname]['diskTotal'] = msg['data']
            break
          case 'free':
            this.status[nickname]['diskFree'] = msg['data']
            break
        }
      })
    }

    this.loading = false
  }
}
</script>

<style scoped>

</style>