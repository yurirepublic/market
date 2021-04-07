<template>
  <button
    class='btn btn-light btn-sm float-right'
    type='button'
    @click="$emit('click', '$event')"
    :disabled='disabled'
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'NoBorderButton',
  props: {
    disabled: {
      type: Boolean,
      default: false
    }
  }
}
</script>

<style scoped>
button {
  border: none;
}

button:hover {
  border: none;
}

button:focus {
  border: none;
  box-shadow: none;
}

button:not(:disabled):not(.disabled):active:focus {
  box-shadow: none;
}

</style>