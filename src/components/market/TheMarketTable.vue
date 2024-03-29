<template>
  <div class='p-2' style='background-color: #fafafa'>
    <div class='mb-2 d-flex justify-content-between align-items-center'>
      <span class='font-weight-bold'>套利行情</span>
      <no-border-button @click='showDetail = !showDetail'>
        <input class='align-middle' type='checkbox' :checked='showDetail' />
        <span class='text-muted small ml-1 align-middle'>显示详细信息</span>
      </no-border-button>
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
          <th class='font-weight-normal' nowrap='nowrap' v-if='showDetail'>杠杆支持</th>
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
            {{ toFixed(item['fundingRate'] * 100, 2) }}%
          </td>

          <td
            class='text-monospace'
            v-bind:class="{ positive: item['avgRate'] > 0, negative: item['avgRate'] < 0}"
            nowrap='nowrap'
          >
            {{ toFixed(item['avgRate'] * 100, 2) }}%
          </td>

          <td class='text-monospace' nowrap='nowrap'>
            {{ item['mainPrice'] }}
          </td>

          <td
            class='text-monospace'
            v-bind:class="{ positive: item['premiumRate'] > 0, negative: item['premiumRate'] < 0}"
            nowrap='nowrap'
          >
            {{ toFixed(item['premiumRate'] * 100, 2) }}%
          </td>

          <td
            class='text-monospace'
            nowrap='nowrap'
            v-if='showDetail'
          >
            {{ item['allow'] }}
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import NoBorderButton from '@/components/NoBorderButton.vue'

export default {
  name: 'TheMarketTable',
  components: {
    NoBorderButton
  },
  data: function() {
    return {
      cache: {},    // 将symbol作为键，可以快速查找相应的对象来修改数据
      items: [],    // 排序后的items

      showDetail: false,

      ws: null   // 当前正在连接的websocket
    }
  },
  methods: {

  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    // 获取当前资金费率
    let fundingRate = await this.ws.getDict(['premium', 'fundingRate'])
    console.log('当前资金费率', fundingRate)
    // 根据key来先把object创建好
    for (const symbol of Object.keys(fundingRate)) {
      // 如果symbol以USDT结尾，才允许创建
      if (symbol.endsWith('USDT')) {
        this.items.push({
          symbol: symbol,
          fundingRate: fundingRate[symbol]
        })
      }
    }

    // 对列表排个序
    this.items.sort((a, b) => {
      return Math.abs(b['fundingRate']) - Math.abs(a['fundingRate'])
    })

    // 记录所有symbol的index
    for (let i = 0; i < this.items.length; i++) {
      this.cache[this.items[i]['symbol']] = i
    }

    // 获取历史费率
    let fundingRateHistory = await this.ws.getDict(['premium', 'fundingRateHistory'])
    console.log('历史资金费率', fundingRateHistory)

    for (const symbol of Object.keys(fundingRate)) {
      if (symbol in this.cache) {
        let index = this.cache[symbol]
        // 计算平均费率
        if (fundingRateHistory[symbol] === undefined) {
          this.items[index]['avgRate'] = NaN
        } else if (fundingRateHistory[symbol].length === 0) {
          this.items[index]['avgRate'] = 0
        } else {
          this.items[index]['avgRate'] = this.average(fundingRateHistory[symbol])
        }
      }
    }

    // 获取杠杆支持
    let allowMargin = await this.ws.getDict(['allow', 'margin'])
    let allowIsolated = await this.ws.getDict(['allow', 'isolated'])
    console.log('全仓支持', allowMargin)
    console.log('逐仓支持', allowIsolated)
    for (const symbol of Object.keys(allowMargin)) {
      if (symbol in this.cache) {
        let index = this.cache[symbol]
        this.items[index]['allow'] = '全仓'
      }
    }
    for (const symbol of Object.keys(allowIsolated)) {
      if (symbol in this.cache) {
        let index = this.cache[symbol]
        if (this.items[index]['allow'] === undefined) {
          this.items[index]['allow'] = '逐仓'
        } else {
          this.items[index]['allow'] += ' 逐仓'
        }
      }
    }
    for (const e of this.items) {
      if (e['allow'] === undefined) {
        e['allow'] = '无'
      }
    }


    // 获取现货币价
    let mainPrice = await this.ws.getDict(['price', 'main'])
    console.log('现货币价', mainPrice)
    for (const symbol of Object.keys(mainPrice)) {
      if (symbol in this.cache) {
        let index = this.cache[symbol]
        this.items[index]['mainPrice'] = mainPrice[symbol]
      }
    }

    // 获取期货溢价
    let premiumRate = await this.ws.getDict(['premium', 'rate'])
    console.log('期货溢价', premiumRate)
    for (const symbol of Object.keys(premiumRate)) {
      if (symbol in this.cache) {
        let index = this.cache[symbol]
        this.items[index]['premiumRate'] = premiumRate[symbol]
      }
    }

    // 订阅当前费率
    await this.ws.subscribeDict(['premium', 'fundingRate'], msg => {
      for (const symbol of Object.keys(msg)) {
        if (symbol in this.cache) {
          let index = this.cache[symbol]
          this.items[index]['fundingRate'] = msg[symbol]
        }
      }
    })

    // 订阅历史费率（平均费率）
    await this.ws.subscribeDict(['premium', 'fundingRateHistory'], msg => {
      for (const symbol of Object.keys(msg)) {
        if (symbol in this.cache) {
          let index = this.cache[symbol]
          if (msg[symbol].length === 0) {
            this.items[index]['avgRate'] = 0
          } else {
            this.items[index]['avgRate'] = this.average(fundingRateHistory[symbol])
          }
        }
      }

    })

    // 订阅现货币价
    await this.ws.subscribeDict(['price', 'main'], msg => {
      for (const symbol of Object.keys(msg)) {
        if (symbol in this.cache) {
          let index = this.cache[symbol]
          this.items[index]['mainPrice'] = msg[symbol]
        }
      }

    })

    // 订阅期货溢价
    await this.ws.subscribeDict(['premium', 'rate'], msg => {
      for (const symbol of Object.keys(msg)) {
        if (symbol in this.cache) {
          let index = this.cache[symbol]
          let obj = this.items[index]
          obj['premiumRate'] = msg[symbol]
          this.$set(this.items, index, obj)
        }
      }

    })


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
