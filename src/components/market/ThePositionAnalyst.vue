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
        <th class='font-weight-normal'>逐仓风险</th>
        <th class='font-weight-normal'>期货</th>
        <th class='font-weight-normal'>净持</th>
        <th class='font-weight-normal'>双持</th>
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
          <span v-if="item['main'] !== 0">{{ item['main'] }}</span>

        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['margin'] !== 0">{{ item['margin'] }}</span>
          <span v-if="item['marginBorrowed'] !== 0">{{ -item['marginBorrowed'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['isolated'] !== 0">{{ item['isolated'] }}</span>
          <span v-if="item['isolatedBorrowed'] !== 0">{{ -item['isolatedBorrowed'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['isolatedQuote'] !== 0">{{ item['isolatedQuote'] }}</span>
          <span v-if="item['isolatedQuoteBorrowed'] !== 0">{{ -item['isolatedQuoteBorrowed'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['isolatedRisk'] !== 99999">{{ toPrecision(item['isolatedRisk'], 2) }}%</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['future'] !== 0">{{ item['future'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['net'] !== 0">{{ item['net'] }}</span>
        </td>
        <td class='text-monospace align-middle'>
          <span v-if="item['hedging'] !== 0">{{ item['hedging'] }}</span>
        </td>
      </tr>
      </tbody>
    </table>
    <div class='d-flex justify-content-between'>
      <span class='font-weight-bold'>全仓风险 {{ toPrecision(marginRisk, 2) }}%</span>
      <span class='font-weight-bold' v-if='marginWarning !== 99999'>0.8倍杠杆警告 {{ toPrecision(marginWarning, 2) }}%</span>
      <span class='font-weight-bold' v-if='marginWarning === 99999'>0.8倍杠杆警告 安全</span>

    </div>
    <div class='d-flex justify-content-between'>
      <span class='font-weight-bold'>期货风险 {{ toPrecision(futureRisk, 2) }}%</span>
      <span class='font-weight-bold'
            v-if='futureWarning !== 99999'>5倍杠杆警告 {{ futureWarning > 0 ? '+' : '' }}{{ toPrecision(futureWarning, 2)
        }}%</span>
      <span class='font-weight-bold' v-if='futureWarning === 99999'>5倍杠杆警告 安全</span>
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
      cache: {},    // 快速索引持仓的object以避免遍历列表

      mainPrice: {},    // 市值计算需要用到现货价格，这里会订阅所有的现货价格
      futurePrice: {},    // 市值计算需要用到的期货价格

      havingItems: {},
      havingItemsSingle: {},
      refresh_button_anime: false,

      marginRisk: '',
      marginWarning: '',
      futureRisk: '',
      futureWarning: '',


      riskCalcInterval: null,   // 定期计算风险的定时器

      button_disabled: false,

      showBnb: false,
      showDetail: false,

      ws: null,
      subscribe: null
    }

  },
  methods: {
    createDefaultItem: function() {
      return {
        symbol: '',   // 货币符号

        main: 0,  // 现货余额
        margin: 0,  // 全仓余额
        marginBorrowed: 0,  // 全仓借入
        isolated: 0,  // 逐仓余额
        isolatedBorrowed: 0,  // 逐仓借入
        isolatedQuote: 0, // 逐仓合约币（一般是USDT）余额
        isolatedQuoteBorrowed: 0, // 逐仓合约币借入
        isolatedRisk: 99999,    // 逐仓风险率
        future: 0,  // 期货余额
        net: 0,   // 净持仓
        hedging: 0,   // 双向持仓

        value: 0,    // 双向持仓的单边市值

        show: false // 经过判断后认为此项可以显示的标识
      }
    },
    // 修改一个持仓item，会优先根据cache判断是否存在，不存在会自动创建
    setItem: async function(symbol, key, value) {
      let obj = this.cache[symbol]
      if (obj !== undefined) {
        if (obj[key] === value) {
          return    // 一样的数字没必要改
        }
        obj[key] = value
        // 计算净持和双持
        let positive = 0
        let negative = 0
        positive += obj['main']
        if (obj['future'] > 0) {
          positive += obj['future']
        } else {
          negative += -obj['future']
        }
        positive += obj['margin']
        positive += obj['isolated']

        negative += obj['marginBorrowed']
        negative += obj['isolatedBorrowed']

        obj['net'] = positive - negative
        obj['hedging'] = Math.min(positive, negative)

        // 判断是否可以显示
        obj['show'] = this.checkShow(obj)

        if (obj['show']) {
          // 计算逐仓波动风险
          let assetValue = 0
          let borrowedValue = 0
          let price = this.mainPrice[obj.symbol + 'USDT']
          assetValue += obj.isolated * price
          assetValue += obj.isolatedQuote
          borrowedValue += obj.isolatedBorrowed * price
          borrowedValue += obj.isolatedQuoteBorrowed
          if (borrowedValue - 0.8 * assetValue === 0) {
            obj.isolatedRisk = 99999
          } else {
            obj.isolatedRisk = ((0.8 * assetValue - borrowedValue) / (borrowedValue - 0.8 * assetValue)) * 100
          }
        }


      } else {
        obj = this.createDefaultItem()
        obj['symbol'] = symbol
        obj[key] = value
        obj.show = this.checkShow(obj)
        this.cache[symbol] = obj
        this.items.push(obj)
      }
      this.$forceUpdate()
    },
    checkShow: function(item) {
      // 判断一个item能不能被展示出来。只要有一个数字不是0，都可以被展示
      let keys = Object.keys(item)
      let show = false
      keys.forEach(e => {
        if (e !== 'symbol' && e !== 'show' && e !== 'isolatedRisk' && item[e] !== 0) {
          show = true
        }
      })
      return show
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()
    if (this.riskCalcInterval !== null) {
      clearInterval(this.riskCalcInterval)
    }
    this.riskCalcInterval = setInterval(async () => {
      // 统计全仓和期货的相关信息
      let marginAssetValue = 0
      let marginBorrowedValue = 0
      let futurePositionValue = 0
      for (let i = 0; i < this.items.length; i++) {
        if (this.items[i].show === false) {
          continue
        }
        let symbol = this.items[i].symbol
        let margin = this.items[i].margin
        let borrowed = this.items[i].marginBorrowed
        let futurePosition = this.items[i].future
        if (symbol !== 'USDT') {
          let price = this.mainPrice[symbol + 'USDT']
          marginAssetValue += price * margin
          marginBorrowedValue += price * borrowed
          futurePositionValue += this.futurePrice[symbol + 'USDT'] * futurePosition
        } else {
          marginAssetValue += margin
          marginBorrowedValue += borrowed
        }
      }
      // 套入公式计算风险（借币市值 + 借U / 持币市值 + 持U）
      if (marginAssetValue === 0) {
        this.marginRisk = 0
      } else {
        this.marginRisk = marginBorrowedValue / marginAssetValue
      }

      // 套入公式计算波动风险
      if (marginBorrowedValue - 0.8 * marginAssetValue === 0) {
        this.marginWarning = 99999
      } else {
        this.marginWarning = ((0.8 * marginAssetValue - marginBorrowedValue) / (marginBorrowedValue - 0.8 * marginAssetValue)) * 100
      }

      // 获取期货USDT资产
      let usdt = await this.ws.getData(['asset', 'future', 'USDT'])
      if (usdt === 0) {
        usdt = 0.00000001   // 避免除零错误
      }
      futurePositionValue = Math.abs(futurePositionValue)
      // 计算期货资金利用率 (期货总市值 / 期货余额)
      this.futureRisk = (futurePositionValue / usdt) * 100
      // 计算期货波动风险
      if (futurePositionValue !== 0) {
        let risk = (futurePositionValue + (5 * usdt - futurePositionValue) / 6) / futurePositionValue
        risk *= 100
        risk -= 100
        this.futureWarning = risk
      } else {
        this.futureWarning = 99999
      }


    }, 1000)
    // 获取及订阅所有现货价格
    this.mainPrice = await this.ws.getDict(['price', 'main'])
    await this.subscribe.dict(['price', 'main'], msg => {
      this.mainPrice[msg['special']] = msg['data']
    })

    // 获取及订阅所有期货价格
    this.futurePrice = await this.ws.getDict(['price', 'future'])
    await this.subscribe.dict(['price', 'future'], msg => {
      this.futurePrice[msg['special']] = msg['data']
    })

    // 获取及订阅当前所有现货资产
    let res = await this.ws.getDict(['asset', 'main'])
    let keys = Object.keys(res)
    keys.forEach(key => {
      this.setItem(key, 'main', res[key])
    })
    await this.subscribe.dict(['asset', 'main'], async msg => {
      let symbol = msg['special']
      let data = msg['data']
      await this.setItem(symbol, 'main', data)
    })

    // 获取及订阅当前所有全仓资产
    res = await this.ws.getDict(['asset', 'margin'])
    keys = Object.keys(res)
    keys.forEach(key => {
      this.setItem(key, 'margin', res[key])
    })
    await this.subscribe.dict(['asset', 'margin'], msg => {
      let symbol = msg['special']
      let data = msg['data']
      this.setItem(symbol, 'margin', data)
    })

    // 获取及订阅当前所有逐仓资产
    res = await this.ws.getDict(['asset', 'isolated', 'base'])
    keys = Object.keys(res)
    keys.forEach(key => {
      this.setItem(key.replace('USDT', ''), 'isolated', res[key])
    })
    await this.subscribe.dict(['asset', 'isolated', 'base'], msg => {
      let symbol = msg['special']
      let data = msg['data']
      this.setItem(symbol.replace('USDT', ''), 'isolated', data)
    })

    res = await this.ws.getDict(['asset', 'isolated', 'quote'])
    keys = Object.keys(res)
    keys.forEach(key => {
      this.setItem(key.replace('USDT', ''), 'isolatedQuote', res[key])
    })
    await this.subscribe.dict(['asset', 'isolated', 'quote'], msg => {
      let symbol = msg['special']
      let data = msg['data']
      this.setItem(symbol.replace('USDT', ''), 'isolatedQuote', data)
    })

    // 获取及订阅当前所有期货资产
    res = await this.ws.getDict(['position', 'future'])
    keys = Object.keys(res)
    keys.forEach(key => {
      this.setItem(key.replace('USDT', ''), 'future', res[key])
    })
    await this.subscribe.dict(['position', 'future'], msg => {
      let symbol = msg['special'].replace('USDT', '')
      let data = msg['data']
      this.setItem(symbol, 'future', data)
    })


  },
  components: {
    NoBorderButton
  }
}
</script>

<style scoped>

</style>