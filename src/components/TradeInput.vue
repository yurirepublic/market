<template>
  <div class='card p-2' style='background-color: #f0f1f2'>
    <div class='d-flex justify-content-around'>
      <div class='d-flex align-items-center mr-2' v-if="header !== ''">
        <span class='text-muted no-wrap'>{{ header }}</span>
      </div>

      <input
        class='text-right'
        :type='type'
        :placeholder='placeholder'
        :value='value'
        @input="$emit('input', $event.target.value)"
        :disabled='disabled'
      />
      <div class='d-flex align-items-center ml-2' v-if="footer !== ''">
        <span class='text-muted no-wrap'>{{ footer }}</span>
      </div>

    </div>

  </div>
</template>

<script>
export default {
  name: 'TradeInput',
  props: {
    header: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: ''
    },
    footer: {
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

.no-wrap {
  white-space: nowrap;
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