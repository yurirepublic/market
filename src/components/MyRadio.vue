<template>
  <div>
    <button
      class='p-1 small'
      v-for='(option, index) in options'
      v-bind:class="{'isActive': active === option, 'mr-1': index !== options.length - 1}"
      @click.stop="active = option;$emit('click', option)"
    >
      {{ option }}
    </button>
  </div>
</template>

<script>
export default {
  name: 'Radio',
  props: {
    options: {
      type: Array,
      default: []
    },
    initActive: {
      type: null,
      default: ''
    }
  },
  data: function() {
    return {
      active: ''
    }
  },
  mounted: function() {
    if (this.initActive === '') {
      this.active = this.options[0]
    } else {
      this.active = this.initActive
    }

  }

}
</script>

<style scoped>
button {
  border-radius: 5px;
  border-style: none;
  background-color: #e1e1e1;
  color: #000;
}

.isActive {
  background-color: #505050;
  color: #fff;
}
</style>