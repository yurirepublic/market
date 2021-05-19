<template>
  <div>
    <div class='d-flex justify-content-center p-1'>
      <the-funding-fee-chart />
      <the-server-status class='ml-1' />
      <the-server-info class='ml-1' />

    </div>
    <div class='d-flex'>
      <the-exchange-info />
    </div>

  </div>


</template>

<script>
import TheFundingFeeChart from '@/components/statistics/TheFundingFeeChart'
import TheServerStatus from '@/components/statistics/TheServerStatus'
import TheServerInfo from '@/components/statistics/TheServerInfo'
import TheExchangeInfo from '@/components/statistics/TheExchangeInfo'

export default {
  name: 'Statistics',
  components: {
    TheServerStatus,
    TheFundingFeeChart,
    TheServerInfo,
    TheExchangeInfo
  },
  data: function() {
    return {}
  },

  mounted: async function() {
  }


}
</script>

<style scoped>

</style>