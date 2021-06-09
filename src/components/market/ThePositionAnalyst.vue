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
        <no-border-button @click='showDetail = !showDetail'>
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
        <!--        <th class='font-weight-normal'>逐仓风险</th>-->
        <th class='font-weight-normal'>期货</th>
        <th class='font-weight-normal'>净持</th>
        <th class='font-weight-normal'>双持</th>
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
        <!--        <td class='text-monospace align-middle'>-->
        <!--          <span v-if="item['isolatedRisk'] !== 99999">{{ toFixed(item['isolatedRisk'], 2) }}%</span>-->
        <!--        </td>-->
        <td class='text-monospace align-middle'>
          <span v-if="item['future'] !== 0">{{ strip(item['future']) }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['net'] !== 0">{{ strip(item['net']) }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['hedging'] !== 0">{{ strip(item['hedging']) }}</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['value'] !== 0">{{ toFixed(item['value'], 2) }}＄</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['fundingRate'] !== 0">{{ toFixed(item['fundingRate'] * 100, 2) }}%</span>
        </td>
        <td class='text-monospace align-middle' v-if='showDetail'>
          <span v-if="item['fundingRate'] !== 0">{{ toFixed(item['premiumRate'] * 100, 2) }}%</span>
        </td>
      </tr>
      </tbody>
    </table>
    <div class='d-flex justify-content-between'>
      <span class=''>全仓风险 {{ toFixed(marginRisk, 2) }}%</span>
<!--      <span class='' v-if='marginWarning !== 99999'>0.8倍杠杆警告 {{ toFixed(marginWarning, 2) }}%</span>-->
<!--      <span class='' v-if='marginWarning === 99999'>0.8倍杠杆警告 安全</span>-->

    </div>
    <div class='d-flex justify-content-between'>
      <span class=''>期货风险 {{ toFixed(futureRisk * 100, 2) }}%</span>
      <span class='' v-if='futureWarning !== 99999'>
        5倍杠杆警告 {{ futureWarning > 0 ? '+' : '' }}{{ toFixed(futureWarning * 100, 2) }}%
      </span>
      <span class='' v-if='futureWarning === 99999'>5倍杠杆警告 安全</span>
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

      marginRisk: '',
      marginWarning: '',
      futureRisk: '',
      futureWarning: '',

      updateInterval: null,

      button_disabled: false,

      showBnb: false,
      showDetail: false,

      ws: null,
      subscribe: null
    }

  },
  methods: {},
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()
    if (this.updateInterval !== null) {
      clearInterval(this.updateInterval)
    }

    // 获取及订阅资产变化
    const assetChangeHandle = async (data) => {
      // 对交易对排序
      data.sort((a, b) => {
        if (a.value < b.value) {
          return 1
        } else if (a.value > b.value) {
          return -1
        } else {
          if (Math.abs(a.net) < Math.abs(b.net)) {
            return 1
          } else if (Math.abs(a.net) > Math.abs(b.net)) {
            return -1
          } else {
            return 0
          }
        }
      })
      this.items = data
    }
    await assetChangeHandle(await this.ws.getData(['json', 'position']))
    await this.subscribe.precise(['json', 'position'], async msg => {
      await assetChangeHandle(msg['data'])
    })


    // // 定时刷新费率、溢价和风险率
    // this.updateInterval = setInterval(async () => {
    //   // 逐条更新费率和溢价
    //   const updateHandle = async (item) => {
    //     item['fundingRate'] = await this.ws.getData(['premium', 'fundingRate', item['symbol'] + 'USDT'])
    //     item['premiumRate'] = await this.ws.getData(['premium', 'rate', item['symbol'] + 'USDT'])
    //   }
    //   this.items.forEach(e => {
    //     updateHandle(e)
    //   })
    // }, 1000)

    // 订阅风险率信息
    await this.subscribe.precise(['risk', 'future', 'usage'], async (msg) =>{
      this.futureRisk = msg['data']
    })
    await this.subscribe.precise(['risk', 'future', 'warning'], async (msg) => {
      this.futureWarning = msg['data']
    })
    await this.subscribe.precise(['risk', 'margin', 'usage'], async (msg) => {
      this.marginRisk = msg['data']
    })
    // await this.subscribe.precise(['risk', 'margin', 'warning'], async (msg) => {
    //   this.marginWarning = msg['data']
    // })





  },
  components: {
    NoBorderButton
  }
}
</script>

<style scoped>

</style>