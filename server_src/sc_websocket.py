import script_manager
import binance_api
import data_center
import json
import asyncio


class Script(script_manager.Script):
    """
    用来爬取现货websocket相关数据
    TODO 还差逐仓的ws数据更新，但是逐仓需要每个账户都开一个ws，有点难搞
    """

    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '接收websocket相关数据'
        info.description = """
        最开始会调用普通api获取初始数据，以后就用websocket接收更新数据
        期货价格调用的是标记价格
        """
        return info

    def main(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self._main())
        loop.run_forever()

    async def _main(self):
        self.dc = await data_center.create_client()
        self.operator = await binance_api.create_operator()

        # 针对必须展示的资产进行初始化（因为资产为0不会被查询到）
        asyncio.create_task(self.dc.update({'asset', 'main', 'USDT'}, 0))
        asyncio.create_task(self.dc.update({'asset', 'future', 'USDT'}, 0))
        asyncio.create_task(self.dc.update({'asset', 'margin', 'USDT'}, 0))
        asyncio.create_task(self.dc.update({'asset', 'main', 'BNB'}, 0))
        asyncio.create_task(self.dc.update({'asset', 'future', 'BNB'}, 0))
        asyncio.create_task(self.dc.update({'asset', 'margin', 'BNB'}, 0))

        # 获取现货的资产数量
        res = await self.operator.request('api', '/api/v3/account', 'GET', {
            'timestamp': binance_api.get_timestamp()
        })
        res = res['balances']
        for e in res:
            asset = e['asset']
            free = float(e['free'])
            asyncio.create_task(self.dc.update({'asset', 'main', asset}, free))

        # 获取期货的资产和头寸信息
        res = await self.operator.request('fapi', '/fapi/v2/account', 'GET', {
            'timestamp': binance_api.get_timestamp()
        })
        for e in res['assets']:
            asset = e['asset']
            free = float(e['maxWithdrawAmount'])
            asyncio.create_task(self.dc.update({'asset', 'future', asset}, free))
        for e in res['positions']:
            symbol = e['symbol']
            position = float(e['positionAmt'])
            asyncio.create_task(self.dc.update({'position', 'future', symbol}, position))

        # 获取全仓的资产和借贷数量
        res = await self.operator.request('api', '/sapi/v1/margin/account', 'GET', {
            'timestamp': binance_api.get_timestamp()
        })
        res = res['userAssets']
        for e in res:
            asset = e['asset']
            borrowed = float(e['borrowed'])
            free = float(e['free'])
            asyncio.create_task(self.dc.update({'asset', 'margin', asset}, free))
            asyncio.create_task(self.dc.update({'borrowed', 'margin', asset}, borrowed))

        # 启动websocket进行追踪
        asyncio.create_task(self.main_account_update())
        asyncio.create_task(self.margin_account_update())
        asyncio.create_task(self.future_account_update())
        asyncio.create_task(self.isolated_account_update())

        # 期货比较特殊，纸面浮盈不会推送，所以暂定为5s刷新一次
        asyncio.create_task(self.future_usdt())

        # 获取现货所有价格
        price = await self.operator.get_all_latest_price('MAIN')
        for key in price.keys():
            asyncio.create_task(self.dc.update({'price', 'main', key}, price[key]))
        # 连接websocket获取推送价格
        asyncio.create_task(self.main_price_update())

        # 获取期货所有价格
        price = await self.operator.get_all_latest_price('FUTURE')
        for key in price.keys():
            asyncio.create_task(self.dc.update({'price', 'future', key}, price[key]))
        # 连接websocket获取推送价格
        asyncio.create_task(self.future_price_update())

    async def future_usdt(self):
        """
        每5s刷新一下不会被推送的期货usdt余额
        """
        while True:
            await asyncio.sleep(5)
            usdt = await self.operator.get_asset_amount('USDT', 'FUTURE')
            await self.dc.update({'asset', 'future', 'USDT'}, usdt)

    async def main_update(self, mode, data):
        """
        处理现货和全仓和逐仓的账户更新
        """
        data = json.loads(data)
        if data['e'] == 'outboundAccountPosition':
            # 扫描数据
            for x in data['B']:
                asset = x['a']
                free = float(x['f'])
                try:
                    timestamp = int(x['E'])
                except KeyError:
                    timestamp = None
                # 发送到数据中心
                asyncio.create_task(self.dc.update({'asset', mode, asset}, free, timestamp))
        elif data['e'] == 'balanceUpdate':
            self.log('被忽略的余额更新事件', data)
        elif data['e'] == 'executionReport':
            if data['X'] == 'NEW':
                self.log('被忽略的NEW事件', data)
            elif data['X'] == 'PARTIALLY_FILLED':
                self.log('被忽略的PARTIALLY_FILLED事件')
            elif data['X'] == 'FILLED':
                self.log('被忽略的FILLED事件')
        else:
            self.log('无法识别的现货、全仓或逐仓账户ws消息', data)

    async def main_account_update(self):
        """
        处理现货账户更新
        """
        listen_key = await self.operator.create_listen_key('MAIN')
        ws = await self.operator.connect_websocket('MAIN', listen_key)
        asyncio.create_task(self.ping_main(listen_key))
        while True:
            data = await ws.recv()
            await self.main_update('main', data)

    async def ping_main(self, key):
        """
        每30分钟发送一个ping来延长ws有效时间
        """
        while True:
            await asyncio.sleep(1800)
            await self.operator.overtime_listen_key('MAIN', key)

    async def margin_account_update(self):
        """
        处理全仓账户更新
        """
        # 连接全仓账户ws
        listen_key = await self.operator.create_listen_key('MARGIN')
        ws = await self.operator.connect_websocket('MAIN', listen_key)
        asyncio.create_task(self.ping_margin(listen_key))
        while True:
            data = await ws.recv()
            await self.main_update('margin', data)

    async def ping_margin(self, key):
        while True:
            await asyncio.sleep(1800)
            await self.operator.overtime_listen_key('MARGIN', key)

    async def isolated_account_update(self):
        """
        处理逐仓账户更新
        """
        # 逐仓更新起来十分麻烦，而且仓位更新不频繁，所以1s调用http接口刷新一次
        while True:
            # 获取逐仓的资产和借贷数量
            res = await self.operator.request('api', '/sapi/v1/margin/isolated/account', 'GET', {
                'timestamp': binance_api.get_timestamp()
            })
            res = res['assets']
            for e in res:
                asyncio.create_task(self.update_isolated(e))

            await asyncio.sleep(1)

    async def update_isolated(self, e):
        symbol = e['symbol']

        # 因为isolated是非推送式更新，所以推送前看看有没有变化，没有变化就不推送
        free = float(e['baseAsset']['free'])
        borrowed = float(e['baseAsset']['borrowed'])
        if free != await self.dc.get({'asset', 'isolated', 'base', symbol}):
            asyncio.create_task(self.dc.update({'asset', 'isolated', 'base', symbol}, free))
        if borrowed != await self.dc.get({'borrowed', 'isolated', 'base', symbol}):
            asyncio.create_task(self.dc.update({'borrowed', 'isolated', 'base', symbol}, borrowed))

        free = float(e['quoteAsset']['free'])
        borrowed = float(e['quoteAsset']['borrowed'])
        if free != await self.dc.get({'asset', 'isolated', 'quote', symbol}):
            asyncio.create_task(self.dc.update({'asset', 'isolated', 'quote', symbol}, free))
        if borrowed != await self.dc.get({'borrowed', 'isolated', 'quote', symbol}):
            asyncio.create_task(self.dc.update({'borrowed', 'isolated', 'quote', symbol}, borrowed))

    async def future_account_update(self):
        """
        处理期货账户更新
        """
        # 连接期货账户ws
        listen_key = await self.operator.create_listen_key('FUTURE')
        ws = await self.operator.connect_websocket('FUTURE', listen_key)
        asyncio.create_task(self.ping_future(listen_key))
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
                self.log('无法识别的期货账户ws消息', data)

    async def ping_future(self, key):
        while True:
            await asyncio.sleep(1800)
            await self.operator.overtime_listen_key('FUTURE', key)

    async def main_price_update(self):
        """
        处理现货价格更新
        """
        ws = await self.operator.connect_websocket('MAIN', '!miniTicker@arr')
        while True:
            data = await ws.recv()
            data = json.loads(data)
            for x in data:
                if x['e'] == '24hrMiniTicker':
                    timestamp = int(x['E'])
                    symbol = x['s']
                    price = float(x['c'])  # 最新成交价格
                    asyncio.create_task(self.dc.update({'main', 'price', symbol}, price, timestamp))
                else:
                    self.log('无法识别的现货价格ws消息', x)

    async def future_price_update(self):
        """
        处理期货价格更新
        """
        ws = await self.operator.connect_websocket('FUTURE', '!markPrice@arr')
        while True:
            data = await ws.recv()
            data = json.loads(data)
            for x in data:
                if x['e'] == 'markPriceUpdate':
                    timestamp = int(x['E'])
                    symbol = x['s']
                    price = float(x['p'])  # 标记价格
                    asyncio.create_task(self.dc.update({'future', 'price', symbol}, price, timestamp))
                else:
                    self.log('无法识别的期货价格ws消息', x)
