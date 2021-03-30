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
            {{ item["symbol"] }}
          </td>

          <td
              class="text-monospace"
              style="color: #02c076"
              v-if="parseFloat(item['rate']) > 0"
              nowrap="nowrap"
          >
            {{ item["rate"] }}%
          </td>
          <td
              class="text-monospace"
              style="color: #f84960"
              v-if="parseFloat(item['rate']) < 0"
              nowrap="nowrap"
          >
            {{ item["rate"] }}%
          </td>
          <td
              class="text-monospace"
              v-if="parseFloat(item['rate']) == 0"
              nowrap="nowrap"
          >
            {{ item["rate"] }}%
          </td>

          <td
              class="text-monospace"
              style="color: #02c076"
              v-if="parseFloat(item['avg_rate']) > 0"
              nowrap="nowrap"
          >
            {{ item["avg_rate"] }}%
          </td>
          <td
              class="text-monospace"
              style="color: #f84960"
              v-if="parseFloat(item['avg_rate']) < 0"
              nowrap="nowrap"
          >
            {{ item["avg_rate"] }}%
          </td>
          <td
              class="text-monospace"
              v-if="parseFloat(item['avg_rate']) == 0"
              nowrap="nowrap"
          >
            {{ item["avg_rate"] }}%
          </td>

          <td class="text-monospace" nowrap="nowrap">
            {{ item["price"] }}
          </td>

          <td
              class="text-monospace"
              style="color: #02c076"
              v-if="parseFloat(item['future_premium']) > 0"
              nowrap="nowrap"
          >
            {{ item["future_premium"] }}%
          </td>
          <td
              class="text-monospace"
              style="color: #f84960"
              v-if="parseFloat(item['future_premium']) < 0"
              nowrap="nowrap"
          >
            {{ item["future_premium"] }}%
          </td>
          <td
              class="text-monospace"
              v-if="parseFloat(item['future_premium']) == 0"
              nowrap="nowrap"
          >
            {{ item["future_premium"] }}%
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
      items: [],
      refresh_button_anime: false,
      ws: null,   // 当前正在连接的websocket
    };
  },
  methods: {},
  mounted: function () {
    // 关闭之前的旧连接
    if (this.ws !== null) {
      this.ws.close(1000)
    }
    // 打开新连接
    let ws = new WebSocket(this.localConfig.subscribeUrl)
    this.ws = ws
    ws.onmessage = msg => {
      let data = JSON.parse(msg.data)
      let tags = data['tags']
      let special = data['special']
      data = Math.round(data.data * 10000) / 100
      if (tags.includes('premium') && tags.includes('rate')) {
        // 查找表格项目有没有对应的symbol
        for (let i = 0; i < this.items.length; i++) {
          let e = this.items[i]
          if (e.symbol === special) {
            this.items[i].future_premium = data
          }
        }
        this.items = this.items
      }
    }
    ws.onclose = msg => {
      console.log('ws被关闭', msg)
    }
    ws.onopen = async msg => {
      console.log('ws成功打开', msg)
      // 向服务器发送自己的密码和订阅内容
      await ws.send(this.localConfig.password)
      await ws.send(JSON.stringify({
        tags: ['premium', 'rate'],
        mode: 'SUBSCRIBE_DICT',
        comment: 'rate'
      }))
    }


  },
  components: {
    RefreshButton,
  },
};
</script>

<style scoped>
</style>
