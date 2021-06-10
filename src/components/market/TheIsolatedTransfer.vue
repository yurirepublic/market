<template>
  <card-frame>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>USDT逐仓转账</span>
    </div>

    <div class='d-flex flex-column'>
      <trade-input class='' header='逐仓交易对' v-model='isolatedSymbol' />
      <trade-input class='mt-1' header='资产符号' v-model='isolatedAsset' />

      <div class='d-flex justify-content-end'>
        <my-radio class='mt-1 right' @click='transferMode = $event' :active='transferMode'
                  :options="['转入逐仓', '提到现货']" />
      </div>


      <transfer-input class='mt-1' placeholder='转账金额' v-model='transferAmount' @click='Transfer' />
    </div>


  </card-frame>

</template>

<script>
import CardFrame from '@/components/CardFrame'
import TradeInput from '@/components/TradeInput'
import TransferInput from '@/components/TransferInput'
import MyRadio from '@/components/MyRadio'

export default {
  name: 'TheIsolatedTransfer',
  components: {
    TransferInput,
    TradeInput,
    CardFrame,
    MyRadio
  },
  data: function() {
    return {
      transferMode: '转入逐仓',

      isolatedSymbol: '',
      isolatedAsset: '',
      transferAmount: ''
    }
  },
  methods: {
    Transfer: async function(mode) {
      if (mode === 'confirm') {
        let to = null
        if (this.transferMode === '转入逐仓') {
          to = 'ISOLATED_MARGIN'
        } else if (this.transferMode === '提到现货') {
          to = 'SPOT'
        } else {
          console.error('逐仓转账遇到了未知的转账模式', this.transferAmount)
          return
        }
        await this.apiRequest('isolated_transfer', [this.isolatedAsset, this.isolatedSymbol, to, this.transferAmount]).then(msg => {
          this.showToast.success('转账成功')
        }).catch(err => {
          this.showToast.error('转账失败')
        })
      } else if (mode === 'cancel') {
        this.isolatedSymbol = ''
        this.isolatedAsset = ''
        this.transferAmount = ''

      } else {
        console.error('逐仓转账遇到了未知的转账按钮', mode)
      }
    }
  }

}
</script>

<style scoped>

</style>