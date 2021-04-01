<template>
  <button
    class="float-right"
    type="button"
    @click="$emit('click', '$event')"
    :disabled="disabled"
  >
    <v-icon :name="name"></v-icon>
  </button>
</template>

<script>
export default {
  name: "ClickableIcon",

  props: {
    name: {
      type: String,
      default: ''
    }
  },

  data: function () {
    return {
      amine: false,
      animation: "",
      disabled: false,
    };
  },

  components: {},
};
</script>

<style scoped>
button {
  border-radius: 5px;
  border-style: none;
  color: #000;
}
</style>