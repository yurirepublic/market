<template>
  <div class='p-2 card-background'>
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'CardFrame'
}
</script>

<style scoped>
.card-background {
  background-color: #fafafa;
}
</style>