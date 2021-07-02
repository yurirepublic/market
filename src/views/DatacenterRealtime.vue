<template>
  <div class='p-1'>
    <card-frame>
      <div class='mb-2 d-flex justify-content-between align-items-center'>
        <span class='font-weight-bold'>数据中心全局展示</span>
        <refresh-button :anime='loading' @click='Refresh' />
      </div>
      <span>总共找到：{{ count }}个条目</span>
      <!--      <div v-for='(item, index) in data'>{{ item['tags'] }} {{ item['data'] }}</div>-->

    </card-frame>
  </div>
</template>

<script>
import RefreshButton from '@/components/RefreshButton'
import CardFrame from '@/components/CardFrame'

export default {
  name: 'DatacenterRealtime',
  components: {
    RefreshButton,
    CardFrame
  },

  data: function() {
    return {
      data: {},
      count: 0,   // 总条目数

      loading: false,

      ws: null
    }
  },

  mounted: async function() {
    this.ws = await this.connectDataCenter()

  },
  methods: {
    PutData: function(obj, count) {
      // 对obj的tag根据count正确排序
      obj['tags'].sort((a, b) => {
        if (count[a] < count[b]) {
          return 1
        } else {
          return -1
        }
      })
      // 逐位塞入树状图的data
      let path = this.data
      for (let i = 0; i < obj['tags'].length; i++) {
        let tag = obj['tags'][i]
        if (path[tag] === undefined) {
          path[tag] = {}
        }
        if (i === obj['tags'].length - 1) {
          // 是最后一个tag就写数据了
          path[tag] = obj['data']
        } else {
          path = path[tag]
        }
      }
    },
    Refresh: async function() {
      this.loading = true
      // 获取所有数据
      let msg = await this.ws.getAll()
      console.log('数据中心所有数据', msg)
      this.count = msg.length
      // 数据拿到后统计所有tag的出现次数，并且排序
      let count = {}
      for (let i = 0; i < msg.length; i++) {
        let item = msg[i]
        for (let x = 0; x < item['tags'].length; x++) {
          let tag = item['tags'][x]
          if (count[tag] === undefined) {
            count[tag] = 1
          } else {
            count[tag] += 1
          }
        }
      }
      console.log('数据中心tag出现次数', count)
      // 每个条目根据自己的tag大小放入data的树状结构
      for (let i = 0; i < msg.length; i++) {
        let item = msg[i]
        this.PutData(item, count)
      }
      console.log(this.data)
      this.$forceUpdate()
      this.loading = false
    }
  }
}
</script>

<style scoped>

</style>