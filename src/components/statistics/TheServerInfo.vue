<template>
  <card-frame class='p-2 d-flex flex-column' style='width: 25rem'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>服务器连接信息</span>
    </div>

    <div class='d-flex justify-content-between align-content-center'>
      <span class='small'>选择服务器</span>
      <my-radio :options='radioOptions' :active='radioActive' @click='radioActive=$event' />
    </div>

    <div class='d-flex flex-column' v-for='(value, name) in info' :key='name' v-if='radioActive === name'>
      <info-item header='服务器地址'>{{ value['ip'] }}</info-item>
      <info-item header='api端口'>{{ value['api'] }}</info-item>
      <info-item header='数据中心端口'>{{ value['datacenter'] }}</info-item>
      <info-item header='订阅端口'>{{ value['subscribe'] }}</info-item>
    </div>
  </card-frame>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import MyRadio from '@/components/MyRadio'
import InfoItem from '@/components/InfoItem'

export default {
  name: 'TheServerInfo',
  components: {
    InfoItem,
    CardFrame,
    MyRadio
  },
  data: function() {
    return {
      radioOptions: [],
      radioActive: '',

      info: {},

      ws: null
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    // 获取有哪些服务器
    let ip = await this.ws.getDict(['server', 'info', 'ip'])
    this.radioOptions = Object.keys(ip)
    this.radioActive = this.radioOptions[0]

    // 获取服务器的地址信息
    for (const nickname of Object.keys(ip)) {
      this.$set(this.info, nickname, {})
      this.info[nickname]['ip'] = ip[nickname]

      // 获取服务器端口信息
      let port = await this.ws.getDict(['server', 'info', 'port', nickname])
      this.info[nickname]['api'] = port['api']
      this.info[nickname]['datacenter'] = port['datacenter']
      this.info[nickname]['subscribe'] = port['subscribe']
    }
  }
}
</script>

<style scoped>

</style>