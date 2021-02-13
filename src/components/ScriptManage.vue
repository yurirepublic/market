<template>
  <div>
    <div>脚本列表</div>
    <div>
      <table class="table table-hover table-borderless table-sm small">
        <thead>
          <tr class="text-muted">
            <th class="font-weight-normal">脚本名</th>
            <th class="font-weight-normal">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in script_list" :key="item">
            <td class="align-middle">
              {{ item }}
            </td>
            <td>
              <button
                class="btn btn-secondary btn-sm"
                type="button"
                @click="RunScript(item)"
                @click.stop
                :disabled="button_disabled"
              >
                开始运行
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: "ScriptManage",
  data: function () {
    return {
      script_list: [],
      button_disabled: false,
    };
  },
  mounted: function () {
    this.method_request("script_list", [])
      .then((res) => {
        this.showToast().success("脚本列表获取成功");
        this.script_list = res.data;
      })
      .catch((err) => {
        this.showToast().error("脚本列表获取失败");
      });
  },
  methods: {
    RunScript: function (item) {
      console.log("将要运行", item);
      this.method_request("run_script", [item])
        .then((res) => {
          this.showToast().success("脚本运行成功");
        })
        .catch((err) => {
          this.showToast().error("脚本运行失败");
        });
    },
  },
};
</script>

<style lang="stylus" scoped></style>