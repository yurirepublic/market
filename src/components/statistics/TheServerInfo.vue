<template>
  <card-frame class='p-2 d-flex flex-column' style='width: 25rem'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>服务器连接信息</span>
    </div>

    <div>
      <my-radio :options='radioOptions' :active='radioActive' @click='radioActive=$event' />
    </div>

    <div class='d-flex flex-column'>

    </div>
  </card-frame>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import MyRadio from '@/components/MyRadio'

export default {
  name: 'TheServerInfo',
  components: {
    CardFrame,
    MyRadio
  },
  data: function() {
    return {
      radioOptions: [],
      radioActive: '',

      info: {},

      ws: null,
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    // 获取有哪些服务器
    let msg = await this.ws.getDict(['server', 'info', 'ip'])
    this.radioOptions = Object.keys(msg)
    this.radioActive = this.radioOptions[0]

    // 获取服务器的信息
    // this.info
  }
}
</script>

<style scoped>

</style>