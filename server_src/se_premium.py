"""
获取配对的现货与期货价格，并计算溢价
"""
import data_center
import script_manager
import asyncio


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '从数据中心订阅想要的数据，并计算后放回'
        info.description = """
        目前托管到此脚本的项目有：
        期货现货溢价计算
        """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._main())
        loop.run_forever()

    async def _main(self):
        # 订阅期货和现货价格
        self.subscribe = await data_center.create_subscribe()
        await self.subscribe.subscribe_dict({'price', 'main'}, self.calc_premium)
        await self.subscribe.subscribe_dict({'price', 'future'}, self.calc_premium)
        self.client = await data_center.create_client_adapter()

    async def calc_premium(self, msg):
        # 获取交易符号
        symbol = msg['special']
        # 获取双方价格
        price = await self.client.get_dict({'price', symbol})
        # 如果有一方数据缺失直接返回
        keys = price.keys()
        if 'main' not in keys or 'future' not in keys:
            return

        main_price = price['main']
        future_price = price['future']
        # 计算溢价并且放回去
        premium_price = future_price / main_price - 1
        asyncio.create_task(self.client.update({'premium', 'rate', symbol}, premium_price))
        # asyncio.create_task(self.client.update({'premium', 'dif', symbol}, future_price - main_price))
