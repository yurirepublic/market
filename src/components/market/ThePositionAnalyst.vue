<template>
  <div
    class='p-2 d-flex flex-column flex-column'
    style='
      overflow: auto;
      max-height: 40rem;
      background-color: #fafafa;
    '
  >
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>USDT交易对持仓</span>
      <div class='d-flex'>
        <no-border-button @click='forceRefreshPosition'>
          <span class='small'>强制刷新仓位</span>
        </no-border-button>
        <no-border-button class='ml-1' @click='showDetail = !showDetail'>
          <input class='align-middle' type='checkbox' :checked='showDetail' />
          <span class='text-muted small ml-1 align-middle'>显示详细信息</span>
        </no-border-button>
        <no-border-button class='ml-1' @click='showBnb = !showBnb'>
          <input class='align-middle' type='checkbox' :checked='showBnb' />
          <span class='text-muted small ml-1 align-middle'>显示BNB</span>
        </no-border-button>
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
        <th class='font-weight-normal'>贷款占比</th>
        <th class='font-weight-normal'>期货</th>
        <th class='font-weight-normal' v-if='showDetail'>净持</th>
        <th class='font-weight-normal' v-if='showDetail'>双持</th>
        <th class='font-weight-normal' v-if='showDetail'>市值</th>
        <th class='font-weight-normal' v-if='showDetail'>费率</th>
        <th class='font-weight-normal' v-if='showDetail'>溢价</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for='(item, index) in items'
          v-if="!((item['symbol'] === 'BNB' && !showBnb) || item['symbol'] === 'USDT' || item['show'] === false)"
          :key="item['symbol']"
          @click="$emit('click', item['symbol'] + 'USDT')"
      >
        <td class='text-monospace align-middle'>
          <span>{{ item['symbol'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['main'] !== 0">{{ strip(item['main']) }}</span>

        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['margin'] !== 0">{{ strip(item['margin']) }}</span>
          <span v-if="item['marginBorrowed'] !== 0">{{ strip(-item['marginBorrowed']) }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['isolated'] !== 0">{{ item['isolated'] }}</span>
          <span v-if="item['isolatedBorrowed'] !== 0">{{ strip(-item['isolatedBorrowed']) }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['isolatedQuote'] !== 0">{{ strip(item['isolatedQuote']) }}</span>
          <span v-if="item['isolatedQuoteBorrowed'] !== 0">{{ strip(-item['isolatedQuoteBorrowed']) }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['isolatedRisk'] !== 0">{{ toFixed(item['isolatedRisk'] * 100, 2) }}%</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['future'] !== 0">{{ strip(item['future']) }}</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['net'] !== 0">{{ strip(item['net']) }}</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['hedging'] !== 0">{{ strip(item['hedging']) }}</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['value'] !== 0">{{ toFixed(item['value'], 2) }}＄</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['fundingRate'] !== 0">{{ toFixed(item['fundingRate'] * 100, 2) }}%</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['premiumRate'] !== 0">{{ toFixed(item['premiumRate'] * 100, 2) }}%</span>
        </td>
      </tr>
      </tbody>
    </table>
    <div class='d-flex justify-content-between'>
      <span class=''>全仓风险 {{ toFixed(marginRisk * 100, 2) }}%</span>
    </div>
    <div class='d-flex justify-content-between'>
      <span class=''>期货风险 {{ toFixed(futureRisk * 100, 2) }}%</span>
    </div>

  </div>
</template>

<script>
import NoBorderButton from '@/components/NoBorderButton.vue'

export default {
  name: 'ThePositionAnalyst',
  data: function() {
    return {
      items: [],    // 存储每个持仓情况的object
      cache: {},    // 依据symbol来索引的items

      marginRisk: '',
      futureRisk: '',

      updateInterval: null,

      button_disabled: false,

      showBnb: false,
      showDetail: false,

      ws: null,
    }

  },
  methods: {
    initItem: function(symbol) {
      let data = {
        symbol: symbol,
        main: 0,
        margin: 0,
        marginBorrowed: 0,
        isolated: 0,
        isolatedBorrowed: 0,
        isolatedQuote: 0,
        isolatedQuoteBorrowed: 0,
        isolatedRisk: 0,
        future: 0,
        net: 0,
        hedging: 0,
        value: 0,
        fundingRate: 0,
        premiumRate: 0
      }
      this.items.push(data)
      this.cache[symbol] = data
    },
    setItem: function(symbol, property, data) {
      if (this.cache[symbol] === undefined) {
        this.initItem(symbol)
      }
      this.cache[symbol][property] = data
    },
    forceRefreshPosition: function() {
      this.apiRequest('force_refresh_position', []).then(res => {
        this.showToast.success('成功提交刷新请求')
      }).catch(err => {
        this.showToast.error('提交刷新请求失败')
      })
    }

  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    // 订阅仓位数据
    await this.ws.subscribePrecise(['json', 'position'], msg => {
      console.log('持仓信息更新')
      this.items = msg
      this.cache = {}
      for (const e of this.items) {
        this.cache[e['symbol']] = e
      }
    }, true)


    // 订阅资金费率
    await this.ws.subscribeDict(['premium', 'fundingRate'], msg => {
      for (const symbol of Object.keys(msg)) {
        // 确保要是USDT交易对的费率
        if (symbol.endsWith('USDT')) {
          let asset = symbol.substring(0, symbol.length - 4)
          if (this.cache[asset] !== undefined) {
            this.setItem(asset, 'fundingRate', msg[symbol])
          }
        }
      }
    }, true)

    // 订阅期货溢价
    await this.ws.subscribeDict(['premium', 'rate'], msg => {
      for (const symbol of Object.keys(msg)) {
        // 确保要是USDT交易对的费率
        if (symbol.endsWith('USDT')) {
          let asset = symbol.substring(0, symbol.length - 4)
          if (this.cache[asset] !== undefined) {
            this.setItem(asset, 'premiumRate', msg[symbol])
          }
        }
      }
    }, true)

    // 订阅期货风险
    await this.ws.subscribePrecise(['risk', 'future', 'usage'], msg => {
      this.futureRisk = msg
    })
  },
  components: {
    NoBorderButton
  }
}
</script>

<style scoped>

</style>