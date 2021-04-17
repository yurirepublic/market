<template>
  <div class='d-flex justify-content-center p-1'>
    <div class='d-flex'>

      <card-frame>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>运行中的脚本</span>
          <refresh-button :anime='loading' @click='Refresh' />
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
              :key="item['thread_id']"
              @click='ShowFocusLog(item)'
            >
              <td class='align-middle'>
                {{ item['thread_id'] }}
              </td>
              <td class='align-middle'>
                {{ item['name'] }}
              </td>
              <td class='align-middle'>
                {{ item['status'] }}
              </td>
              <td>
                <button
                  class='btn btn-secondary btn-sm'
                  type='button'
                  @click='StopScript(item)'
                  @click.stop
                  :disabled='loading'
                >
                  终止
                </button>
              </td>
            </tr>
            </tbody>
          </table>
        </div>


      </card-frame>

      <card-frame class='ml-1' v-if='loadingThreadId !== null'>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>脚本Log</span>
          <div class='d-flex'>
            <span>线程{{ loadingThreadId }}</span>
            <refresh-button :anime='loadingLog' @click='RefreshLog' />
          </div>
        </div>

        <div style='width: 40rem'>
          <div v-if='loadingLog'>
            <v-icon name='ri-loader-4-line' animation='spin'></v-icon>
            <span>正在加载线程 {{ loadingThreadId }} 的Log</span>
          </div>
          <div v-if='!loadingLog'>
            <pre>{{ focus_log }}</pre>
          </div>
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

      loading: false,

      loadingLog: false,
      loadingThreadId: null,

      focus_log: '' // 选中脚本的log
    }
  },
  mounted: function() {
    this.Refresh()
  },
  methods: {
    Refresh: async function() {
      this.loading = true
      try {
        let res = await this.apiRequest('running_script', [])
        this.running_script_list = res.data
        this.showToast.success('运行中的脚本列表获取成功')
      } catch {
        this.showToast.error('运行中的脚本列表获取失败')
      } finally {
        this.loading = false
      }
    },
    RefreshLog: async function() {
      this.loadingLog = true
      try {
        let res = await this.apiRequest('script_log', [this.loadingThreadId])
        this.focus_log = res.data
        this.showToast.success('获取选中脚本log成功')
      } catch {
        this.showToast.error('获取选中脚本log失败')
      } finally {
        this.loadingLog = false
      }
    },
    StopScript: async function(item) {
      this.loading = true
      try {
        await this.apiRequest('stop_script', [item['thread_id']])
        this.showToast.success('脚本终止成功')
      } catch {
        this.showToast.error('脚本终止失败')
      } finally {
        // 无论如何都要调用Refresh重加载
        await this.Refresh()
      }
    },
    ShowFocusLog: async function(item) {
      console.log('选中脚本线程号', item['thread_id'])
      this.loadingThreadId = item['thread_id']
      await this.RefreshLog()
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