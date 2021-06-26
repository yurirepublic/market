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
        self.client = await data_center.create_client()

        # 订阅期货和现货价格
        await self.subscribe.subscribe_dict({'price', 'main'}, self.calc_premium)
        await self.subscribe.subscribe_dict({'price', 'future'}, self.calc_premium)

        # 订阅自己持仓情况
        await self.subscribe.subscribe_dict({'asset', 'main'}, self.calc_position)

        await self.subscribe.subscribe_dict({'asset', 'margin'}, self.calc_position)
        await self.subscribe.subscribe_dict({'borrowed', 'margin'}, self.calc_position)

        await self.subscribe.subscribe_dict({'asset', 'isolated', 'base'}, self.calc_position)
        await self.subscribe.subscribe_dict({'borrowed', 'isolated', 'base'}, self.calc_position)

        await self.subscribe.subscribe_dict({'asset', 'isolated', 'quote'}, self.calc_position)
        await self.subscribe.subscribe_dict({'borrowed', 'isolated', 'quote'}, self.calc_position)

        await self.subscribe.subscribe_dict({'position', 'future'}, self.calc_position)

        # 启动风险率计算协程
        asyncio.create_task(self.calc_risk_interval())

    @staticmethod
    def delete_usdt_symbol(data: dict) -> dict:
        """
        用于删除字典中所有key的USDT符号
        """
        temp = {}
        for key, value in data.items():
            if 'USDT' in key and key[-4:] == 'USDT':
                temp[key.replace('USDT', '')] = value
        return temp

    async def calc_premium(self, msg) -> None:
        for key in msg.keys():
            # 获取交易符号
            symbol = key
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
            asyncio.create_task(self.client.update({'premium', 'dif', symbol}, future_price - main_price))

    async def calc_position(self, msg) -> None:
        """
        持仓信息有更新的时候计算双持、净持等信息\n
        并且会将数据上传到数据中心
        """
        # 获取自己所有的持仓情况
        asset_main = await self.client.get_dict({'asset', 'main'})

        asset_margin = await self.client.get_dict({'asset', 'margin'})
        margin_borrowed = await self.client.get_dict({'borrowed', 'margin'})

        isolated_free = await self.client.get_dict({'asset', 'isolated', 'base'})
        isolated_borrowed = await self.client.get_dict({'borrowed', 'isolated', 'base'})

        isolated_quote_free = await self.client.get_dict({'asset', 'isolated', 'quote'})
        isolated_quote_borrowed = await self.client.get_dict({'borrowed', 'isolated', 'quote'})

        position_future = await self.client.get_dict({'position', 'future'})

        # 将期货和逐仓的USDT交易对符号去掉
        position_future = self.delete_usdt_symbol(position_future)
        isolated_free = self.delete_usdt_symbol(isolated_free)
        isolated_borrowed = self.delete_usdt_symbol(isolated_borrowed)
        isolated_quote_free = self.delete_usdt_symbol(isolated_quote_free)
        isolated_quote_borrowed = self.delete_usdt_symbol(isolated_quote_borrowed)

        # 定义初始化的项目
        init_data = {
            'main': 0,  # 现货余额
            'margin': 0,  # 全仓余额
            'marginBorrowed': 0,  # 全仓借入
            'isolated': 0,  # 逐仓余额
            'isolatedBorrowed': 0,  # 逐仓借入
            'isolatedQuote': 0,  # 逐仓合约币（一般是USDT）余额
            'isolatedQuoteBorrowed': 0,  # 逐仓合约币借入
            'isolatedRisk': 0,  # 逐仓贷款占比
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
        res = {}  # 最终要返回的结果
        # 将net可能用到的symbol都初始化为0
        need_init_symbol = set()
        need_init_symbol = need_init_symbol | asset_main.keys()
        need_init_symbol = need_init_symbol | asset_margin.keys()
        need_init_symbol = need_init_symbol | margin_borrowed.keys()
        need_init_symbol = need_init_symbol | position_future.keys()
        need_init_symbol = need_init_symbol | isolated_free.keys()
        need_init_symbol = need_init_symbol | isolated_borrowed.keys()
        need_init_symbol = need_init_symbol | isolated_quote_free.keys()
        need_init_symbol = need_init_symbol | isolated_quote_borrowed.keys()

        for symbol in need_init_symbol:
            net[symbol] = 0
            positive[symbol] = 0
            negative[symbol] = 0
            res[symbol] = copy.copy(init_data)

        # 开始统计净值和双持，依据不同影响，将数值加到净值或者双持上面
        for symbol in asset_main.keys():
            amount = asset_main[symbol]
            net[symbol] += amount
            positive[symbol] += amount
        for symbol in asset_margin.keys():
            amount = asset_margin[symbol]
            net[symbol] += amount
            positive[symbol] += amount
        for symbol in position_future.keys():
            amount = position_future[symbol]
            net[symbol] += amount
            if amount > 0:
                positive[symbol] += amount
            if amount < 0:
                negative[symbol] += (-amount)
        for symbol in isolated_free:
            amount = isolated_free[symbol]
            net[symbol] += amount
            positive[symbol] += amount
        for symbol in isolated_borrowed:
            amount = isolated_borrowed[symbol]
            net[symbol] -= amount
            negative[symbol] += amount

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
        for key, value in position_future.items():
            res[key]['future'] = value
        for key, value in isolated_free.items():
            res[key]['isolated'] = value
        for key, value in isolated_borrowed.items():
            res[key]['isolatedBorrowed'] = value
        for key, value in isolated_quote_free.items():
            res[key]['isolatedQuote'] = value
        for key, value in isolated_quote_borrowed.items():
            res[key]['isolatedQuoteBorrowed'] = value

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

        # 将字典格式转为列表格式
        res = [res[symbol] for symbol in res.keys()]

        await self.client.update({'json', 'position'}, res)

    async def calc_risk_interval(self):
        """
        计算风险率
        """
        while True:
            asyncio.create_task(self.calc_risk())
            await asyncio.sleep(1)

    async def calc_risk(self):
        # 获取期货的仓位和USDT余额
        position = await self.client.get_dict({'position', 'future'})
        usdt = await self.client.get({'asset', 'future', 'USDT'})
        if usdt is None:
            usdt = 0

        # 计算期货的总市值
        total = 0
        prices = await self.client.get_dict({'price', 'future'})
        for key, value in position.items():
            amount = value
            if amount != 0:
                price = prices[key]
                total += abs(price * amount)

        # 计算期货风险率
        try:
            risk = total / usdt
        except ZeroDivisionError:
            risk = 0
        await self.client.update({'risk', 'future', 'usage'}, risk)

        # 计算期货风险所需波动率（500%风险率）
        try:
            warning = (total + (5 * usdt - total) / 6) / total
            warning -= 1
        except ZeroDivisionError:
            warning = 99999
        await self.client.update({'risk', 'future', 'warning'}, warning)

        # 获取全仓的仓位和USDT余额
        margin = await self.client.get_dict({'asset', 'margin'})
        borrowed = await self.client.get_dict({'borrowed', 'margin'})

        if 'USDT' in margin.keys():
            usdt = margin['USDT']
            del margin['USDT']  # 必须要删除，不然等下会把USDT纳入base资产
        else:
            usdt = 0

        if 'USDT' in borrowed.keys():
            usdt_borrowed = borrowed['USDT']
            del borrowed['USDT']    # 必须要删除，不然等下会把USDT纳入base资产
        else:
            usdt_borrowed = 0

        # 统计全仓的总市值和总借贷市值
        total = 0
        total_borrowed = 0
        prices = await self.client.get_dict({'price', 'main'})
        for key, value in margin.items():
            amount = value
            if amount != 0:
                price = prices[key + 'USDT']
                total += price * amount
        for key, value in borrowed.items():
            amount = value
            if amount != 0:
                price = prices[key + 'USDT']
                total += price * amount  # 借贷的钱也是自己手上的钱，所有要加上
                total_borrowed += price * amount
        total += usdt
        total_borrowed += usdt_borrowed

        # 计算全仓风险率
        if total == 0:
            margin_risk = 0
        else:
            margin_risk = ((total_borrowed + usdt_borrowed) / (total + usdt))

        # # 计算全仓触发风险警告所需波动率
        # if total_borrowed - 0.8 * total == 0:
        #     margin_warning = 99999
        # else:
        #     margin_warning = ((0.8 * total - usdt_borrowed) / (total_borrowed - 0.8 * total))

        await self.client.update({'risk', 'margin', 'usage'}, margin_risk)
        # await self.client.update({'risk', 'margin', 'warning'}, margin_warning)


