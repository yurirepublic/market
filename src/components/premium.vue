<template>
  <div class="d-flex justify-content-center">
    <div class="d-flex justify-content-center">
      <div class="">
        <div class="card shadow">
          <div class="" style="overflow: auto; max-height: 15rem">
            <MiniTable v-bind:columns="premium_table_columns">

            </MiniTable>

            <!-- <table class="table table-hover small">
              <thead>
                <tr>
                  <th>交易对</th>
                  <th>资金费率</th>
                  <th>现货币价(U)</th>
                  <th>期货溢价</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="item in items"
                  :key="item['symbol']"
                  @click="premiumClickAction(item['symbol'])"
                >
                  <td class="text-monospace">
                    {{ item["symbol"] }}
                  </td>

                  <td
                    class="text-monospace"
                    style="color: #02c076"
                    v-if="parseFloat(item['rate']) > 0"
                  >
                    {{ item["rate"] }}%
                  </td>
                  <td
                    class="text-monospace"
                    style="color: #f84960"
                    v-if="parseFloat(item['rate']) < 0"
                  >
                    {{ item["rate"] }}%
                  </td>
                  <td
                    class="text-monospace"
                    v-if="parseFloat(item['rate']) == 0"
                  >
                    {{ item["rate"] }}%
                  </td>

                  <td class="text-monospace">
                    {{ item["price"] }}
                  </td>

                  <td
                    class="text-monospace"
                    style="color: #02c076"
                    v-if="parseFloat(item['further_premium']) > 0"
                  >
                    {{ item["further_premium"] }}%
                  </td>
                  <td
                    class="text-monospace"
                    style="color: #f84960"
                    v-if="parseFloat(item['further_premium']) < 0"
                  >
                    {{ item["further_premium"] }}%
                  </td>
                  <td
                    class="text-monospace"
                    v-if="parseFloat(item['further_premium']) == 0"
                  >
                    {{ item["further_premium"] }}%
                  </td>
                </tr>
              </tbody>
            </table> -->
          </div>
        </div>

        <div class="card shadow mt-3">
          <div class="p-3">
            <div class="">
              <div class="">
                <div>
                  <div class="input-group">
                    <label class="input-group-text">双向交易对</label>
                    <input
                      class="form-control text-right text-monospace"
                      placeholder="点击表格"
                      :value="pair_symbol"
                    />
                  </div>
                  <div class="mt-3 input-group">
                    <label class="input-group-text">双向总金额</label>
                    <input
                      class="form-control text-right text-monospace"
                      type="number"
                      v-model="create_value"
                      @input="premiumValueChange"
                    />
                    <label class="input-group-text">USDT</label>
                  </div>
                  <div class="mt-3 input-group">
                    <label class="input-group-text">合约杠杆率</label>
                    <input
                      class="form-control text-right"
                      type="number"
                      placeholder="1"
                      disabled
                    />
                  </div>
                </div>
              </div>
              <div class="mt-3">
                <div class="d-flex justify-content-between">
                  <label>每边开仓</label>
                  <label class="text-monospace text-primary"
                    >{{ quantity }} {{ symbol }}</label
                  >
                </div>
                <div class="d-flex justify-content-between">
                  <label>预计8小时收益</label>
                  <label class="text-monospace text-primary"
                    >{{ benefit }} USDT</label
                  >
                </div>
                <div class="d-flex justify-content-between">
                  <label>预计开仓手续费(以0.075%)</label>
                  <label class="text-monospace text-primary"
                    >{{ tax }} USDT</label
                  >
                </div>
                <button
                  type="submit"
                  class="btn btn-primary mt-3"
                  @click="primaryTradeClick"
                  :disabled="disabled_trade"
                >
                  下单
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="ml-3">
        <div class="card shadow">
          <div class="p-2">
            <div class="d-flex justify-content-between">
              <label>可用现货</label>
              <label class="ml-2 text-primary text-monospace"
                >{{ free_usdt }} USDT</label
              >
            </div>
            <div class="d-flex justify-content-between">
              <label>可用期货</label>
              <label class="ml-2 text-primary text-monospace"
                >{{ free_further_usdt }} USDT</label
              >
            </div>
            <div class="d-flex justify-content-between">
              <span>资金充足率</span>
              <span class="ml-2 text-primary text-monospace"
                >{{ free_further_usdt }}%</span
              >
            </div>
            <div class="d-flex justify-content-end">
              <button
                class="btn btn-secondary"
                type="button"
                @click="refreshWallet"
                @click.stop
              >
                刷新
              </button>
            </div>
          </div>
        </div>

        <div class="card shadow mt-3">
          <div style="overflow: auto; max-height: 20rem">
            <table class="table table-hover small">
              <thead>
                <tr>
                  <th>交易对</th>
                  <th>仓位</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, index) in havingItems"
                  :key="item['symbol']"
                  @click="premiumClickAction(item[index])"
                >
                  <td class="text-monospace align-middle">
                    {{ item["symbol"] }}
                  </td>
                  <td class="text-monospace align-middle">
                    {{ item["quantity"] }}
                  </td>
                  <td>
                    <button
                      class="btn btn-secondary"
                      type="button"
                      @click="
                        premiumDestoryClick(item['symbol'], item['quantity'])
                      "
                      @click.stop
                    >
                      平仓
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import request from 'request'
import MiniTable from '@/components/MiniTable.vue'

