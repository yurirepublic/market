<template>
  <div class='d-flex justify-content-center p-1'>
    <the-funding-fee-chart />
    <the-server-status class='ml-1' />
    <the-server-info class='ml-1' />
  </div>
</template>

<script>
import TheFundingFeeChart from '@/components/statistics/TheFundingFeeChart'
import TheServerStatus from '@/components/statistics/TheServerStatus'
import TheServerInfo from '@/components/statistics/TheServerInfo'

export default {
  name: 'Statistics',
  components: {
    TheServerStatus,
    TheFundingFeeChart,
    TheServerInfo
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