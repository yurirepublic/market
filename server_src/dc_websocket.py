import tools
import binance_api
import data_center
import json

operator = binance_api.SmartOperator()
dc = data_center.WebsocketClientAdapter()


class Script(tools.Script):
    """
    用来爬取现货websocket相关数据
    """

    def __init__(self):
        super(Script, self).__init__()

    def info(self):
        info = tools.ScriptInfo()
        info.title = '接收websocket相关数据'
        info.description = """
        最开始会调用普通api获取初始数据，以后就用websocket接收更新数据
        期货价格调用的是标记价格
        """
        info.inputs = []
        return info

    def main_update(self, mode, data):
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
                dc.update(['asset', mode, symbol], free, timestamp)
        elif data['e'] == 'balanceUpdate':
            pass
        else:
            self.log('无法识别的ws消息', data)

    def main_account_update(self, data):
        """
        处理现货账户更新
        """
        self.main_update('main', data)

    def margin_account_update(self, data):
        """
        处理全仓账户更新
        """
        self.main_update('margin', data)

    def isolated_account_update(self, data):
        """
        处理逐仓账户更新
        """
        self.main_update('isolated', data)

    def future_account_update(self, data):
        """
        处理期货账户更新
        """
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
                dc.update(['asset', 'future', symbol], wb, timestamp)
            # 如果事件原因不是FUNDING FEE，则更新持仓
            if data['a']['m'] != 'FUNDING FEE':
                position = data['a']['P']
                for x in position:
                    symbol = x['s']
                    pa = float(x['pa'])  # 仓位
                    dc.update(['position', 'future', symbol], pa, timestamp)
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

    def main_price_update(self, data):
        """
        处理现货价格更新
        """
        data = json.loads(data)
        for x in data:
            if x['e'] == '24hrMiniTicker':
                timestamp = int(x['E'])
                symbol = x['s']
                price = float(x['c'])  # 最新成交价格
                dc.update(['main', 'price', symbol], price, timestamp)
            else:
                self.log('无法识别的ws消息', x)

    def future_price_update(self, data):
        """
        处理期货价格更新
        """
        data = json.loads(data)
        for x in data:
            if x['e'] == 'markPriceUpdate':
                timestamp = int(x['E'])
                symbol = x['s']
                price = float(x['p'])  # 标记价格
                dc.update(['future', 'price', symbol], price, timestamp)
            else:
                self.log('无法识别的ws消息', x)

    def main(self):
        handles = []

        # 获取现货的资产数量
        asset = operator.get_all_asset_amount('MAIN')
        # 推送到数据中心
        for key in asset.keys():
            dc.update(['asset', 'main', key], asset[key])

        # 获取全仓资产数量
        asset = operator.get_all_asset_amount('MARGIN')
        for key in asset.keys():
            dc.update(['asset', 'margin', key], asset[key])

        # 获取逐仓资产数量
        asset = operator.get_all_asset_amount('ISOLATED')
        for key in asset.keys():
            dc.update(['asset', 'isolated', key], asset[key])

        # 连接现货账户ws
        def _main_ws_ping():
            pass

        listen_key = operator.create_listen_key('MAIN')
        handle = operator.connect_websocket('MAIN', listen_key, self.main_account_update)
        handles.append(handle)

        # 连接全仓账户ws
        listen_key = operator.create_listen_key('MARGIN')
        handle = operator.connect_websocket('MAIN', listen_key, self.margin_account_update)
        handles.append(handle)

        # # 连接逐仓账户ws
        # listen_key = operator.create_listen_key('ISOLATED')
        # handle = operator.connect_websocket('ISOLATED', listen_key, self.isolated_account_update)
        # handles.append(handle)

        # 连接期货账户ws
        listen_key = operator.create_listen_key('FUTURE')
        handle = operator.connect_websocket('FUTURE', listen_key, self.future_account_update)
        handles.append(handle)

        # 获取现货所有价格
        price = operator.get_all_latest_price('MAIN')
        for key in price.keys():
            dc.update(['price', 'main', key], price[key])
        # 连接websocket获取推送价格
        handle = operator.connect_websocket('MAIN', '!miniTicker@arr', self.main_price_update)
        handles.append(handle)

        # 获取期货所有价格
        price = operator.get_all_latest_price('FUTURE')
        for key in price.keys():
            dc.update(['price', 'future', key], price[key])
        # 连接websocket获取推送价格
        handle = operator.connect_websocket('FUTURE', '!markPrice@arr', self.future_price_update)
        handles.append(handle)

        for e in handles:
            e.join()
