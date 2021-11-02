import script_manager
import datacenter
import json
import asyncio
import time


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '记录交易所的价格数据'
        info.description = """
        这个脚本会订阅数据中心一些数据，并且将数据原封不动写入到文件中
        """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._main())
        loop.run_forever()

    async def _main(self):
        self.client = await datacenter.create_client()
        await self.client.subscribe_dict({'premium', 'fundingRate'}, self.funding_rate)
        await self.client.subscribe_dict({'premium', 'rate'}, self.premium_rate)
        await self.client.subscribe_dict({'price', 'main'}, self.price_main)

    @staticmethod
    def write_data(msg, f):
        for key in msg.keys():
            obj = {
                't': round(time.time() * 1000),
                's': key,
                'd': msg[key]
            }
            obj = json.dumps(obj)
            f.write(obj + '\n')

    async def funding_rate(self, msg):
        with open('database_funding_rate.txt', 'a+', encoding='utf-8') as f:
            self.write_data(msg, f)

    async def premium_rate(self, msg):
        with open('database_premium_rate.txt', 'a+', encoding='utf-8') as f:
            self.write_data(msg, f)

    async def price_main(self, msg):
        with open('database_price_main.txt', 'a+', encoding='utf-8') as f:
            self.write_data(msg, f)
