<template>

</template>

<script>
export default {
  name: "PremiumHistory",

  data: function () {

  },

  mounted: function () {
    this.request_method("premium_history", "ZENUSDT")    
  }
};
</script>

<style scoped>

</style>