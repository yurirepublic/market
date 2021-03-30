<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">套利行情</span>
      <!--      <RefreshButton :anime="refresh_button_anime" @click="refresh"/>-->
    </div>
    <div style="overflow: auto; max-height: 15rem">
      <table class="table table-hover table-borderless table-sm small">
        <thead>
        <tr class="text-muted">
          <th class="font-weight-normal" nowrap="nowrap">交易对</th>
          <th class="font-weight-normal" nowrap="nowrap">当前费率</th>
          <th class="font-weight-normal" nowrap="nowrap">平均费率</th>
          <th class="font-weight-normal" nowrap="nowrap">现货币价(U)</th>
          <th class="font-weight-normal" nowrap="nowrap">期货溢价</th>
        </tr>
        </thead>
        <tbody>
        <tr
            v-for="item in items"
            :key="item['symbol']"
            @click="$emit('click', item)"
        >
          <td class="text-monospace" style="" nowrap="nowrap">
            {{ item['symbol'] }}
          </td>

          <td
              class="text-monospace"
              style="color: #02c076"
              v-if="item['fundingRate'] > 0"
              nowrap="nowrap"
          >
            {{ item["fundingRate"] }}%
          </td>
          <td
              class="text-monospace"
              style="color: #f84960"
              v-if="item['fundingRate'] < 0"
              nowrap="nowrap"
          >
            {{ item["fundingRate"] }}%
          </td>
          <td
              class="text-monospace"
              v-if="item['fundingRate'] === 0"
              nowrap="nowrap"
          >
            {{ item["fundingRate"] }}%
          </td>

          <td
              class="text-monospace"
              style="color: #02c076"
              v-if="item['avgRate'] > 0"
              nowrap="nowrap"
          >
            {{ item["avgRate"] }}%
          </td>
          <td
              class="text-monospace"
              style="color: #f84960"
              v-if="item['avgRate'] < 0"
              nowrap="nowrap"
          >
            {{ item["avgRate"] }}%
          </td>
          <td
              class="text-monospace"
              v-if="item['avgRate'] === 0"
              nowrap="nowrap"
          >
            {{ item["avgRate"] }}%
          </td>

          <td class="text-monospace" nowrap="nowrap">
            {{ item["mainPrice"] }}
          </td>

          <td
              class="text-monospace"
              style="color: #02c076"
              v-if="item['premiumRate'] > 0"
              nowrap="nowrap"
          >
            {{ item["premiumRate"] }}%
          </td>
          <td
              class="text-monospace"
              style="color: #f84960"
              v-if="item['premiumRate'] < 0"
              nowrap="nowrap"
          >
            {{ item["premiumRate"] }}%
          </td>
          <td
              class="text-monospace"
              v-if="item['premiumRate'] === 0"
              nowrap="nowrap"
          >
            {{ item["premiumRate"] }}%
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import RefreshButton from "@/components/RefreshButton.vue";

export default {
  name: "PremiumTable",
  data: function () {
    return {
      cache: {},    // 将symbol作为键，可以快速查找相应的对象来修改数据
      items: [],    // 排序后的items
      refresh_button_anime: false,
      dataWs: null,
      subWs: null,   // 当前正在连接的websocket
    };
  },
  methods: {},
  mounted: async function () {
    if (this.dataWs !== null) {
      this.dataWs.close()
    }
    if (this.subWs !== null) {
      this.subWs.close()
    }
    this.dataWs = await this.connectDataCenter('行情表单')
    // 获取当前资金费率
    let fundingRate = await this.dataWs.getDict(['premium', 'fundingRate'])
    console.log('当前资金费率', fundingRate)
    // 以同步方式根据key来先把object创建好
    let keys = Object.keys(fundingRate)
    for (let i = 0; i < keys.length; i++) {
      let obj = {
        symbol: keys[i]
      }
      this.cache[keys[i]] = obj
      this.items.push(obj)
    }

    Object.keys(fundingRate).forEach(symbol => {
      let obj = this.cache[symbol]
      obj['fundingRate'] = this.toPrecision(fundingRate[symbol] * 100, 2)
      this.$forceUpdate()
    })

    // 获取历史费率
    let fundingRateHistory = await this.dataWs.getDict(['premium', 'fundingRateHistory'])
    console.log('历史资金费率', fundingRateHistory)
    Object.keys(fundingRateHistory).forEach(symbol => {
      let obj = this.cache[symbol]
      obj['fundingRateHistory'] = fundingRateHistory[symbol]
      // 计算平均费率
      let total = 0
      for (let i = 0; i < fundingRateHistory[symbol].length; i++) {
        total += fundingRateHistory[symbol][i]
      }
      if (fundingRateHistory[symbol].length === 0) {
        obj['avgRate'] = 0
      } else {
        obj['avgRate'] = this.toPrecision((total / fundingRateHistory[symbol].length) * 100, 2)
      }
      this.$forceUpdate()
    })

    // 获取现货币价
    let mainPrice = await this.dataWs.getDict(['price', 'main'])
    console.log('现货币价', mainPrice)
    Object.keys(mainPrice).forEach(symbol => {
      let obj = this.cache[symbol]
      try {
        obj['mainPrice'] = mainPrice[symbol]
      } catch (err) {
        // 遇到多出的符号是正常的
        if (err instanceof TypeError) {
          return
        }
        throw err
      }
      this.$forceUpdate()
    })

    // 获取期货溢价
    let premiumRate = await this.dataWs.getDict(['premium', 'rate'])
    console.log('期货溢价', premiumRate)
    Object.keys(premiumRate).forEach(symbol => {
      let obj = this.cache[symbol]
      try {
        obj['premiumRate'] = this.toPrecision(premiumRate[symbol] * 100, 2)
      } catch (err) {
        if (err instanceof TypeError) {
          return
        }
        throw err
      }
      this.$forceUpdate()
    })

    // 获取




    // // 打开新连接
    // this.connectDataCenter('溢价表单').then(res => {
    //   if (this.dataWs !== null) {
    //     this.dataWs.close(1000)
    //   }
    //   this.dataWs = res
    //   // 获取基础数据
    //   this.dataWs.onmessage = msg => {
    //     msg = JSON.parse(msg.data)['data']
    //     Object.keys(msg).forEach(key => {
    //       this.items[key] = {
    //         rate: msg[key]
    //       }
    //       this.items = this.items
    //     })
    //
    //   }
    //   this.dataWs.send(JSON.stringify({
    //     mode: 'GET_DICT',
    //     tags: ['premium', 'rate']
    //   }))
    // })
    // this.connectSubscribe('溢价表单订阅').then(res => {
    //   this.subWs = res
    //   if (this.subWs !== null) {
    //     this.subWs.close(1000)
    //   }
    //   this.subWs.onmessage = msg => {
    //     let data = JSON.parse(msg.data)
    //     let tags = data['tags']
    //     let special = data['special']
    //     data = Math.round(data.data * 10000) / 100
    //     if (tags.includes('premium') && tags.includes('rate')) {
    //       // 查找表格项目有没有对应的symbol
    //       for (let i = 0; i < this.items.length; i++) {
    //         let e = this.items[i]
    //         if (e.symbol === special) {
    //           this.items[i].future_premium = data
    //         }
    //       }
    //       this.items = this.items
    //     }
    //   }
    // })
    //

  },
  components: {
    RefreshButton,
  },
};
</script>

<style scoped>
</style>
