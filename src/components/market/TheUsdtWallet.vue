<template>
  <div
    class='p-2 d-flex flex-column'
    style='background-color: #fafafa; min-width: 17rem'
  >
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>USDT资产</span>
      <div class='d-flex'>
        <ClickableIcon
          class=''
          name='ri-arrow-left-right-line'
          @click='showTransfer = !showTransfer'
        />
      </div>
    </div>

    <InfoItem header='可用现货' footer='USDT'>{{ mainFree }}</InfoItem>
    <InfoItem header='可用期货' footer='USDT'>{{ futureFree }}</InfoItem>
    <span class='text-muted small align-self-end'>
      可转出期货 {{ futureWithdrawAble }}
    </span>
    <InfoItem header='可用全仓' footer='USDT'>{{ marginFree }}</InfoItem>
    <div v-if='showTransfer'>
      <div class='py-1 d-flex justify-content-between align-items-center'>
        <Radio @click='fromMode = $event' :active='fromMode' :options="['现货', '期货', '全仓']"></Radio>
        <v-icon name='bi-arrow-right'></v-icon>
        <Radio @click='toMode = $event' v-bind:active='toMode' :options="['现货', '期货', '全仓']"></Radio>
      </div>
      <div class='d-flex flex-column'>
        <TransferInput
          class=''
          placeholder='转账金额'
          :disabled='disabledTransferButton'
          v-model='transferAmount'
          @click='Transfer'
        >
        </TransferInput>
      </div>
    </div>
  </div>
</template>

<script>
import InfoItem from '@/components/InfoItem.vue'
import RefreshButton from '@/components/RefreshButton.vue'
import TransferInput from '@/components/TransferInput.vue'
import ClickableIcon from '@/components/ClickableIcon.vue'
import Radio from '@/components/MyRadio.vue'

export default {
  name: 'TheUsdtWallet',
  data: function() {
    return {
      mainFree: NaN,
      futureFree: NaN,
      futureWithdrawAble: NaN,
      marginFree: NaN,

      disabledTransferButton: false,

      transferAmount: '',

      fromMode: '现货',
      toMode: '期货',

      showTransfer: false,

      ws: null,
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    // 订阅资产变动
    await this.ws.subscribePrecise(['asset', 'main', 'USDT'], msg => {
      this.mainFree = msg
    }, true)
    await this.ws.subscribePrecise(['asset', 'future', 'USDT'], msg => {
      this.futureFree = msg
    }, true)
    await this.ws.subscribePrecise(['asset', 'future', 'USDT_WITHDRAW_ABLE'], msg => {
      this.futureWithdrawAble = msg
    })
    await this.ws.subscribePrecise(['asset', 'margin', 'USDT'], msg => {
      this.marginFree = msg
    }, true)
  },
  methods: {
    // 转账操作
    Transfer: async function(mode) {
      if (mode === 'cancel') {
        this.showTransfer = false
        return
      }
      if (this.fromMode === this.toMode) {
        this.showToast.warning('不能自己转给自己')
        return
      }
      this.disabledTransferButton = true
      // 生成转账模式
      let transferMode = ''
      switch (this.fromMode) {
        case '现货':
          transferMode += 'MAIN'
          break
        case '全仓':
          transferMode += 'MARGIN'
          break
        case '期货':
          transferMode += 'UMFUTURE'
      }
      transferMode += '_'
      switch (this.toMode) {
        case '现货':
          transferMode += 'MAIN'
          break
        case '全仓':
          transferMode += 'MARGIN'
          break
        case '期货':
          transferMode += 'UMFUTURE'
      }
      this.showToast.info('开始转账')
      try {
        await this.apiRequest('transfer', [
          transferMode,
          'USDT',
          this.transferAmount
        ])
        this.showToast.success('转账成功')
        // 转账成功了清空一下输入
        this.transferAmount = ''
      } catch (err) {
        this.showToast.error('转账失败')
      } finally {
        this.disabledTransferButton = false
      }
    }
  },
  components: {
    InfoItem,
    RefreshButton,
    TransferInput,
    ClickableIcon,
    Radio
  }
}
</script>

<style scoped>
</style>