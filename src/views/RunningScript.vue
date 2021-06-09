<template>
  <div class='d-flex justify-content-center p-1'>
    <div class='d-flex'>

      <card-frame>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>运行中的脚本</span>
        </div>
        <div class='d-flex justify-content-between align-content-center'>
          <span class='small'>选择服务器</span>
          <my-radio :options='radioOptions' :active='radioActive' @click='radioActive=$event' />
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
              v-for='(value, name) in scriptStatusDict[radioActive]'
              :key="value['thread_id']"
              @click='ShowFocusLog(value)'
            >
              <td class='align-middle'>
                {{ value['thread_id'] }}
              </td>
              <td class='align-middle'>
                {{ value['name'] }}
              </td>
              <td class='align-middle'>
                {{ value['status'] }}
              </td>
              <td>
                <button
                  class='btn btn-secondary btn-sm'
                  type='button'
                  @click='StopScript(value)'
                  @click.stop
                  :disabled='waiting'
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
            <pre>{{ focusLog }}</pre>
          </div>
        </div>
      </card-frame>

    </div>
  </div>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import RefreshButton from '@/components/RefreshButton'
import MyRadio from '@/components/MyRadio'

export default {
  name: 'RunningScript',
  components: {
    CardFrame,
    RefreshButton,
    MyRadio
  },
  data: function() {
    return {
      scriptStatusDict: {},

      radioOptions: [],
      radioActive: '',

      apiUrl: {},   // key是nickname， value是可以直接访问的url

      waiting: false,   // 正在等待回复

      loadingLog: false,    // 正在加载log
      loadingThreadId: null,    // 正在加载线程ID

      focusLog: '', // 选中脚本的log
      focusUrl: '', // 当前选中服务器的的url，包含ip和端口，可直接访问

      ws: null,
      subscribe: null
    }
  },
  watch: {
    radioActive: function(newVal) {
      this.focusUrl = this.apiUrl[newVal]
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()
    this.subscribe = await this.connectSubscribe()

    // 获取服务器和端口
    let ip = await this.ws.getDict(['server', 'info', 'ip'])
    this.radioOptions = Object.keys(ip)

    for (const nickname of Object.keys(ip)) {
      let port = await this.ws.getDict(['server', 'info', 'port', nickname])
      // 生成url
      this.apiUrl[nickname] = 'https://' + ip[nickname] + ':' + port['api']
    }

    this.radioActive = this.radioOptions[0]

    // 根据当前已有的服务器，订阅脚本运行状态
    for (const nickname of this.radioOptions) {
      await this.subscribe.precise(['json', 'scriptManager', 'status', nickname], msg => {
        this.$set(this.scriptStatusDict, nickname, JSON.parse(msg['data']))
      }, true)
    }

  },
  methods: {
    RefreshLog: async function() {
      this.loadingLog = true
      try {
        let res = await this.apiRequest('script_log', [this.loadingThreadId], this.focusUrl)
        this.focusLog = res.data
        this.showToast.success('获取选中脚本log成功')
      } catch {
        this.showToast.error('获取选中脚本log失败')
      } finally {
        this.loadingLog = false
      }
    },
    StopScript: async function(item) {
      this.waiting = true
      try {
        await this.apiRequest('stop_script', [item['thread_id']], this.focusUrl)
        this.showToast.success('脚本终止成功')
      } catch {
        this.showToast.error('脚本终止失败')
      } finally {
        this.waiting = false
      }
    },
    ShowFocusLog: async function(item) {
      console.log('选中脚本线程号', item['thread_id'])
      this.loadingThreadId = item['thread_id']
      await this.RefreshLog()
    }
  }
}
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>