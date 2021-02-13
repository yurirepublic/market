<template>
  <div>
    <div class="p-1">
      <CardFrame>
        <div>运行中的脚本</div>
        <div>
          <table class="table table-hover table-borderless table-sm small">
            <thead>
              <tr class="text-muted">
                <th class="font-weight-normal">线程号</th>
                <th class="font-weight-normal">脚本名</th>
                <th class="font-weight-normal">运行状态</th>
                <th class="font-weight-normal">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in running_script_list"
                :key="item.thread_id"
                @click="ShowFocusLog(item)"
              >
                <td class="align-middle">
                  {{ item.thread_id }}
                </td>
                <td class="align-middle">
                  {{ item.name }}
                </td>
                <td class="align-middle">
                  {{ item.status }}
                </td>
                <td>
                  <button
                    class="btn btn-secondary btn-sm"
                    type="button"
                    @click="StopScript(item)"
                    @click.stop
                    :disabled="button_disabled"
                  >
                    终止
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div>
          <pre>{{ focus_log }}</pre>
        </div>
      </CardFrame>
    </div>
  </div>
</template>

<script>
import CardFrame from "@/components/CardFrame.vue";

export default {
  name: "RunningScript",
  data: function () {
    return {
      running_script_list: [],
      button_disabled: false,

      focus_log: "", // 选中脚本的log
    };
  },
  mounted: function () {
    this.method_request("running_script", [])
      .then((res) => {
        this.running_script_list = res.data;
        this.showToast().success("运行中的脚本列表获取成功");
      })
      .catch((err) => {
        this.showToast().error("运行中的脚本列表获取失败");
      });
  },
  methods: {
    StopScript: function (item) {
      this.button_disabled = true;
      this.method_request("stop_script", [item.thread_id])
        .then((res) => {
          this.showToast().success("脚本终止成功");
        })
        .catch((err) => {
          this.showToast().error("脚本终止失败");
        })
        .finally(() => {
          this.button_disabled = false;
        });
    },
    ShowFocusLog: function (item) {
      console.log("选中脚本线程号", item.thread_id);
      this.method_request("script_log", [item.thread_id])
        .then((res) => {
          this.focus_log = res.data;
          this.showToast().success("获取选中脚本log成功");
        })
        .catch((err) => {
          this.showToast().error("获取选中脚本log失败");
        });
    },
  },
  components: {
    CardFrame,
  },
};
</script>

<style lang="stylus" scoped></style>