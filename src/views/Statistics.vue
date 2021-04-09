<template>
  <div class='d-flex justify-content-center p-1'>
    <the-funding-fee-chart />
  </div>
</template>

<script>
import TheFundingFeeChart from '@/components/charts/TheFundingFeeChart.vue'

export default {
  name: 'Statistics',

  data: function() {
    return {
      ws: null,
      subscribe: null
    }
  },

  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()

  },

  components: {
    TheFundingFeeChart
  }
}
</script>

<style scoped>

</style>