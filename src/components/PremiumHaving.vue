<template>
  <div
    class="p-2"
    style="overflow: auto; max-height: 20rem; background-color: #fafafa"
  >
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">双向持仓交易对</span>
      <RefreshButton :anime="refresh_button_anime" @click="refresh" />
    </div>
    <table class="table table-hover table-borderless table-sm small">
      <thead>
        <tr class="text-muted">
          <th class="font-weight-normal">交易对</th>
          <th class="font-weight-normal">仓位</th>
          <th class="font-weight-normal">操作</th>
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
              class="btn btn-secondary btn-sm"
              type="button"
              @click="CloseOut(item)"
              @click.stop
            >
              平仓
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import RefreshButton from "@/components/RefreshButton.vue";

export default {
  name: "PremiumHaving",
  data: function () {
    return {
      havingItems: [],
      refresh_button_anime: false,
    };
  },
  mounted: function () {
    this.refresh();
  },

  methods: {
    // 刷新持仓
    refresh() {
      this.refresh_button_anime = true;

      // 获取套利开仓情况
      this.method_request("analyze_premium", [])
        .then((res) => {
          this.havingItems = res["data"];

          this.$toast.open({
            message: "套利开仓情况获取成功",
            type: "success",
          });
        })
        .catch((err) => {
          this.$toast.open({
            message: "套利开仓情况获取失败",
            type: "error",
          });
        })
        .finally(() => {
          this.refresh_button_anime = false;
        });
    },

    // 平仓
    CloseOut(item) {
      console.log(item);
      // 平仓下单
      console.log("平仓下单符号", item['symbol']);
      console.log("平仓下单数量", item['quantity']);
      this.method_request("destroy_premium", item['symbol'], item['quantity']);
    },
  },

  components: {
    RefreshButton,
  },
};
</script>