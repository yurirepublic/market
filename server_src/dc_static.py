import tools
import binance_api
import data_center
import json
import time


class Script(tools.Script):
    def info(self):
        info = tools.ScriptInfo()
        info.title = '接收交易所的静态数据'
        info.description = """
        静态数据不需要频繁更新
        所以此脚本放置的都是诸如交易规则、下单精度之类的数据
        一般1小时更新一次
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
            time.sleep(3600)

    def work(self):
        # 获取每个 现货 交易对的规则（下单精度）
        info = json.loads(self.operator.request(
            'api', '/api/v3/exchangeInfo', 'GET', {}, send_signature=False))
        server_time = info['serverTime']
        info = info['symbols']
        for e in info:
            symbol = e['symbol']
            quote_precision = e['quotePrecision']
            self.dc.update({'precision', 'quote', 'main', symbol}, quote_precision, server_time)

        # 获取每个 期货 交易对的规则（下单精度）
        info = json.loads(self.operator.request(
            'fapi', '/fapi/v1/exchangeInfo', 'GET', {}, send_signature=False))
        server_time = info['serverTime']
        info = info['symbols']
        for e in info:
            symbol = e['symbol']
            quote_precision = e['quantityPrecision']
            self.dc.update({'precision', 'quote', 'future', symbol}, quote_precision, server_time)

            # 获取这个symbol的历史100次资金费率
            history = json.loads(self.operator.request('fapi', '/fapi/v1/fundingRate', 'GET', {
                'symbol': symbol
            }))
            rate = [float(x['fundingRate']) for x in history]
            self.dc.update({'premium', 'fundingRateHistory', symbol}, rate)
