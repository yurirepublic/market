<template>
  <div class='p-1 d-flex justify-content-center'>
    <div>
      <card-frame style='width: 15rem'>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>脚本列表</span>
          <refresh-button :anime='isLoading' @click='Refresh' />
        </div>
        <div class='d-flex justify-content-between align-content-center'>
          <span class='small'>选择服务器</span>
          <my-radio :options='radioOptions' :active='radioActive' @click='radioActive=$event' />
        </div>
        <div style='overflow: auto; max-height: 30rem'>
          <table class='table table-hover table-borderless table-sm small'>
            <thead>
            <tr class='text-muted'>
              <th class='font-weight-normal'>脚本名</th>
            </tr>
            </thead>
            <tbody>
            <tr
              v-for='item in scriptList'
              :key="item['file_name']"
              @click='ClickScript(item)'
            >
              <td class='align-middle'>
                {{ item['file_name'] }}
              </td>
              <td></td>
            </tr>
            </tbody>
          </table>
        </div>
      </card-frame>
    </div>
    <div class='ml-1'>
      <card-frame style='max-height: 100%' v-if='focusItem !== null'>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>自定义脚本输入</span>
        </div>
        <div>
          <pre>标题: {{ focusItem['title'] }}</pre>
          <pre>描述: {{ focusItem['description'] }}</pre>
          <trade-input
            class='mt-1'
            v-for="item in focusItem['inputs']"
            :key="item['file_name']"
            :header="item['show_text']"
            :value="item['default']"
            v-model="item['default']"
          />
        </div>
        <div>
          <button
            class='btn btn-secondary btn-sm mt-2'
            type='button'
            @click='RunScript(focusItem)'
            @click.stop
            :disabled='isRunningRequest'
          >
            开始运行
          </button>
        </div>
      </card-frame>
    </div>
  </div>
</template>

<script>
import CardFrame from '@/components/CardFrame'
import RefreshButton from '@/components/RefreshButton'
import TradeInput from '@/components/TradeInput'
import InfoItem from '@/components/InfoItem'
import MyRadio from '@/components/MyRadio'

export default {
  name: 'ScriptManage',
  components: {
    CardFrame,
    RefreshButton,
    TradeInput,
    InfoItem,
    MyRadio
  },
  data: function() {
    return {
      scriptList: [],

      isLoading: false,
      isRunningRequest: false,

      focusItem: null,

      radioOptions: [],
      radioActive: '',

      apiUrl: {},   // key是nickname， value是可以直接访问的url

      focusLog: '', // 选中脚本的log
      focusUrl: '', // 当前选中服务器的的url，包含ip和端口，可直接访问

      ws: null
    }
  },
  watch: {
    radioActive: function(newVal) {
      this.focusUrl = this.apiUrl[newVal]
      this.focusItem = null
      this.scriptList = []
      this.Refresh()
    }
  },
  mounted: async function() {
    this.ws = await this.connectDataCenter()

    let ip = await this.ws.getDict(['server', 'info', 'ip'])
    this.radioOptions = Object.keys(ip)

    for (const nickname of Object.keys(ip)) {
      let port = await this.ws.getDict(['server', 'info', 'port', nickname])
      // 生成url
      this.apiUrl[nickname] = 'https://' + ip[nickname] + ':' + port['api']
    }

    this.radioActive = this.radioOptions[0]
  },
  methods: {
    Refresh: async function() {
      this.isLoading = true
      try {
        let res = await this.apiRequest('script_list', [], this.focusUrl)
        this.showToast.success('脚本列表获取成功')
        this.scriptList = res.data
      } catch {
        this.showToast.error('脚本列表获取失败')
      } finally {
        this.isLoading = false
      }
    },
    RunScript: async function(item) {
      console.log('将要运行', item)
      // 将用户的输入提取成字典
      let inputDict = {}
      for (const e of this.focusItem['inputs']) {
        inputDict[e['var_name']] = e['default']
      }
      // 发送请求
      this.isRunningRequest = true
      try {
        await this.apiRequest('run_script', [item['file_name'], inputDict], this.focusUrl)
        this.showToast.success('脚本运行成功')
      } catch {
        this.showToast.error('脚本运行失败')
      } finally {
        this.isRunningRequest = false
      }
    },
    ClickScript: function(item) {
      this.focusItem = item
    }
  }
}
</script>

<style scoped></style>
