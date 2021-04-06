<template>
  <div class="d-flex justify-content-center p-1">
    <div class="d-flex justify-content-center">
      <div class="">
        <div class="">
          <PremiumTable @click="clickTable" />
        </div>

        <div class="mt-1" style="width: 26rem">
          <PremiumCreator :pair-symbol="pairSymbol" />
        </div>
      </div>

      <div class="ml-1" style="max-width: 20rem">
        <div>
          <PremiumHistory :pair-symbol="pairSymbol" />
        </div>

        <div class="mt-1">
          <Wallet />
        </div>

        <div class="mt-1">
          <BNBWallet />
        </div>
      </div>

      <div class="ml-1">
        <div>
          <PremiumHaving @click="clickTable" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import PremiumTable from "@/components/PremiumTable.vue";
import PremiumHaving from "@/components/PremiumHaving.vue";
import Wallet from "@/components/Wallet.vue";
import PremiumCreator from "@/components/PremiumCreator.vue";
import BNBWallet from "@/components/BNBWallet.vue";
import PremiumHistory from "@/components/PremiumHistory.vue";

export default {
  name: "premium",
  data: function () {
    return {
      pairSymbol: '', // 被选中的符号
    };
  },
  methods: {
    clickTable(event) {
      this.pairSymbol = event
    },
  },
  created: function () {

  },
  mounted: function () {},
  components: {
    PremiumTable,
    PremiumHaving,
    Wallet,
    PremiumCreator,
    BNBWallet,
    PremiumHistory,
  },
};
</script>

<style scoped>
</style>