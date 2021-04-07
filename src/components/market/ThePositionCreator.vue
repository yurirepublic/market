<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="">
      <div class="mb-2">
        <span class="font-weight-bold">下单</span>
      </div>
      <div v-if="isLoading">
        <div v-if="banReason === ''">
          <v-icon name="ri-loader-4-line" animation="spin"></v-icon>
          <span>正在加载交易数据</span>
        </div>

        <div v-if="banReason !== ''">
          <v-icon name="ri-error-warning-line"></v-icon>
          <span>交易数据加载失败：</span>
          <span>{{ banReason }}</span>
        </div>


      </div>
      <div v-if="!isLoading">
        <div class="">
          <div>
            <trade-input
                header="交易对"
                placeholder="点击表格"
                disabled="true"
                :value="pairSymbol"
            />
            <trade-input
                class="mt-2"
                header="单方下单金额"
                footer="USDT"
                v-model="wantMoney"
                @input="ValueChanged('value')"
            />
            <trade-input
                class="mt-2"
                header="每边下单"
                :footer="baseSymbol"
                v-model="quantity"
                @input="ValueChanged('quantity')"
            />
          </div>
        </div>
        <div class="mt-3 d-flex flex-column">
          <info-item header="货币精度">{{ quotePrecision }}</info-item>
          <info-item header="预计8小时收益" footer="USDT">{{ toPrecision(benefit, 2) }}</info-item>
          <info-item header="预计8小时收益" footer="USDT">{{ toPrecision(benefit, 2) }}</info-item>
          <info-item header="总开仓手续费" footer="USDT">{{ toPrecision(totalTax, 2) }}</info-item>
          <span class="text-muted small align-self-end">
            现货手续费(以0.075%) {{ toPrecision(mainTax, 2) }} USDT
          </span>
          <span class="text-muted small align-self-end float-right">
            期货手续费(以0.040%) {{ toPrecision(futureTax, 2) }} USDT
          </span>
          <div class="d-flex flex-row justify-content-between mt-2">
            <span class="align-middle text-muted small">现货下单位置</span>
            <div class="d-flex">
              <no-border-button class="btn checkbox ml-2 checkbox-check" v-if="mainMode==='MAIN'"
                                @click="ChangeMainMode('MAIN')">现货
              </no-border-button>
              <no-border-button class="btn checkbox ml-2 checkbox-nocheck" v-if="mainMode!=='MAIN'"
                                @click="ChangeMainMode('MAIN')">现货
              </no-border-button>
              <no-border-button class="btn checkbox ml-2 checkbox-check" v-if="mainMode==='MARGIN'"
                                @click="ChangeMainMode('MARGIN')">全仓
              </no-border-button>
              <no-border-button class="btn checkbox ml-2 checkbox-nocheck" v-if="mainMode!=='MARGIN'"
                                @click="ChangeMainMode('MARGIN')">全仓
              </no-border-button>
              <no-border-button class="btn checkbox ml-2 checkbox-check" v-if="mainMode==='ISOLATED'"
                                @click="ChangeMainMode('ISOLATED')">逐仓
              </no-border-button>
              <no-border-button class="btn checkbox ml-2 checkbox-nocheck" v-if="mainMode!=='ISOLATED'"
                                @click="ChangeMainMode('ISOLATED')">逐仓
              </no-border-button>
            </div>
          </div>

          <div class="d-flex flex-row justify-content-between mt-2" v-if="disabledTrade">
            <span class="align-middle text-muted small">禁止下单原因</span>
            <span
                class="align-middle text-muted small"
            >{{ banReason }}</span>
          </div>

          <div class="d-flex flex-row justify-content-between mt-2">
            <span class="align-middle text-muted small">警告列表</span>
          </div>

          <div class="d-flex">
            <button
                type="submit"
                class="btn btn-primary mt-3 px-2"
                @click="OpenPosition"
                :disabled="disabledTrade"
                style="background-color: #02c076; border-color: transparent"
            >
              多现货 空期货 (正向)
            </button>
            <button
                type="submit"
                class="btn btn-primary mt-3 px-2 ml-2"
                @click="ClosePosition"
                :disabled="disabledTrade"
                style="background-color: #f84960; border-color: transparent"
            >
              多期货 空现货 (反向)
            </button>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import TradeInput from "@/components/TradeInput.vue"
import InfoItem from "@/components/InfoItem.vue"
import NoBorderButton from "@/components/NoBorderButton"

