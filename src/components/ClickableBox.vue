<template>
  <button
    class="btn btn-light btn-sm float-right"
    type="button"
    @click="$emit('click', '$event')"
    :disabled="disabled"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: "ClickableBox",

  props: {
    name: "",
  },

  data: function () {
    return {
      amine: false,
      animation: "",
      disabled: false,
    };
  },

  watch: {
    // anime: function (newValue, oldValue) {
    //   if (newValue == true) {
    //     this.animation = "spin-reverse";
    //     this.disabled = true;
    //   } else {
    //     this.animation = "";
    //     this.disabled = false;
    //   }
    // },
  },

  components: {},
};
</script>

<style scoped>
button {
  background-color: transparent;
  border: none;
}
button:active {
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