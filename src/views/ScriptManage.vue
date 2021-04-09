<template>
  <div class='p-1 d-flex justify-content-center'>
    <div>
      <card-frame style='max-height: 100%'>
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>脚本列表</span>
          <refresh-button :anime='refresh_button_anime' @click='Refresh' />
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
              v-for='item in script_list'
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
      <card-frame style='max-height: 100%' v-if="focus_item != ''">
        <div class='mb-2 d-flex justify-content-between align-items-center'>
          <span class='font-weight-bold'>自定义脚本输入</span>
        </div>
        <div>
          <pre>标题: {{ focus_item['title'] }}</pre>
          <pre>描述: {{ focus_item['description'] }}</pre>
          <trade-input
            class='mt-1'
            v-for="item in focus_item['inputs']"
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
            @click='RunScript(focus_item)'
            @click.stop
            :disabled='button_disabled'
          >
            开始运行
          </button>
        </div>
      </card-frame>
    </div>
  </div>
</template>

<script>
import CardFrame from '@/components/CardFrame.vue'
import RefreshButton from '@/components/RefreshButton.vue'
import TradeInput from '@/components/TradeInput.vue'
import InfoItem from '@/components/InfoItem.vue'

export default {
  name: 'ScriptManage',
  data: function() {
    return {
      script_list: [],
      button_disabled: false,
      refresh_button_anime: false,
      focus_item: {}
    }
  },
  mounted: function() {
    this.Refresh()
  },
  methods: {
    Refresh: function() {
      this.refresh_button_anime = true
      this.apiRequest('script_list', [])
        .then((res) => {
          this.showToast.success('脚本列表获取成功')
          this.script_list = res.data
        })
        .catch((err) => {
          this.showToast.error('脚本列表获取失败')
        })
        .finally(() => {
          this.refresh_button_anime = false
        })
    },
    RunScript: function(item) {
      console.log('将要运行', item)
      // 将用户的输入提取成字典
      let input_dict = {}
      this.focus_item['inputs'].forEach((e) => {
        input_dict[e['var_name']] = e['default']
      })
      // 发送请求
      this.button_disabled = true
      this.apiRequest('run_script', [item['file_name'], input_dict])
        .then((res) => {
          this.showToast.success('脚本运行成功')
        })
        .catch((err) => {
          this.showToast.error('脚本运行失败')
        })
        .finally(() => {
          this.button_disabled = false
        })
    },
    ClickScript: function(item) {
      this.focus_item = item
    },
    InputScriptOption: function(item) {
      console.log(item)
    }
  },
  components: {
    CardFrame,
    RefreshButton,
    TradeInput,
    InfoItem
  }
}
</script>

<style scoped></style>
