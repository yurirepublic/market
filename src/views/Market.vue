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

        <div class='mt-1'>
          <the-isolated-transfer />
        </div>


      </div>

      <div class='ml-1'>
        <div class='mt-1 d-flex flex-row'>
          <the-borrowed-panel style='width: 18rem' @query='QueryInterest' />
          <the-interest-history style='width: 15rem' :history-data='interestHistoryData' />
        </div>

        <div class='mt-1'>
          <the-position-analyst style='min-width: 17rem;' @click='clickTable' />
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
import TheIsolatedTransfer from '@/components/market/TheIsolatedTransfer'
import TheBorrowedPanel from '@/components/market/TheBorrowedPanel'
import TheInterestHistory from '@/components/market/TheInterestHistory'

export default {
  name: 'Market',
  components: {
    TheIsolatedTransfer,
    TheMarketTable,
    ThePositionAnalyst,
    TheUsdtWallet,
    ThePositionCreator,
    TheBnbWallet,
    TheFundingRateHistory,
    TheBorrowedPanel,
    TheInterestHistory
  },
  data: function() {
    return {
      pairSymbol: '', // 被选中的符号
      interestHistoryData: []   // 借贷利息历史数据

    }
  },
  methods: {
    clickTable(event) {
      this.pairSymbol = event
    },
    QueryInterest(event) {
      this.interestHistoryData = event
    }
  },
  created: function() {

  },
  mounted: function() {
  }

}
</script>

<style scoped>
</style>