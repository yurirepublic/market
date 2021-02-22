<template>
  <div
    class="p-2"
    style="
      overflow: auto;
      max-height: 40rem;
      min-width: 17rem;
      background-color: #fafafa;
    "
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
        <tr v-for="(item, index) in havingItems" :key="item['symbol']">
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
              :disabled="button_disabled"
            >
              平仓
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="mb-2 d-flex justify-content-between align-items-center">
      <span class="font-weight-bold">孤立仓位</span>
    </div>
    <table class="table table-hover table-borderless table-sm small">
      <thead>
        <tr class="text-muted">
          <th class="font-weight-normal">交易对</th>
          <th class="font-weight-normal">仓位</th>
          <th class="font-weight-normal">类型</th>
          <th class="font-weight-normal">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in havingItemsSingle" :key="item['symbol']">
          <td class="text-monospace align-middle">
            {{ item["symbol"] }}
          </td>
          <td class="text-monospace align-middle">
            {{ item["quantity"] }}
          </td>
          <td class="align-middle">
            {{ item["type"] }}
          </td>
          <td>
            <button
              class="btn btn-secondary btn-sm"
              type="button"
              @click="CloseSingle(item)"
              @click.stop
              :disabled="button_disabled"
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
      havingItemsSingle: [],
      refresh_button_anime: false,

      button_disabled: false,
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
          this.havingItems = res["data"]["pair"];
          this.havingItemsSingle = res["data"]["single"];

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
      console.log("即将平仓双向交易对", item);
      this.button_disabled = true;
      // 平仓下单
      console.log("平仓下单符号", item["symbol"]);
      console.log("平仓下单数量", item["quantity"]);
      this.showToast().info("开始平仓" + item["symbol"]);
      this.method_request("destroy_premium", [item["symbol"], item["quantity"]])
        .then((res) => {
          this.showToast().success(item["symbol"] + "成功平仓");
        })
        .catch((err) => {
          this.showToast().error("平仓失败");
        })
        .finally(() => {
          this.button_disabled = false;
        });
    },

    // 平孤立仓
    CloseSingle(item) {
      console.log("即将平孤立仓", item["symbol"]);
      console.log("平仓下单符号", item["symbol"]);
      console.log("平仓下单数量", item["quantity"]);
      if (item["type"] == "现货") {
        console.log("平仓区域", "现货");
      } else if (item["type"] == "期货") {
        console.log("平仓区域", "期货");
      } else {
        console.error("没找到平仓区域");
      }
    },
  },

  components: {
    RefreshButton,
  },
};
</script>