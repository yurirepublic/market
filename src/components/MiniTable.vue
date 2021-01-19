<template>
  <div>
    <div>
      <span v-for="column_name in columns" :key="column_name">{{column_name}}</span>
    </div>
    <div>
      <div v-for="item in items" :key="item[name]">
        <span v-for="name in columns" :key="name">{{item[name]}}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "MiniTable",
  props: {
    columns: {
      type: Array,
      default: [],
    },
    items: {
      type: Array,
      defalut: [],
    },
  },
  data: function () {
    return {};
  },
  methods: {

  }
};
</script>

<style scoped>

</style>