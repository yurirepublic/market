"""
获取配对的现货与期货价格，并计算溢价
"""
import data_center
import script_manager
import asyncio
import copy


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '从数据中心订阅想要的数据，并计算后放回'
        info.description = """
        目前托管到此脚本的项目有：
        期货现货溢价计算
        持仓情况 TODO 
        风险率 TODO
        """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._main())
        loop.run_forever()

    async def _main(self):
        self.subscribe = await data_center.create_subscribe()
        self.client = await data_center.create_client_adapter()

        # 订阅期货和现货价格
        await self.subscribe.subscribe_dict({'price', 'main'}, self.calc_premium)
        await self.subscribe.subscribe_dict({'price', 'future'}, self.calc_premium)

        # 订阅自己持仓情况
        await self.subscribe.subscribe_dict({'asset', 'main'}, self.calc_position)
        await self.subscribe.subscribe_dict({'asset', 'margin'}, self.calc_position)
        await self.subscribe.subscribe_dict({'asset', 'isolated', 'base'}, self.calc_position)
        await self.subscribe.subscribe_dict({'asset', 'isolated', 'quote'}, self.calc_position)
        await self.subscribe.subscribe_dict({'position', 'future'}, self.calc_position)

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

    async def calc_position(self, msg):
        """
        持仓信息有更新的时候计算双持、净持等信息
        """
        # 获取自己所有的持仓情况
        asset_main = await self.client.get_dict({'asset', 'main'})
        asset_margin = await self.client.get_dict({'asset', 'margin'})
        margin_borrowed = await self.client.get_dict({'borrowed', 'margin'})
        position_future = await self.client.get_dict({'position', 'future'})
        isolated_free = await self.client.get_dict({'asset', 'isolated', 'free'})
        isolated_borrowed = await self.client.get_dict({'asset', 'isolated', 'borrowed'})

        # 将期货的USDT交易对符号去掉
        temp = {}
        for key, value in position_future.items():
            if 'USDT' in key:
                temp[key.replace('USDT', '')] = value
        position_future = temp

        # 定义初始化的项目
        init_data = {
            'main': 0,  # 现货余额
            'margin': 0,  # 全仓余额
            'marginBorrowed': 0,  # 全仓借入
            'isolated': 0,  # 逐仓余额
            'isolatedBorrowed': 0,  # 逐仓借入
            'isolatedQuote': 0,  # 逐仓合约币（一般是USDT）余额
            'isolatedQuoteBorrowed': 0,  # 逐仓合约币借入
            # 'isolatedRisk': 99999,  # 逐仓风险率
            'future': 0,  # 期货余额
            'net': 0,  # 净持仓
            'hedging': 0,  # 双向持仓

            'value': 0,  # 双向持仓的单边市值
            'fundingRate': 0,  # 期货费率
            'premiumRate': 0,  # 期货溢价
        }

        # 统计净值和双持
        net = {}
        positive = {}
        negative = {}
        res = {}        # 最终要返回的结果
        # 将net可能用到的symbol都初始化为0
        for symbol in asset_main.keys():
            net[symbol] = 0
            positive[symbol] = 0
            negative[symbol] = 0
            res[symbol] = copy.copy(init_data)
        for symbol in asset_margin.keys():
            net[symbol] = 0
            positive[symbol] = 0
            negative[symbol] = 0
            res[symbol] = copy.copy(init_data)
        for symbol in position_future.keys():
            net[symbol] = 0
            positive[symbol] = 0
            negative[symbol] = 0
            res[symbol] = copy.copy(init_data)

        # 统计
        for symbol in asset_main.keys():
            num = asset_main[symbol]
            net[symbol] += num
            if num > 0:
                positive[symbol] += num
            if num < 0:
                negative[symbol] += (-num)
        for symbol in asset_margin.keys():
            num = asset_margin[symbol]
            net[symbol] += num
            if num > 0:
                positive[symbol] += num
            if num < 0:
                negative[symbol] += (-num)
        for symbol in position_future.keys():
            num = position_future[symbol]
            net[symbol] += num
            if num > 0:
                positive[symbol] += num
            if num < 0:
                negative[symbol] += (-num)

        for symbol in net.keys():
            res[symbol]['net'] = net[symbol]
        for symbol in (positive.keys() & negative.keys()):
            res[symbol]['hedging'] = min(positive[symbol], negative[symbol])

        # 填充自己的仓位信息
        for key, value in asset_main.items():
            res[key]['main'] = value
        for key, value in asset_margin.items():
            res[key]['margin'] = value
        for key, value in margin_borrowed.items():
            res[key]['marginBorrowed'] = value
        for key, value in isolated_free.items():
            res[key]['isolated'] = value
        for key, value in isolated_borrowed.items():
            res[key]['isolatedBorrowed'] = value
        for key, value in position_future.items():
            res[key]['future'] = value

        # 获取价格计算双持市值
        for key, value in res.items():
            if value['hedging'] != 0:
                price = await self.client.get({'price', 'main', key + 'USDT'})
                value['value'] = price * abs(value['hedging'])

        # 过滤掉全是0（无意义）的项目
        new_res = {}
        for key, value in res.items():
            for e in value.values():
                if e != 0:
                    new_res[key] = value
                    break

        res = new_res

        # 加入symbol成员，为转为列表格式做准备
        for symbol in res:
            res[symbol]['symbol'] = symbol

        res = [res[symbol] for symbol in res.keys()]

        await self.client.update({'json', 'position'}, res)
