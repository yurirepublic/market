<template>
  <button
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
  border-radius: 5px;
  border-style: none;
  color: #000;
}

button:hover {
  background-color: #ddd;
}
</style>