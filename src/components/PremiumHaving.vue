<template>
  <div style="overflow: auto; max-height: 20rem; background-color: #fafafa">
    <table class="table table-hover small">
      <thead>
        <tr>
          <th>交易对</th>
          <th>仓位</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(item, index) in havingItems"
          :key="item['symbol']"
          @click="premiumClickAction(item[index])"
        >
          <td class="text-monospace align-middle">
            {{ item["symbol"] }}
          </td>
          <td class="text-monospace align-middle">
            {{ item["quantity"] }}
          </td>
          <td>
            <button
              class="btn btn-secondary"
              type="button"
              @click="premiumDestoryClick(item['symbol'], item['quantity'])"
              @click.stop
            >
              平仓
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: PremiumHaving,
  data: function () {
    return {

    }
  },
  
}
</script>