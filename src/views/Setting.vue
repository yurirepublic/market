<template>
  <div class='p-1'>
    <card-frame style='min-width: 30rem'>
      <div class='mb-2'>
        <span class='font-weight-bold'>网络连接设置</span>
      </div>
      <div>
        <trade-input
          header='服务器地址'
          placeholder=''
          v-model='serverUrl'
        ></trade-input>
        <trade-input
          class='mt-1'
          header='服务器口令'
          placeholder=''
          v-model='password'
          type='password'
        ></trade-input>
        <trade-input
          class='mt-1'
          header='数据中心接口'
          placeholder=''
          v-model='dataUrl'
        ></trade-input>
        <trade-input
          class='mt-1'
          header='数据订阅接口'
          placeholder=''
          v-model='subscribeUrl'
        ></trade-input>
        <button
          class='btn btn-primary mt-3 px-2'
          @click='Save'
          style='background-color: #02c076; border-color: transparent'
        >
          保存
        </button>
      </div>
    </card-frame>
  </div>
</template>

<script>
import CardFrame from '@/components/CardFrame.vue'
import TradeInput from '@/components/TradeInput.vue'

export default {
  name: 'Setting',
  data: function() {
    return {
      serverUrl: '',
      password: '',
      dataUrl: '',
      subscribeUrl: ''
    }
  },
  mounted: async function() {
    this.serverUrl = this.localConfig.serverUrl
    this.password = this.localConfig.password
    this.dataUrl = this.localConfig.dataUrl
    this.subscribeUrl = this.localConfig.subscribeUrl
  },
  methods: {
    Save: function() {
      try {
        this.localConfig.serverUrl = this.serverUrl
        this.localConfig.password = this.password
        this.localConfig.dataUrl = this.dataUrl
        this.localConfig.subscribeUrl = this.subscribeUrl
        this.showToast.success('成功保存设置')
      } catch (e) {
        this.showToast.error('保存设置失败')
      }
    }
  },
  components: {
    CardFrame,
    TradeInput
  }
}
</script>

<style scoped>
</style>