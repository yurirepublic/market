<template>
  <card-frame>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>交易所统计信息</span>
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
  name: 'TheExchangeInfo',
  components: {
    CardFrame,
    MyRadio,
    InfoItem
  },
  data() {
    return {
      ws: null
    }
  },
  async mounted() {
    this.ws = await this.connectDataCenter()

  }


}
</script>

<style scoped>

</style>