<template>
  <div class=''>
    <div class='d-flex justify-content-between'>
      <div class='flex-shrink-0'>
        <span class='text-muted small'>{{ header }}</span>
      </div>
      <div>
        <span class='text-monospace ml-3'><slot></slot></span>
        <span class='text-monospace small text-muted ml-2'>{{ footer }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InfoItem',
  props: {
    header: {
      type: String,
      default: ''
    },
    footer: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
@font-face {
  font-family: "JetBrainsMono";
  src: url("../assets/JetBrainsMonoNL-Regular.ttf");
}

.text-monospace {
  font-family: "JetBrainsMono";
}
</style>