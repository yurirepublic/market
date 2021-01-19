<template>
  <div class="d-flex justify-content-between align-items-center">
		<span class="text-muted small">{{ header }}</span>
    
    <div class="d-flex ml-3 align-items-center">
      <span class="text-monospace">{{ content }}</span>
      <span class="text-monospace small text-muted ml-2 align-text-bottom">{{ footer }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: "InfoItem",
  props: {
    header: {
      type: String,
      defalut: "",
    },
    content: {
      type: [String, Number],
      defalut: "",
    },
    footer: {
      type: String,
      defalut: "",
    },
  },
};
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