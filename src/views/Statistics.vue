<template>
  <div class='d-flex justify-content-center p-1'>
    <the-funding-fee-chart />
    <the-server-status class='ml-1' />
  </div>
</template>

<script>
import TheFundingFeeChart from '@/components/statistics/TheFundingFeeChart'
import TheServerStatus from '@/components/statistics/TheServerStatus'

export default {
  name: 'Statistics',
  components: {
    TheServerStatus,
    TheFundingFeeChart
  },
  data: function() {
    return {
      ws: null,
      subscribe: null
    }
  },

  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()

  }


}
</script>

<style scoped>

</style>