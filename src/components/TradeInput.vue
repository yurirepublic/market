<template>
  <div class='card' style='background-color: #f0f1f2'>
    <div class='input-group'>
      <span v-if="header !== ''" class='input-group-text text-muted'>{{ header }}</span>
      <input
        class='form-control text-right'
        :type='type'
        :placeholder='placeholder'
        :value='value'
        @input="$emit('input', $event.target.value)"
        :disabled='disabled'
      />
      <span v-if="footer !== ''" class='input-group-text text-muted'>{{ footer }}</span>
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
  border-color: transparent;
  box-shadow: none;
  background-color: transparent;
}
</style>