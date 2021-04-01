<template>
  <div class="card" style="background-color: #f0f1f2">
    <div class="input-group">
      <input
        class="form-control text-right"
        :type="type"
        :placeholder="placeholder"
        :value="value"
        @input="$emit('input', $event.target.value)"
      />
      <div class="input-group-append">
        <button
          class="btn btn-light d-flex align-items-center"
          type="button"
          :disabled="disabled"
          @click.stop="$emit('click', $event)"
        >
            <slot></slot>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "TransferInput",
  props: {
    placeholder: {
      type: String,
      default: "",
    },
    type: {
      type: String,
      default: "text",
    },
    disabled: false,
    value: "",
  },
  data: function () {
    return {};
  },
};
</script>

<style scoped>
@font-face {
  font-family: "JetBrainsMono";
  src: url("../assets/JetBrainsMonoNL-Regular.ttf");
}

.card {
  border: none;
  border-radius: 0.5rem;
}

.input-group-text {
  border: 0;
  background-color: transparent;
}

.form-control {
  border: 0;
  box-shadow: none;
  background-color: transparent;
  font-family: "JetBrainsMono";
}

.form-control:disabled {
  background-color: transparent;
}

.form-control:focus {
  border-color: none;
  box-shadow: none;
  background-color: transparent;
}

button {
  background-color: transparent;
  border: none;
}
button:active {
  border: none;
}
button:hover {
  border: none;
}
button:focus {
  background-color: transparent;
  border: none;
  box-shadow: none;
}
button:not(:disabled):not(.disabled):active:focus {
  box-shadow: none;
  border: none;
}
</style>