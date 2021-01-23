<template>
  <div class="p-2" style="background-color: #fafafa">
    <div class="mb-2">
      <span class="font-weight-bold">100次资金费率表</span>
      <span>{{ pair_item["symbol"] }}</span>
    </div>
    <TrendChart
      :datasets="[
        {
          data: price_list,
          smooth: false,
          fill: true,
        },
      ]"
      :labels="{
        yLabels: 5,
        yLabelsTextFormatter: (val) => Math.round(val * 10000) / 100 + '%',
      }"
    >
    </TrendChart>
  </div>
</template>

<script>
import TrendChart from "vue-trend-chart";

export default {
  name: "PremiumHistory",

  props: {
    pair_item: {
      type: Object,
      default: function () {
        return {};
      },
    },
  },

  data: function () {
    return {
      price_list: [0, 0, 0],
      times: [1, 2, 3],
    };
  },

  watch: {
    pair_item() {
      this.method_request("premium_history", [this.pair_item["symbol"]]).then(
        (res) => {
          this.price_list = res["data"]["rate"];
          let temp = [];
          res["data"]["time"].forEach((e) => {
            let date = new Date(e);
            if (date.getHours() == 0) {
              temp.push(date.getDate());
            }
          });
          this.times = temp;
        }
      );
    },
  },

  mounted: function () {},

  methods: {},
  components: {
    TrendChart,
  },
};
</script>

<style scoped>
</style>