import script_manager
import binance
import datacenter
import json
import time
import asyncio


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '接收交易所的静态数据'
        info.description = """
        静态数据不需要频繁更新
        所以此脚本放置的都是诸如交易规则、下单精度之类的数据
        一般1小时更新一次
        """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._main())
        loop.run_forever()

    async def _main(self):
        self.binance = await binance.create_operator()
        self.client = await datacenter.create_client()

        while True:
            # 获取每个 现货 交易对的规则（下单精度、全仓逐仓支持情况）
            info = await self.binance.request('api', '/api/v3/exchangeInfo', 'GET', {}, send_signature=False)
            server_time = info['serverTime']
            info = info['symbols']
            for e in info:
                symbol = e['symbol']
                quote_precision = e['quotePrecision']
                asyncio.create_task(
                    self.client.update({'precision', 'quote', 'main', symbol}, quote_precision, server_time))

            # 查询所有全仓交易对
            info = await self.binance.request('api', '/sapi/v1/margin/allPairs', 'GET', {})
            for e in info:
                # 只保留quote是USDT的交易对
                if e['quote'] != 'USDT':
                    continue

                base = e['base']
                if e['isBuyAllowed'] and e['isMarginTrade'] and e['isSellAllowed']:
                    asyncio.create_task(self.client.update({'allow', 'margin', base + 'USDT'}, True))
                else:
                    asyncio.create_task(self.client.update({'allow', 'margin', base + 'USDT'}, False))

            # 查询所有逐仓交易对
            info = await self.binance.request('api', '/sapi/v1/margin/isolated/allPairs', 'GET', {},
                                              auto_timestamp=True)
            for e in info:
                # 只保留quote是USDT的交易对
                if e['quote'] != 'USDT':
                    continue

                base = e['base']
                if e['isBuyAllowed'] and e['isMarginTrade'] and e['isSellAllowed']:
                    asyncio.create_task(self.client.update({'allow', 'isolated', base + 'USDT'}, True))
                else:
                    asyncio.create_task(self.client.update({'allow', 'isolated', base + 'USDT'}, False))

            # 获取每个 期货 交易对的规则（下单精度）
            info = await self.binance.request('fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False)
            server_time = info['serverTime']
            info = info['symbols']
            for e in info:
                symbol = e['symbol']
                quote_precision = e['quantityPrecision']
                asyncio.create_task(
                    self.client.update({'precision', 'quote', 'future', symbol}, quote_precision, server_time))

                # 获取这个symbol的历史100次资金费率
                history = await self.binance.request('fapi', '/fapi/v1/fundingRate', 'GET', {
                    'symbol': symbol
                })
                rate = [float(x['fundingRate']) for x in history]
                funding_time = [int(x['fundingTime']) for x in history]
                asyncio.create_task(self.client.update({'premium', 'fundingRateHistory', symbol}, rate))
                asyncio.create_task(
                    self.client.update({'premium', 'fundingRateHistory', 'timestamp', symbol}, funding_time))

            # 获取收取的资金费率流水
            res = await self.binance.request('fapi', '/fapi/v1/income', 'GET', {
                'limit': str(1000),
                'incomeType': 'FUNDING_FEE',
                'startTime': str(int(binance.get_timestamp()) - 3600 * 24 * 30 * 1000)
            }, auto_timestamp=True)
            asyncio.create_task(self.client.update({'json', 'fundingFee'}, res))

            await asyncio.sleep(3600)
