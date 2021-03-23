import tools
import binance_api
import data_center
import json
import time


class Script(tools.Script):
    def info(self):
        info = tools.ScriptInfo()
        info.title = '接收交易所的实时静态数据'
        info.description = """
        虽然是静态数据，交易所不提供websocket进行推送
        但是这个数据也具有一定的实时性
        例如每个交易对的资金费率
        一般1分钟更新一次
        """
        return info

    def __init__(self):
        super(Script, self).__init__()
        self.dc = None
        self.operator = None

    def main(self):
        self.operator = binance_api.SmartOperator()
        while True:
            self.dc = data_center.WebsocketClientAdapter()
            self.work()
            self.dc.close()
            time.sleep(60)

    def work(self):
        premium = json.loads(self.operator.request(
            'fapi', '/fapi/v1/premiumIndex', 'GET', {}))
        for e in premium:
            symbol = e['symbol']
            rate = float(e['lastFundingRate'])
            server_time = e['time']
            self.dc.update({'premium', 'fundingRate', symbol}, rate, server_time)

