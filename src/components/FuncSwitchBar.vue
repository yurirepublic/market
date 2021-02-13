<template>
  <div class="d-flex flex-column" style="background-color: #e1e1e1">
    <div class="d-flex" @click="$emit('click', 'premium')">
      <div
        class="pl-1"
        :class="focus_page == 'premium' ? 'focus-line' : 'normal-line'"
      ></div>
      <div class="py-3 pl-2 pr-3">
        <v-icon
          name="ri-coins-line"
          scale="2"
          :fill="focus_page == 'premium' ? focus_color : normal_color"
        ></v-icon>
      </div>
    </div>

    <div class="d-flex" @click="$emit('click', 'history')">
      <div
        class="pl-1"
        :class="focus_page == 'history' ? 'focus-line' : 'normal-line'"
      ></div>
      <div class="py-3 pl-2 pr-3">
        <v-icon
          name="ri-history-line"
          scale="2"
          :fill="focus_page == 'history' ? focus_color : normal_color"
        ></v-icon>
      </div>
    </div>

    <div class="d-flex" @click="$emit('click', 'running_script')">
      <div
        class="pl-1"
        :class="focus_page == 'running_script' ? 'focus-line' : 'normal-line'"
      ></div>
      <div class="py-3 pl-2 pr-3">
        <v-icon
          name="bi-file-earmark-play"
          scale="2"
          :fill="focus_page == 'running_script' ? focus_color : normal_color"
        ></v-icon>
      </div>
    </div>

    <div class="d-flex" @click="$emit('click', 'script_manage')">
      <div
        class="pl-1"
        :class="focus_page == 'script_manage' ? 'focus-line' : 'normal-line'"
      ></div>
      <div class="py-3 pl-2 pr-3">
        <v-icon
          name="bi-file-earmark-code"
          scale="2"
          :fill="focus_page == 'script_manage' ? focus_color : normal_color"
        ></v-icon>
      </div>
    </div>

    <div class="d-flex" @click="$emit('click', 'setting')">
      <div
        class="pl-1"
        :class="focus_page == 'setting' ? 'focus-line' : 'normal-line'"
      ></div>
      <div class="py-3 pl-2 pr-3">
        <v-icon
          name="ri-settings-4-line"
          scale="2"
          :fill="focus_page == 'setting' ? focus_color : normal_color"
        ></v-icon>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "FuncSwitchBar",
  props: {
    focus_page: {
      type: String,
      default: "premium",
    },
  },
  data: function () {
    return {
      focus_color: "#505050",
      normal_color: "#808080",
    };
  },
  methods: {},
};
</script>

<style scoped>
.focus-line {
  background-color: #505050;
}
.normal-line {
  background-color: #e1e1e1;
}
</style>