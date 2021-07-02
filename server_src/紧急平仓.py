import binance
import time
import script_manager
import json
import math
import multiprocessing


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = "自动紧急平仓"
        info.description = """
        需要手动改代码
        """
        return info

    def main(self):
        operator = binance.SmartOperator()  # 实例化一个币安api的操作者

        while True:
            # 获取余额
            main = operator.get_asset_amount('USDT', 'MAIN')
            future = operator.get_asset_amount('USDT', 'FUTURE')

            # 现货有一丁点钱都划到期货
            if main > 0:
                self.log('现货期货余额', main, future, '已全部划转到期货')
                operator.transfer_asset('MAIN_UMFUTURE', 'USDT', main)
                main = operator.get_asset_amount('USDT', 'MAIN')
                future = operator.get_asset_amount('USDT', 'FUTURE')
                self.log('划转后现货期货余额', main, future)

            # 期货钱不够的情况
            elif future < 300:
                self.log('现货期货余额', main, future, '期货资金不足，准备平仓')

                self.log('发出平仓交易请求')

                def _close_main(symbol, amount):
                    operator.trade_market(
                        symbol, 'MAIN', amount, 'SELL')

                def _close_future(symbol, amount):
                    operator.trade_market(
                        symbol, 'FUTURE', amount, 'BUY')

                handel1 = multiprocessing.Process(
                    target=_close_main, args=('CHZUSDT', 2484))
                handel2 = multiprocessing.Process(
                    target=_close_future, args=('CHZUSDT', 2484))
                handel3 = multiprocessing.Process(
                    target=_close_main, args=('FTMUSDT', 2016))
                handel4 = multiprocessing.Process(
                    target=_close_future, args=('FTMUSDT', 2016))
                handel5 = multiprocessing.Process(
                    target=_close_main, args=('DODOUSDT', 185.6))
                handel6 = multiprocessing.Process(
                    target=_close_future, args=('DODOUSDT', 185.6))
                handel1.start()
                handel2.start()
                handel3.start()
                handel4.start()
                handel5.start()
                handel6.start()
                handel1.join()
                handel2.join()
                handel3.join()
                handel4.join()
                handel5.join()
                handel6.join()

            time.sleep(30)
