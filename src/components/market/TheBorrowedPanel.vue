<template>
  <card-frame>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>借贷与还款</span>
    </div>
    <div class='d-flex justify-content-between'>
      <trade-input class='' header='资产名' v-model='asset' />
      <no-border-button class='ml-1 no-wrap' @click='QueryInterest' :disabled='waiting'>查询利息</no-border-button>
    </div>

    <trade-input class='mt-1' header='资产数量' v-model='amount' />
    <div class='px-1'>
      <info-item header='8时利息'>{{ toFixed(interestRate * 100, 3) }} %</info-item>
      <info-item header='操作位置'>
        <my-radio :options='["全仓", "逐仓base", "逐仓quote"]' :active='borrowedMode'
                  @click='borrowedMode = $event'></my-radio>
      </info-item>
      <trade-input class='mt-1' header='逐仓符号' v-model='isolatedSymbol'
                   v-if='borrowedMode === "逐仓base" || borrowedMode === "逐仓quote"' />
    </div>

    <div class='d-flex justify-content-end mt-2'>
      <button
        type='submit'
        class='btn btn-primary px-2'
        @click='Repay'
        :disabled='waiting'
        style='background-color: #f84960; border-color: transparent'
      >
        还款
      </button>
      <button
        class='btn btn-primary px-2 ml-2'
        @click='Loan'
        :disabled='waiting'
        style='background-color: #02c076; border-color: transparent'
      >
        借贷
      </button>
    </div>


  </card-frame>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import TradeInput from '@/components/TradeInput'
import InfoItem from '@/components/InfoItem'
import NoBorderButton from '@/components/NoBorderButton'
import MyRadio from '@/components/MyRadio'

export default {
  name: 'TheBorrowedPanel',
  components: {
    CardFrame,
    TradeInput,
    InfoItem,
    NoBorderButton,
    MyRadio
  },
  data: function() {
    return {
      asset: '',
      amount: '',

      interestRate: NaN,

      borrowedMode: '全仓',
      isolatedSymbol: '',

      waiting: false,

      ws: null
    }
  },
  mounted: function() {
    this.ws = this.connectDataCenter()
  },
  methods: {
    QueryInterest: async function() {
      this.waiting = true
      this.apiRequest('query_interest', [this.asset]).then(res => {
        this.showToast.success('查询成功')
        this.interestRate = res['data'][0]['dailyInterestRate'] / 3
        this.$emit('query', res['data'])
      }).catch(err => {
        this.showToast.error('查询失败')
        this.interestRate = NaN
      }).finally(() => {
        this.waiting = false
      })
    },
    Loan: async function() {
      let isIsolated = null
      if (this.borrowedMode === '全仓') {
        isIsolated = false
      } else if (this.borrowedMode === '逐仓base' || this.borrowedMode === '逐仓quote') {
        isIsolated = true
      } else {
        console.error('未知的借贷模式', this.borrowedMode)
      }

      this.waiting = true
      this.apiRequest('loan', [this.asset, isIsolated, this.isolatedSymbol, this.amount]).then(res => {
        this.showToast.success('借贷成功')
      }).catch(err => {
        this.showToast.error('借贷失败')
      }).finally(() => {
        this.waiting = false
      })
    },
    Repay: async function() {
      let isIsolated = null
      if (this.borrowedMode === '全仓') {
        isIsolated = false
      } else if (this.borrowedMode === '逐仓base' || this.borrowedMode === '逐仓quote') {
        isIsolated = true
      } else {
        console.error('未知的借贷模式', this.borrowedMode)
      }

      this.waiting = true
      this.apiRequest('repay', [this.asset, isIsolated, this.isolatedSymbol, this.amount]).then(res => {
        this.showToast.success('还款成功')
      }).catch(err => {
        this.showToast.error('还款失败')
      }).finally(() => {
        this.waiting = false
      })
    }

  }
}
</script>

<style scoped>
.no-wrap {
  white-space: nowrap;
}
</style>