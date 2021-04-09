<template>
  <button
    class='btn btn-light btn-sm float-right'
    type='button'
    @click="$emit('click', '$event')"
    :disabled='disabled'
  >
    <v-icon name='ri-refresh-line' :animation='animation'></v-icon>
  </button>
</template>

<script>
export default {
  name: 'RefreshButton',

  props: {
    anime: {
      type: Boolean,
      default: false
    }
  },

  data: function() {
    return {
      animation: null,
      disabled: false
    }
  },

  watch: {
    anime: function(newValue, oldValue) {
      if (newValue === true) {
        this.animation = 'spin'
        this.disabled = true
      } else {
        this.animation = null
        this.disabled = false
      }
    }
  }
}
</script>

<style scoped>
button {
  background-color: transparent;
  border: none;
}

button:hover {
  background-color: transparent;
  border: none;
}

button:focus {
  background-color: transparent;
  border: none;
  box-shadow: none;
}

button:not(:disabled):not(.disabled):active:focus {
  box-shadow: none;
}
</style>