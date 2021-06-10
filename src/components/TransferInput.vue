<template>
  <div class='card' style='background-color: #f0f1f2'>
    <div class='d-flex justify-content-between'>
      <input
        class='p-2 text-left flex-shrink-1'
        :type='type'
        :placeholder='placeholder'
        :value='value'
        @input="$emit('input', $event.target.value)"
      />
      <div class='d-flex'>
        <button
          class='d-flex align-items-center'
          type='button'
          :disabled='disabled'
          @click.stop="$emit('click', 'confirm')"
        >
          <v-icon class='mx-1' name='ri-checkbox-circle-line'></v-icon>
        </button>
        <button
          class='d-flex align-items-center'
          type='button'
          :disabled='disabled'
          @click.stop="$emit('click', 'cancel')"
        >
          <v-icon class='mx-1' name='ri-close-circle-line'></v-icon>
        </button>
      </div>

    </div>
  </div>
</template>

<script>
export default {
  name: 'TransferInput',
  props: {
    placeholder: {
      type: String,
      default: ''
    },
    type: {
      type: String,
      default: 'text'
    },
    disabled: false,
    value: ''
  },
  data: function() {
    return {}
  }
}
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

input {
  font-family: 'JetBrains Mono';
  border: none;
  background: transparent;
  width: 100%;
}

input:focus {
  outline: none;
}

button {
  border-radius: 5px;
  border-style: none;
  color: #000;
}

button:hover {
  background-color: #ddd;
}

button:disabled {
  color: #888;
}
</style>