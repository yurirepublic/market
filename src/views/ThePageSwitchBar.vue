<template>
  <div class='d-flex flex-column' style='background-color: #e1e1e1'>
    <div v-for='page in pages' :key='page.name' @click="$emit('click', page.name)">
      <div class='pl-1' :class="focusPage === page.name? 'focus-line': 'normal-line'" />
      <div class='py-3 pl-2 pr-3'>
        <v-icon :name='page.icon' scale='2' :fill="focusPage === page.name ? focusColor : normalColor" />
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FuncSwitchBar',
  props: {
    pages: {
      type: Array,
      default: []
    },
    focusPage: {
      type: String,
      default: ''
    }
  },
  data: function() {
    return {
      focusColor: '#505050',
      normalColor: '#808080'
    }
  },
  methods: {}
}
</script>

<style scoped>
.focus-line {
  background-color: #505050;
}

.normal-line {
  background-color: #e1e1e1;
}
</style>