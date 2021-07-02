<template>
  <div
    class='p-2 d-flex flex-column'
    style='background-color: #fafafa; min-width: 17rem'
  >
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>BNB资产</span>

      <div class='d-flex'>
        <clickable-icon
          class=''
          name='ri-arrow-left-right-line'
          @click='showTransfer = !showTransfer'
        />
      </div>
    </div>

    <info-item header='现货账户' footer='BNB'>{{ mainBNB }}</info-item>
    <span class='text-muted small align-self-end'>
      ≈ {{ Math.floor(mainBNB * BNBPrice * 100) / 100 }} USDT
    </span>

    <info-item header='期货账户' footer='BNB'>{{ futureBNB }}</info-item>
    <span class='text-muted small align-self-end'>
      ≈ {{ Math.floor(futureBNB * BNBPrice * 100) / 100 }} USDT
    </span>

    <info-item header='全仓账户' footer='BNB'>{{ marginBNB }}</info-item>
    <span class='text-muted small align-self-end'>
      ≈ {{ Math.floor(marginBNB * BNBPrice * 100) / 100 }} USDT
    </span>

    <div v-if='showTransfer'>
      <div class='py-1 d-flex justify-content-between align-items-center'>
        <my-radio @click='fromMode = $event' :active='fromMode' :options="['现货', '期货', '全仓']" />
        <v-icon name='bi-arrow-right'></v-icon>
        <my-radio @click='toMode = $event' :active='toMode' :options="['现货', '期货', '全仓']" />
      </div>
      <div class='d-flex flex-column'>
        <transfer-input
          class=''
          placeholder='转账金额'
          :disabled='disabledTransferButton'
          v-model='transferAmount'
          @click='Transfer'
        >
        </transfer-input>
      </div>
    </div>
  </div>
</template>

<script>
import InfoItem from '@/components/InfoItem.vue'
import RefreshButton from '@/components/RefreshButton.vue'
import TransferInput from '@/components/TransferInput.vue'
import ClickableIcon from '@/components/ClickableIcon.vue'
import NoBorderButton from '@/components/NoBorderButton'
import MyRadio from '@/components/MyRadio.vue'

export default {
  name: 'TheBnbWallet',
  data: function() {
    return {
      mainBNB: '',
      futureBNB: '',
      marginBNB: '',
      BNBPrice: '',

      transferAmount: '',

      fromMode: '现货',
      toMode: '期货',

      showTransfer: false,   // 显示转账输入框

      disabledTransferButton: false,

      ws: null,   // websocket连接对象
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    this.BNBPrice = await this.ws.getPrecise(['price', 'main', 'BNBUSDT'])
    await this.ws.subscribePrecise(['asset', 'main', 'BNB'], msg => {
      this.mainBNB = msg
    }, true)
    await this.ws.subscribePrecise(['asset', 'future', 'BNB'], msg => {
      this.futureBNB = msg
    }, true)
    await this.ws.subscribePrecise(['asset', 'margin', 'BNB'], msg => {
      this.marginBNB = msg
    }, true)
    await this.ws.subscribePrecise(['price', 'main', 'BNBUSDT'], msg => {
      this.BNBPrice = msg
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
          'BNB',
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
    NoBorderButton,
    MyRadio
  }
}
</script>

<style scoped>
</style>