export default {
  name: "ThePositionCreator",

  props: {
    pairSymbol: ''    // 用于开仓的交易对
  },

  data: function () {
    return {
      // 填写的信息
      wantMoney: 0, // 想要开仓的总价值
      quantity: 0, // 开仓的币数
      mainMode: 'MAIN',   // 现货下单模式，可能为MAIN、MARGIN、ISOLATED

      // 获取的信息
      quotePrecision: NaN,
      fundingRate: NaN,

      // 计算得出的信息
      baseSymbol: '',   // 从pariSymbol去除USDT得到
      benefit: 0, // 8小时收益
      mainTax: 0, // 现货手续费
      futureTax: 0, // 期货手续费
      totalTax: 0, // 总开仓手续费

      isLoading: false,    // 是否正在加载所需数据
      disabledTrade: true, // 是否禁止下单（数据有错的情况）


      banReason: '',   // 下单的错误原因，被禁止下单时会显示原因
      warnings: [],    // 下单的警告列表，无论是否禁止下单都会显示

      dontRepeat: false,   // 表示不要重复计算的flag，用于侦听数量和价值变量时不重复计算

      ws: null,    // 与数据中心交互的websocket
    }
  },

  mounted: async function () {
    this.ws = await this.connectDataCenter()
    await this.ValueChanged('value')
  },

  watch: {
    pairSymbol: async function () {
      // 提前获取需要的信息
      this.banReason = ''
      this.isLoading = true
      let mainPrice = this.ws.getData(['price', 'main', this.pairSymbol]) // 交易对单价
      let futurePrice = this.ws.getData(['price', 'future', this.pairSymbol])
      let fundingRate = this.ws.getData(['premium', 'fundingRate', this.pairSymbol])  // 资金费率

      this.mainPrice = await mainPrice
      this.futurePrice = await futurePrice
      this.fundingRate = await fundingRate

      if (mainPrice === null) {
        this.banReason = '无法获取该交易对现货价格'
        return
      }
      if (futurePrice === null) {
        this.banReason = '无法获取该交易对期货价格'
        return
      }
      if (fundingRate === null) {
        this.banReason = '无法获取该交易对资金费率'
        return
      }
      let mainPrecision = this.ws.getData(['precision', 'quote', 'main', this.pairSymbol])
      let futurePrecision = this.ws.getData(['precision', 'quote', 'future', this.pairSymbol])
      mainPrecision = await mainPrecision
      futurePrecision = await futurePrecision
      this.quotePrecision = Math.min(mainPrecision, futurePrecision)
      if (mainPrecision === null) {
        this.banReason = '无法获取现货下单精度'
        return
      }
      if (futurePrecision === null) {
        this.banReason = '无法获取期货下单精度'
        return
      }
      this.isLoading = false
      await this.ValueChanged('value')
    }
  },

  methods: {
    // 加仓下单
    OpenPosition: function () {
      // 发送开仓指令
      this.disabledTrade = true
      this.banReason = '正在下单'
      this.apiRequest("trade_premium", [this.pairSymbol, this.quantity, 'OPEN', this.mainMode])
          .then((res) => {
            this.showToast.success("加仓成功")
          })
          .catch((err) => {
            console.log(this.showToast)
            this.showToast.error("加仓失败")
          })
          .finally(() => {
            this.disabledTrade = false
          })
    },

    // 减仓下单
    ClosePosition: function () {
      // 发送指令
      this.disabledTrade = true
      this.banReason = '正在下单'
      this.apiRequest("trade_premium", [this.pairSymbol, this.quantity, 'CLOSE', this.mainMode])
          .then((res) => {
            this.showToast.success("减仓成功")
          })
          .catch((err) => {
            console.log(this.showToast)
            this.showToast.error("减仓失败")
          })
          .finally(() => {
            this.disabledTrade = false
          })
    },

    // 交易对or开仓数改变时重新计算，有输入mode代表是开仓数改变，mode可以是value和quantity
    ValueChanged: async function (mode) {
      this.banReason = ''
      this.warnings = []

      // 没有交易对的情况下直接返回
      if (this.pairSymbol === '') {
        this.banReason = '无交易对'
        return
      }

      this.baseSymbol = this.pairSymbol.replace('USDT', '')

      // 这个函数用来一键清除计算结果，适用于输入非法的情况
      const CLearOutput = () => {
        this.disabledTrade = true
        this.benefit = 0
        this.mainTax = 0
        this.futureTax = 0
        this.totalTax = 0
      }

      // 输入数字为空的情况下，清空计算结果
      if (this.wantMoney === "" && this.quantity === "") {
        this.banReason = '输入数字为空'
        CLearOutput()
        return
      }

      // 输入非法的情况下，清空计算结果
      if (
          !(this.isNumber(this.wantMoney) && parseFloat(this.wantMoney) >= 0) &&
          !(this.isNumber(this.quantity) && parseFloat(this.quantity) >= 0)
      ) {
        this.banReason = '输入非法'
        CLearOutput()
        return
      }

      // 超精度的情况下清空计算结果
      if (parseFloat(this.float2strRound(this.wantMoney, 8)) !== parseFloat(this.wantMoney)
          && mode === 'value') {
        this.banReason = '欲下单金额超出精度'
        CLearOutput()
        return
      }
      if (parseFloat(this.float2strRound(this.quantity, this.quotePrecision)) !== parseFloat(this.quantity)
          && mode === 'quantity') {
        this.banReason = '欲下单货币数额超出精度'
        CLearOutput()
        return
      }

      let wantMoney = parseFloat(this.wantMoney) // 单边开仓价值

      let quantity = parseFloat(this.quantity)    // 欲下单的货币数量


      // 如果以数量为基准，计算开仓价值
      if (mode === 'quantity') {
        wantMoney = this.mainPrice * quantity
        this.wantMoney = this.float2strFloor(wantMoney, 8)
      }
      // 如果以价值为基准，就计算数量
      else if (mode === 'value') {
        quantity = wantMoney / this.mainPrice
        this.quantity = this.float2strFloor(quantity, this.quotePrecision)
      }

      // 计算收益和手续费
      this.benefit = wantMoney * this.fundingRate
      this.mainTax = wantMoney * 0.00075
      this.futureTax = wantMoney * 0.0004
      this.totalTax = this.mainTax + this.futureTax

      this.disabledTrade = false
    },

    // 切换下单位置
    ChangeMainMode: function (mode) {
      this.mainMode = mode
    },
  },

  components: {
    TradeInput,
    InfoItem,
    NoBorderButton
  },
}
</script>

<style scoped>
.checkbox {
  border-radius: 5px;
  padding: 3px;
}

.checkbox-check {
  background-color: #505050;
  color: #ffffff;
}

.checkbox-nocheck {
  background-color: #e1e1e1;
}
</style>