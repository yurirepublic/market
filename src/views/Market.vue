<template>
  <div class='d-flex justify-content-center p-1'>
    <div class='d-flex justify-content-center'>
      <div class=''>
        <div class=''>
          <the-market-table @click='clickTable' />
        </div>

        <div class='mt-1' style='width: 26rem'>
          <the-position-creator :pair-symbol='pairSymbol' />
        </div>
      </div>

      <div class='ml-1' style='width: 18rem'>
        <div>
          <the-funding-rate-history :pair-symbol='pairSymbol' />
        </div>

        <div class='mt-1'>
          <the-usdt-wallet />
        </div>

        <div class='mt-1'>
          <the-bnb-wallet />
        </div>
      </div>

      <div class='ml-1'>
        <div>
          <the-position-analyst @click='clickTable' />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import TheMarketTable from '@/components/market/TheMarketTable.vue'
import ThePositionAnalyst from '@/components/market/ThePositionAnalyst.vue'
import TheUsdtWallet from '@/components/market/TheUsdtWallet.vue'
import ThePositionCreator from '@/components/market/ThePositionCreator.vue'
import TheBnbWallet from '@/components/market/TheBnbWallet.vue'
import TheFundingRateHistory from '@/components/market/TheFundingRateHistory.vue'

export default {
  name: 'Market',
  data: function() {
    return {
      pairSymbol: '' // 被选中的符号
    }
  },
  methods: {
    clickTable(event) {
      this.pairSymbol = event
    }
  },
  created: function() {

  },
  mounted: function() {
  },
  components: {
    TheMarketTable,
    ThePositionAnalyst,
    TheUsdtWallet,
    ThePositionCreator,
    TheBnbWallet,
    TheFundingRateHistory
  }
}
</script>

<style scoped>
</style>