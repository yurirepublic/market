<template>
  <card-frame>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>交易所统计信息</span>
    </div>
    <div class='d-flex flex-column'>
      <info-item header='现货交易对数量'>{{ mainNum }}</info-item>
      <info-item header='期货交易对数量'>{{ futureNum }}</info-item>
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
      ws: null,

      mainNum: NaN,
      futureNum: NaN,

    }
  },
  async mounted() {
    this.ws = await this.connectDataCenter()

    this.ws.getDict(['price', 'main']).then(res =>{
      this.mainNum = Object.keys(res).length
    })

    this.ws.getDict(['price', 'future']).then(res => {
      this.futureNum = Object.keys(res).length
    })

  }


}
</script>

<style scoped>

</style>