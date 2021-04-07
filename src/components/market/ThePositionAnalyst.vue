<template>
  <div
    class='p-2 d-flex flex-column flex-column'
    style='
      overflow: auto;
      max-height: 40rem;
      min-width: 17rem;
      background-color: #fafafa;
    '
  >
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>USDT交易对持仓</span>
      <div class='d-flex'>
        <no-border-button @click='show_detail = !show_detail'>
          <input class='align-middle' type='checkbox' :checked='show_detail' />
          <span class='text-muted small ml-1 align-middle'>显示详细信息</span>
        </no-border-button>
        <no-border-button @click='show_bnb = !show_bnb'>
          <input class='align-middle' type='checkbox' :checked='show_bnb' />
          <span class='text-muted small ml-1 align-middle'>显示BNB</span>
        </no-border-button>
        <RefreshButton :anime='refresh_button_anime' @click='refresh' />
      </div>
    </div>
    <table class='table table-hover table-borderless table-sm small'>
      <thead>
      <tr class='text-muted'>
        <th class='font-weight-normal'>资产</th>
        <th class='font-weight-normal'>现货</th>
        <th class='font-weight-normal'>全仓/借贷</th>
        <th class='font-weight-normal'>逐仓/借贷</th>
        <th class='font-weight-normal'>逐仓U/借贷</th>
        <th class='font-weight-normal'>逐仓风险</th>
        <th class='font-weight-normal'>期货</th>
        <th class='font-weight-normal'>净持</th>
        <th class='font-weight-normal'>双持</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for='(value, key) in havingItems'
          v-if="!(key=='BNB' && !show_bnb)"
          :key='key'
          @click="$emit('click', key + 'USDT')"
      >
        <td class='text-monospace align-middle'>
          <span>{{ key }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['main'] != 0">{{ value['main'] }}</span>

        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['margin'] != 0">{{ value['margin'] }}</span>
          <span v-if="value['margin_borrowed'] != 0">{{ -value['margin_borrowed'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['isolated'] != 0">{{ value['isolated'] }}</span>
          <span v-if="value['isolated_borrowed'] != 0">{{ -value['isolated_borrowed'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['isolated_quote'] != 0">{{ value['isolated_quote'] }}</span>
          <span v-if="value['isolated_quote_borrowed'] != 0">{{ -value['isolated_quote_borrowed'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['isolated_risk'] != 0">{{ value['isolated_risk'] }}%</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['future'] != 0">{{ value['future'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['net'] != 0">{{ value['net'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="value['hedging'] != 0">{{ value['hedging'] }}</span>
        </td>
      </tr>
      </tbody>
    </table>
    <div class='d-flex justify-content-between'>
      <span class='font-weight-bold'>全仓风险 {{ margin_risk }}%</span>
      <span class='font-weight-bold' v-if='margin_warning != 99999'>0.8倍杠杆警告 {{ margin_warning }}%</span>
      <span class='font-weight-bold' v-if='margin_warning == 99999'>0.8倍杠杆警告 安全</span>

    </div>
    <div class='d-flex justify-content-between'>
      <span class='font-weight-bold'>期货风险 {{ future_risk }}%</span>
      <span class='font-weight-bold'
            v-if='future_warning != 99999'>5倍杠杆警告 {{ future_warning > 0 ? '+' : '' }}{{ future_warning }}%</span>
      <span class='font-weight-bold' v-if='future_warning == 99999'>5倍杠杆警告 安全</span>
    </div>

  </div>
</template>

<script>
import RefreshButton from '@/components/RefreshButton.vue'
import NoBorderButton from '@/components/NoBorderButton'

export default {
  name: 'PremiumHaving',
  data: function() {
    return {
      havingItems: {},
      havingItemsSingle: {},
      refresh_button_anime: false,

      margin_risk: '',
      future_risk: '',
      future_warning: '',
      margin_warning: '',

      button_disabled: false,

      show_bnb: false,
      show_detail: false
    }

  },
  mounted: function() {
    this.refresh()
  },

  methods: {
    // 刷新持仓
    refresh() {
      this.refresh_button_anime = true

      // 获取套利开仓情况
      this.method_request('analyze_premium', [])
        .then((res) => {
          this.havingItems = res['data']['USDT']
          this.margin_risk = res['data']['margin_risk']
          this.future_risk = res['data']['future_risk']
          this.future_warning = res['data']['future_warning']
          this.margin_warning = res['data']['margin_warning']
          // this.havingItemsSingle = res["data"]["single"];

          this.$toast.open({
            message: '套利开仓情况获取成功',
            type: 'success'
          })
        })
        .catch((err) => {
          this.$toast.open({
            message: '套利开仓情况获取失败',
            type: 'error'
          })
        })
        .finally(() => {
          this.refresh_button_anime = false
        })
    },

    // 平仓
    CloseOut(item) {
      console.log('即将平仓双向交易对', item)
      this.button_disabled = true
      // 平仓下单
      console.log('平仓下单符号', item['symbol'])
      console.log('平仓下单数量', item['quantity'])
      this.showToast.info('开始平仓' + item['symbol'])
      this.method_request('trade_premium', [item['symbol'], item['quantity'], 'MAIN'])
        .then((res) => {
          this.showToast.success(item['symbol'] + '成功平仓')
        })
        .catch((err) => {
          this.showToast.error('平仓失败')
        })
        .finally(() => {
          this.button_disabled = false
        })
    },

    // 平孤立仓
    CloseSingle(item) {
      this.button_disabled = true
      console.log('即将平孤立仓', item['symbol'])
      console.log('平仓下单数量', item['quantity'])
      console.log('平仓区域', item['type'])

      // 特别对待一下期货的负仓位情况
      if (item['type'] === 'FUTURE' && item['quantity'] < 0) {
        // 将仓位的负号消除，方向使用BUY
        this.method_request('trade_market', [item['symbol'], item['type'], item['quantity'].replace('-', ''), 'BUY']).then(res => {
          this.showToast.success(item['symbol'] + '成功平仓')
        }).catch(err => {
          this.showToast.success(item['symbol'] + '平仓失败')
        }).finally(() => {
          this.button_disabled = false
        })
      } else {
        // 将仓位的负号消除，方向使用BUY
        this.method_request('trade_market', [item['symbol'], item['type'], item['quantity'], 'SELL']).then(res => {
          this.showToast.success(item['symbol'] + '成功平仓')
        }).catch(err => {
          this.showToast.success(item['symbol'] + '平仓失败')
        }).finally(() => {
          this.button_disabled = false
        })
      }
    }
  },

  components: {
    RefreshButton,
    NoBorderButton
  }
}
</script>

<style scoped>

</style>