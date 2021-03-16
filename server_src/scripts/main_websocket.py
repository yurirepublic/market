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

    def info(self):
        info = tools.ScriptInfo()
        info.title = '接收现货websocket相关数据'
        info.description = '最开始会调用普通api获取初始数据，以后就用websocket接收更新数据'
        info.inputs = []

    @staticmethod
    def main_asset_update(data):
        """
        处理现货ws的回调函数
        """
        data = json.loads(data)
        if data['e'] == 'outboundAccountPosition':
            # 扫描数据
            for x in data['B']:
                symbol = x['a']
                free = x['f']
                # 发送到数据中心
                dc.update(['asset', 'main', symbol], free)
        elif data['e'] == 'balanceUpdate':
            pass
        else:
            print('无法识别的ws消息', data)

    def main(self):
        # 获取现货的资产数量
        asset = operator.get_all_asset_amount('MAIN')
        # 推送到数据中心
        for key in asset.keys():
            dc.update(['asset', 'main', key], asset[key])

        # 获取现货账户listen_key
        listen_key = operator.create_listen_key('MAIN')
        # 连接websocket
        handle = operator.connect_websocket('MAIN', listen_key, self.main_asset_update)
        handle.join()
