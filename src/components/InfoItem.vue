<template>
  <div class=''>
    <div class='d-flex justify-content-between'>
      <div class='flex-shrink-0'>
        <span class='small' :class='{"text-muted": mutedHeader}'>{{ header }}</span>
      </div>
      <div>
        <span class='text-monospace ml-3'><slot></slot></span>
        <span class='text-monospace small ml-2' :class='{"text-muted": mutedFooter}'>{{ footer }}</span>
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
    },
    mutedHeader: {
      type: Boolean,
      default: false
    },
    mutedFooter: {
      type: Boolean,
      default: true
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