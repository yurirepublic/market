<template>
  <div class='p-2' style='background-color: #fafafa'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>套利行情</span>
    </div>
    <div style='overflow: auto; max-height: 15rem'>
      <table class='table table-hover table-borderless table-sm small'>
        <thead>
        <tr class='text-muted'>
          <th class='font-weight-normal' nowrap='nowrap'>交易对</th>
          <th class='font-weight-normal' nowrap='nowrap'>当前费率</th>
          <th class='font-weight-normal' nowrap='nowrap'>平均费率</th>
          <th class='font-weight-normal' nowrap='nowrap'>现货币价(U)</th>
          <th class='font-weight-normal' nowrap='nowrap'>期货溢价</th>
        </tr>
        </thead>
        <tbody>
        <tr
          v-for='item in items'
          :key="item['symbol']"
          @click="$emit('click', item['symbol'])"
        >
          <td class='text-monospace' style='' nowrap='nowrap'>
            {{ item['symbol'] }}
          </td>

          <td
            class='text-monospace'
            v-bind:class="{ positive: item['fundingRate'] > 0, negative: item['fundingRate'] < 0}"
            nowrap='nowrap'
          >
            {{ toPrecision(item['fundingRate'] * 100, 2) }}%
          </td>

          <td
            class='text-monospace'
            v-bind:class="{ positive: item['avgRate'] > 0, negative: item['avgRate'] < 0}"
            nowrap='nowrap'
          >
            {{ toPrecision(item['avgRate'] * 100, 2) }}%
          </td>

          <td class='text-monospace' nowrap='nowrap'>
            {{ item['mainPrice'] }}
          </td>

          <td
            class='text-monospace'
            v-bind:class="{ positive: item['premiumRate'] > 0, negative: item['premiumRate'] < 0}"
            nowrap='nowrap'
          >
            {{ toPrecision(item['premiumRate'] * 100, 2) }}%
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import RefreshButton from '@/components/RefreshButton.vue'

export default {
  name: 'PremiumTable',
  data: function() {
    return {
      cache: {},    // 将symbol作为键，可以快速查找相应的对象来修改数据
      items: [],    // 排序后的items

      dataWs: null,
      subWs: null,   // 当前正在连接的websocket

      sortInterval: null
    }
  },
  methods: {},
  mounted: async function() {
    if (this.sortInterval !== null) {
      clearInterval(this.sortInterval)
    }
    this.cache = {}
    this.items = []

    this.dataWs = await this.connectDataCenter()
    // 获取当前资金费率
    let fundingRate = await this.dataWs.getDict(['premium', 'fundingRate'])
    console.log('当前资金费率', fundingRate)
    // 以同步方式根据key来先把object创建好
    let keys = Object.keys(fundingRate)
    for (let i = 0; i < keys.length; i++) {
      let symbol = keys[i]
      // 如果symbol以USDT结尾，才允许创建
      if (symbol.endsWith('USDT')) {
        let obj = {
          symbol: symbol,
          fundingRate: fundingRate[symbol]
        }
        this.cache[symbol] = obj
        this.items.push(obj)
      }
    }
    this.$forceUpdate()

    // 获取历史费率
    let fundingRateHistory = await this.dataWs.getDict(['premium', 'fundingRateHistory'])
    console.log('历史资金费率', fundingRateHistory)
    Object.keys(fundingRateHistory).forEach(symbol => {
      let obj = this.cache[symbol]
      if (obj) {
        obj['fundingRateHistory'] = fundingRateHistory[symbol]
        // 计算平均费率
        let total = 0
        if (fundingRateHistory[symbol].length === 0) {
          obj['avgRate'] = 0
        } else {
          obj['avgRate'] = this.average(fundingRateHistory[symbol])
        }
        this.$forceUpdate()
      }
    })

    // 获取现货币价
    let mainPrice = await this.dataWs.getDict(['price', 'main'])
    console.log('现货币价', mainPrice)
    Object.keys(mainPrice).forEach(symbol => {
      let obj = this.cache[symbol]
      if (obj) {
        obj['mainPrice'] = mainPrice[symbol]
        this.$forceUpdate()
      }
    })

    // 获取期货溢价
    let premiumRate = await this.dataWs.getDict(['premium', 'rate'])
    console.log('期货溢价', premiumRate)
    Object.keys(premiumRate).forEach(symbol => {
      let obj = this.cache[symbol]
      if (obj) {
        obj['premiumRate'] = premiumRate[symbol]
        this.$forceUpdate()
      }
    })

    // 打开订阅连接
    this.subWs = await this.connectSubscribe()

    // 订阅当前费率
    await this.subWs.dict(['premium', 'fundingRate'], msg => {
      let symbol = msg['special']
      let obj = this.cache[symbol]
      if (obj) {
        obj['fundingRate'] = msg['data']
        this.$forceUpdate()
      }
    })

    // 订阅历史费率（平均费率）
    await this.subWs.dict(['premium', 'fundingRateHistory'], msg => {
      let symbol = msg['special']
      let obj = this.cache[symbol]
      if (obj) {
        obj['fundingRateHistory'] = msg['data']
        // 计算平均费率
        if (msg['data'].length === 0) {
          obj['avgRate'] = 0
        } else {
          obj['avgRate'] = this.average(msg['data'])
        }
        this.$forceUpdate()
      }
    })

    // 订阅现货币价
    await this.subWs.dict(['price', 'main'], msg => {
      let symbol = msg['special']
      let obj = this.cache[symbol]
      if (obj) {
        obj['mainPrice'] = msg['data']
        this.$forceUpdate()
      }
    })

    // 订阅期货溢价
    await this.subWs.dict(['premium', 'rate'], msg => {
      let symbol = msg['special']
      let obj = this.cache[symbol]
      if (obj) {
        obj['premiumRate'] = msg['data']
        this.$forceUpdate()
      }
    })

    // 每3s对列表排个序
    this.sortInterval = setInterval(() => {
      this.items.sort((a, b) => {
        return Math.abs(b['fundingRate']) - Math.abs(a['fundingRate'])
      })
    }, 3000)

  },
  components: {
    RefreshButton
  }
}
</script>

<style scoped>
.positive {
  color: #02c076
}

.negative {
  color: #f84960
}
</style>
