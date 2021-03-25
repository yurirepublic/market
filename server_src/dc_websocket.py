import tools
import binance_api
import data_center
import json
import asyncio


class Script(tools.Script):
    """
    用来爬取现货websocket相关数据
    """

    def info(self):
        info = tools.ScriptInfo()
        info.title = '接收websocket相关数据'
        info.description = """
        最开始会调用普通api获取初始数据，以后就用websocket接收更新数据
        期货价格调用的是标记价格
        """
        return info

    def __init__(self):
        super(Script, self).__init__()
        self.dc = data_center.WebsocketClientAdapter()
        self.operator = binance_api.SmartOperator()

    def main(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._main())

    async def _main(self):
        # 获取现货的资产数量
        asset = self.operator.get_all_asset_amount('MAIN')
        # 推送到数据中心
        for key in asset.keys():
            asyncio.create_task(self.dc.update({'asset', 'main', key}, asset[key]))

        # 获取全仓资产数量
        asset = self.operator.get_all_asset_amount('MARGIN')
        for key in asset.keys():
            asyncio.create_task(self.dc.update({'asset', 'margin', key}, asset[key]))

        # 获取逐仓资产数量
        asset = self.operator.get_all_asset_amount('ISOLATED')
        for key in asset.keys():
            asyncio.create_task(self.dc.update({'asset', 'isolated', key}, asset[key]))

        asyncio.create_task(self.main_account_update())
        asyncio.create_task(self.margin_account_update())
        asyncio.create_task(self.future_account_update())

        # 获取现货所有价格
        price = self.operator.get_all_latest_price('MAIN')
        for key in price.keys():
            await self.dc.update({'price', 'main', key}, price[key])
        # 连接websocket获取推送价格
        asyncio.create_task(self.main_price_update())

        # 获取期货所有价格
        price = self.operator.get_all_latest_price('FUTURE')
        for key in price.keys():
            await self.dc.update({'price', 'future', key}, price[key])
        # 连接websocket获取推送价格
        asyncio.create_task(self.future_price_update())

    async def main_update(self, mode, data):
        """
        处理现货三个仓位的账户更新
        """
        data = json.loads(data)
        if data['e'] == 'outboundAccountPosition':
            # 扫描数据
            for x in data['B']:
                symbol = x['a']
                free = float(x['f'])
                timestamp = int(x['E'])
                # 发送到数据中心
                await self.dc.update({'asset', mode, symbol}, free, timestamp)
        elif data['e'] == 'balanceUpdate':
            pass
        else:
            self.log('无法识别的ws消息', data)

    async def main_account_update(self):
        """
        处理现货账户更新
        """
        listen_key = self.operator.create_listen_key('MAIN')
        ws = await binance_api.connect_websocket('MAIN', listen_key)
        while True:
            data = await ws.recv()
            await self.main_update('main', data)

    async def margin_account_update(self):
        """
        处理全仓账户更新
        """
        # 连接全仓账户ws
        listen_key = self.operator.create_listen_key('MARGIN')
        ws = await binance_api.connect_websocket('MAIN', listen_key)
        while True:
            data = await ws.recv()
            await self.main_update('margin', data)

    # async def isolated_account_update(self, data):
    #     """
    #     处理逐仓账户更新
    #     """
    # # 连接逐仓账户ws
    # listen_key = operator.create_listen_key('ISOLATED')
    # handle = operator.connect_websocket('ISOLATED', listen_key, self.isolated_account_update)
    # handles.append(handle)
    #     self.main_update('isolated', data)

    async def future_account_update(self):
        """
        处理期货账户更新
        """
        # 连接期货账户ws
        listen_key = self.operator.create_listen_key('FUTURE')
        ws = await binance_api.connect_websocket('FUTURE', listen_key)
        while True:
            data = await ws.recv()
            data = json.loads(data)
            # 账户更新推送
            timestamp = int(data['E'])
            if data['e'] == 'ACCOUNT_UPDATE':
                """
                注：根据API说明，事件原因为FUNDING FEE时，不推送持仓信息，且仅推送相关资产信息
                """
                balance = data['a']['B']
                for asset in balance:
                    symbol = asset['a']
                    wb = float(asset['wb'])  # 钱包余额
                    await self.dc.update({'asset', 'future', symbol}, wb, timestamp)
                # 如果事件原因不是FUNDING FEE，则更新持仓
                if data['a']['m'] != 'FUNDING FEE':
                    position = data['a']['P']
                    for x in position:
                        symbol = x['s']
                        pa = float(x['pa'])  # 仓位
                        await self.dc.update({'position', 'future', symbol}, pa, timestamp)
            # 追加保证金通知推送
            elif data['e'] == 'MARGIN_CALL':
                pass
            # 订单/交易 更新推送
            elif data['e'] == 'ORDER_TRADE_UPDATE':
                pass
            # 杠杆倍数更新推送
            elif data['e'] == 'ACCOUNT_CONFIG_UPDATE':
                pass
            else:
                self.log('无法识别的ws消息', data)

    async def main_price_update(self):
        """
        处理现货价格更新
        """
        ws = await binance_api.connect_websocket('MAIN', '!miniTicker@arr')
        while True:
            data = await ws.recv()
            data = json.loads(data)
            for x in data:
                if x['e'] == '24hrMiniTicker':
                    timestamp = int(x['E'])
                    symbol = x['s']
                    price = float(x['c'])  # 最新成交价格
                    await self.dc.update({'main', 'price', symbol}, price, timestamp)
                else:
                    self.log('无法识别的ws消息', x)

    async def future_price_update(self):
        """
        处理期货价格更新
        """
        ws = await binance_api.connect_websocket('FUTURE', '!markPrice@arr')
        while True:
            data = await ws.recv()
            data = json.loads(data)
            for x in data:
                if x['e'] == 'markPriceUpdate':
                    timestamp = int(x['E'])
                    symbol = x['s']
                    price = float(x['p'])  # 标记价格
                    await self.dc.update({'future', 'price', symbol}, price, timestamp)
                else:
                    self.log('无法识别的ws消息', x)
