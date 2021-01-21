<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">套利行情</span>
      <RefreshButton :anime="refresh_button_anime" @click="refresh"/>
    </div>
    <div style="overflow: auto; max-height: 15rem">
      <table class="table table-hover table-borderless table-sm small">
        <thead>
          <tr class="text-muted">
            <th class="font-weight-normal" nowrap="nowrap">交易对</th>
            <th class="font-weight-normal" nowrap="nowrap">资金费率</th>
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
    };
  },
  methods: {
    refresh: function () {
      this.refresh_button_anime = true;
      this.method_request("request_premium", [])
        .then((res) => {
          this.items = res["data"];
          this.$toast.open({
            message: "资金费率表格加载成功",
            type: "success",
          });
        })
        .catch((error) => {
          this.$toast.open({
            message: "资金费率表格加载失败",
            type: "error",
          });
        })
        .finally(() => {
          this.refresh_button_anime = false;
        });
    },
  },
  mounted: function () {
    this.refresh();
  },
  components: {
    RefreshButton,
  },
};
</script>

<style scoped>
</style>