async function method_request(func, args) {
  return await new Promise(function (resolve, reject) {
    // const request = require("request");
    request.post(
      {
        url: "http://us.pwp.today:11327",
        form: {
          function: func,
          args: JSON.stringify(args),
        },
      },
      function (err, httpResponse, body) {
        if (err) {
          reject(err);
          return;
        }
        if (httpResponse.statusCode != 200) {
          reject(httpResponse);
          return;
        }
        let res = JSON.parse(body);
        if (res['msg'] != 'success') {
          reject(res)
          return
        }
        console.log(res);
        resolve(res['data']);
      }
    );
  });
}

export default {
  name: "premium",
  data: function () {
    return {
      // 资金费率表格
      premium_table_columns: ['交易对', '资金费率', '现货币价', '期货溢价'],
      premium_table_items: [],

      havingItems: [], // 套利持仓表格

      free_usdt: "", // 现货剩余usdt
      free_further_usdt: "", // 期货剩余usdt

      pair_symbol: "", // 想要套利的交易对
      create_value: "", // 开仓的总价值
      create_rate: "", // 开仓的合约杠杆率

      benefit: 0, // 计算的收益
      tax: 0, // 计算的手续费
      quantity: "", // 开仓的币数(需要用于最终下单，所以是字符串)
      symbol: "", // 开仓的货币符号(仅用于显示)
      disabled_trade: true, // 是否将下单按钮无效化
    }
  },
  methods: {
    // 刷新账户余额
    refreshWallet: function () {
      this.free_usdt = "";
      this.free_further_usdt = "";
      // 获取账户余额
      method_request("wallet_money", []).then((res) => {
        this.free_usdt = res[0];
        this.free_further_usdt = res[1];
      });
    },

    // 自动填写货币对
    premiumClickAction: function (pair_symbol) {
      console.log(pair_symbol);
      // 更新一下要下单的货币种类
      this.pair_symbol = pair_symbol;
      this.premiumValueChange(); // 主动触发一下事件刷新信息
    },

    // 平仓下单
    premiumDestoryClick: function (pair_symbol, quantity) {
      console.log("平仓下单符号", pair_symbol);
      console.log("平仓下单数量", quantity);
      method_request("destroy_premium", [pair_symbol, quantity]);
    },

    // 开仓下单
    primaryTradeClick: function () {
      // 取出要下单的交易对
      let pair_symbol = this.pair_symbol;
      // 取出要下单的数量
      let quantity = this.quantity;
      // 发送开仓指令
      method_request("create_premium", [pair_symbol, quantity]);
    },

    // 自动计算收益
    premiumValueChange: function (event) {
      console.log(this.create_value);
      // 输入数字为空的情况下，清空计算结果
      if (this.create_value == "") {
        this.disabled_trade = true;
        this.benefit = 0;
        this.tax = 0;
        this.quantity = 0;
        this.symbol = "";
        return;
      }
      let side_value = parseFloat(this.create_value) / 2; // 单边开仓价值
      let price = 0; // 等待读取的币价
      let percision = 0; // 等待读取的精度
      let rate = 0; // 等待读取的利率
      this.items.forEach((e) => {
        if (e["symbol"] == this.pair_symbol) {
          price = parseFloat(e["price"]);
          percision = e["percision"];
          rate = e["rate"];
        }
      });
      if (price != 0) {
        let quantity = side_value / price;
        // 将数字乘以精度
        quantity *= Math.pow(10, percision);
        // 向下取整
        quantity = Math.floor(quantity);
        // 将数字除以精度
        // 为什么要这么弄？因为浮点数精度问题不可忽视，最终结果不能出现999999
        quantity /= Math.pow(10, percision);

        this.quantity = quantity.toString();

        // 计算收益和手续费
        let benefit = (side_value * 2 * rate) / 100;
        let tax = (side_value * 2 * 0.075) / 100;

        benefit = Math.round(benefit * 1000) / 1000;
        tax = Math.round(tax * 1000) / 1000;

        this.benefit = benefit;
        this.tax = tax;

        this.symbol = this.pair_symbol.replace("USDT", "");
        this.disabled_trade = false;
      }
    },
  },
  mounted: function () {
    // 获取货币对
    method_request("request_premium", []).then((res) => {
      this.items = res['data']
    }).catch(error => {
      this.$toast.open({
        message: '成功获取溢价货币对',
      })
    })

    method_request("wallet_money", []).then((res) => {
      this.free_usdt = res[0];
      this.free_further_usdt = res[1];
    });

    // 获取套利开仓情况
    method_request("analyze_premium", []).then((res) => {
      this.havingItems = res;
    });
  },
  components: {
    MiniTable
  }
};
</script>

<style scoped>
</style>