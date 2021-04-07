<template>
  <div class='d-flex justify-content-center p-1'>
    <div class=''>
      <card-frame>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>运行中的脚本</span>
          <refresh-button :anime='refresh_button_anime' @click='Refresh' />
        </div>
        <div>
          <table class='table table-hover table-borderless table-sm small'>
            <thead>
            <tr class='text-muted'>
              <th class='font-weight-normal'>线程号</th>
              <th class='font-weight-normal'>脚本名</th>
              <th class='font-weight-normal'>运行状态</th>
              <th class='font-weight-normal'>操作</th>
            </tr>
            </thead>
            <tbody>
            <tr
              v-for='item in running_script_list'
              :key='item.thread_id'
              @click='ShowFocusLog(item)'
            >
              <td class='align-middle'>
                {{ item.thread_id }}
              </td>
              <td class='align-middle'>
                {{ item.name }}
              </td>
              <td class='align-middle'>
                {{ item.status }}
              </td>
              <td>
                <button
                  class='btn btn-secondary btn-sm'
                  type='button'
                  @click='StopScript(item)'
                  @click.stop
                  :disabled='button_disabled'
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
      </card-frame>
    </div>
  </div>
</template>

<script>
import CardFrame from '@/components/CardFrame.vue'
import RefreshButton from '@/components/RefreshButton.vue'

export default {
  name: 'RunningScript',
  data: function() {
    return {
      running_script_list: [],
      button_disabled: false,
      refresh_button_anime: false,

      focus_log: '' // 选中脚本的log
    }
  },
  mounted: function() {
    this.Refresh()
  },
  methods: {
    Refresh: function() {
      this.refresh_button_anime = true
      this.method_request('running_script', [])
        .then((res) => {
          this.running_script_list = res.data
          this.showToast.success('运行中的脚本列表获取成功')
        })
        .catch((err) => {
          this.showToast.error('运行中的脚本列表获取失败')
        })
        .finally(() => {
          this.refresh_button_anime = false
        })
    },
    StopScript: function(item) {
      this.button_disabled = true
      this.method_request('stop_script', [item.thread_id])
        .then((res) => {
          this.showToast.success('脚本终止成功')
        })
        .catch((err) => {
          this.showToast.error('脚本终止失败')
        })
        .finally(() => {
          this.button_disabled = false
        })
    },
    ShowFocusLog: function(item) {
      console.log('选中脚本线程号', item.thread_id)
      this.method_request('script_log', [item.thread_id])
        .then((res) => {
          this.focus_log = res.data
          this.showToast.success('获取选中脚本log成功')
        })
        .catch((err) => {
          this.showToast.error('获取选中脚本log失败')
        })
    }
  },
  components: {
    CardFrame,
    RefreshButton
  }
}
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>