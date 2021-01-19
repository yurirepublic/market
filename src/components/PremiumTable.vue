<template>
  <div style="background-color: #fafafa;">
    <table class="table table-hover table-borderless table-sm small">
      <thead>
        <tr class="text-muted ">
          <th class="font-weight-normal">交易对</th>
          <th class="font-weight-normal">资金费率</th>
          <th class="font-weight-normal">现货币价(U)</th>
          <th class="font-weight-normal">期货溢价</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="item in items"
          :key="item['symbol']"
          @click="premiumClickAction(item['symbol'])"
        >
          <td class="text-monospace " style="">
            {{ item["symbol"] }}
          </td>

          <td
            class="text-monospace "
            style="color: #02c076"
            v-if="parseFloat(item['rate']) > 0"
          >
            {{ item["rate"] }}%
          </td>
          <td
            class="text-monospace "
            style="color: #f84960"
            v-if="parseFloat(item['rate']) < 0"
          >
            {{ item["rate"] }}%
          </td>
          <td class="text-monospace " v-if="parseFloat(item['rate']) == 0">
            {{ item["rate"] }}%
          </td>

          <td class="text-monospace ">
            {{ item["price"] }}
          </td>

          <td
            class="text-monospace "
            style="color: #02c076"
            v-if="parseFloat(item['further_premium']) > 0"
          >
            {{ item["further_premium"] }}%
          </td>
          <td
            class="text-monospace "
            style="color: #f84960"
            v-if="parseFloat(item['further_premium']) < 0"
          >
            {{ item["further_premium"] }}%
          </td>
          <td
            class="text-monospace "
            v-if="parseFloat(item['further_premium']) == 0"
          >
            {{ item["further_premium"] }}%
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: "PremiumTable",
  data: function () {
    return {
      items: [],
    };
  },
  methods: {
    refresh: function () {
      this.method_request("request_premium", []).then((res) => {
        this.items = res["data"];
        this.$toast.open({
          message: "资金费率表格加载成功",
        });
      });
    },
  },
  mounted: function () {
    this.refresh();
  },
};
</script>

<style scoped>
</style>