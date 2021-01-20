<template>
  <button
    class="btn btn-light btn-sm float-right"
    type="button"
    @click="$emit('click', '$event')"
    :disabled="disabled"
  >
    <b-icon icon="arrow-counterclockwise" :animation="animation"></b-icon>
  </button>
</template>

<script>
export default {
  props: {
    anime: false,
  },

  data: function () {
    return {
      amine: false,
      animation: "",
      disabled: false
    };
  },

  watch: {
    anime: function (newValue, oldValue) {
      if (newValue == true) {
        this.animation = "spin-reverse";
        this.disabled = true;
      } else {
        this.animation = "";
        this.disabled = false;
      }
    },
  },
};
</script>

<style scoped>
button {
  background-color: transparent;
  border: none;
}
button:hover {
  background-color: transparent;
  border-color: transparent;
}
button:focus {
  background-color: transparent;
  border-color: transparent;
  box-shadow: none;
}
button:not(:disabled):not(.disabled):active:focus {
  box-shadow: none;
}
</style>