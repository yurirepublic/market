import tools
import binance_api
import data_center
import json
import time

operator = binance_api.SmartOperator()
dc = data_center.Client()


class Script(tools.Script):
    """
    用来爬取现货websocket相关数据
    """

    def __init__(self):
        super(Script, self).__init__()
        self.main_asset = None  # 现货资产

    def info(self):
        info = tools.ScriptInfo()
        info.title = '接收现货websocket相关数据'
        info.description = '最开始会调用普通api获取初始数据，以后就用websocket接收更新数据'
        info.inputs = []

    def main_asset_update(self, data):
        """
        处理现货ws的回调函数
        """
        data = json.loads(data)
        if data['e'] == 'outboundAccountPosition':
            for x in data['B']:
                symbol = x['a']
                free = x['f']
                self.main_asset[symbol] = float(free)
            dc.set('main_asset', self.main_asset)
        elif data['e'] == 'balanceUpdate':
            pass
        else:
            print('无法识别的ws消息', data)

    def main(self):
        # 获取现货的资产数量
        self.main_asset = operator.get_all_asset_amount('MAIN')
        # 推送到数据中心
        dc.set('main_asset', self.main_asset)

        # 获取现货账户listen_key
        listen_key = operator.create_listen_key('MAIN')
        # 连接websocket
        handle = operator.connect_websocket('MAIN', listen_key, self.main_asset_update)
        handle.join()

