import script_manager
import binance_api
import data_center
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
        self.operator = await binance_api.create_operator()
        self.dc = await data_center.create_client_adapter()

        while True:
            # 获取每个 现货 交易对的规则（下单精度）
            info = await self.operator.request('api', '/api/v3/exchangeInfo', 'GET', {}, send_signature=False)
            server_time = info['serverTime']
            info = info['symbols']
            for e in info:
                symbol = e['symbol']
                quote_precision = e['quotePrecision']
                asyncio.create_task(
                    self.dc.update({'precision', 'quote', 'main', symbol}, quote_precision, server_time))

            # 获取每个 期货 交易对的规则（下单精度）
            info = await self.operator.request('fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False)
            server_time = info['serverTime']
            info = info['symbols']
            for e in info:
                symbol = e['symbol']
                quote_precision = e['quantityPrecision']
                asyncio.create_task(
                    self.dc.update({'precision', 'quote', 'future', symbol}, quote_precision, server_time))

                # 获取这个symbol的历史100次资金费率
                history = await self.operator.request('fapi', '/fapi/v1/fundingRate', 'GET', {
                    'symbol': symbol
                })
                rate = [float(x['fundingRate']) for x in history]
                asyncio.create_task(self.dc.update({'premium', 'fundingRateHistory', symbol}, rate))

            await asyncio.sleep(3600)
