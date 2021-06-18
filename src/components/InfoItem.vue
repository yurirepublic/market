<template>
  <div class='d-flex justify-content-between align-items-center'>
    <div>
      <span class='small' :class='{"text-muted": mutedHeader}'>{{ header }}</span>
    </div>
    <div>
      <span class='text-monospace'><slot></slot></span>
      <span class='text-monospace small ml-2' :class='{"text-muted": mutedFooter}' v-if='footer !== ""'>{{ footer }}</span>
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