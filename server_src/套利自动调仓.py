import script_manager
import binance
import binance as bi
import time
import script_manager
import json
import math
import multiprocessing


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = "套利自动调仓"
        info.description = """
        初代版本，有待改进
        会自动将所有钱都划到期货，所以要对账户进行操作的时候，务必关闭脚本
        注意加仓限制和减仓限制，针对的都是期货账户的USDT余额
        加仓限制和减仓限制太过接近，将会频繁调仓导致亏损
        单周期加仓交易额不要设置太高，市价单对大金额订单滑点特别厉害
        TODO 添加下单失败重下机制
        TODO 制定严谨的错误处理链，从可靠的自动处理，到无法自动处理的语音电话警报
        TODO 添加孤立仓位平仓机制，如果操作的仓位发现孤立仓位立马平仓，并发出警报
        """
        info.inputs.append(script_manager.ScriptInput('调仓的交易对', 'close_symbol', ''))
        info.inputs.append(script_manager.ScriptInput('减仓限制', 'close_limit', 200))
        info.inputs.append(script_manager.ScriptInput('加仓限制', 'open_limit', 1500))
        info.inputs.append(script_manager.ScriptInput('调仓目标', 'aim', 800))
        info.inputs.append(script_manager.ScriptInput('单周期加仓最大交易额', 'max_once', 100))
        info.inputs.append(script_manager.ScriptInput('期货保证金率', 'margin_rate', 0.05))
        info.inputs.append(script_manager.ScriptInput('刷新间隔（秒）', 'refresh_timeout', 30))
        return info

    def main(self):
        operator = binance.SmartOperator()  # 实例化一个币安api的操作者

        # 从用户输入获取
        close_symbol = str(self.input_dict['close_symbol'])
        close_limit = float(self.input_dict['close_limit'])
        open_limit = float(self.input_dict['open_limit'])
        aim = float(self.input_dict['aim'])
        max_once = float(self.input_dict['max_once'])
        margin_rate = float(self.input_dict['margin_rate'])
        refresh_timeout = float(self.input_dict['refresh_timeout'])
        self.log(self.input_dict)

        """
        注：每次调仓会将仓位调到目标
        """

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
            elif future < close_limit:
                self.log('现货期货余额', main, future, '期货资金不足，准备平仓')
                # 差目标多少钱
                need = aim - future
                self.log('差目标', need, 'USDT')

                # 折算成仓位币数
                # 平仓1现货，能减仓现货币价
                # 平仓1期货，能减仓期货币价 * margin_rate
                # 所以平仓1仓位，能减仓 现货币价 + 期货币价 * margin_rate
                main_price = operator.get_latest_price(close_symbol, 'MAIN')
                future_price = operator.get_latest_price(
                    close_symbol, 'FUTURE')
                self.log('最新现货期货币价', main_price, future_price)

                # 平仓币数，就等于 差多少钱/平仓减仓钱
                coin = need / (main_price + future_price * margin_rate)
                # 转为最低精度
                coin = binance.float_to_str_floor(
                    coin, operator.get_symbol_precision(close_symbol))
                self.log('需要平仓', coin, close_symbol)

                self.log('发出平仓交易请求')

                # TODO 加入下单错误处理机制

                def _close_main():
                    operator.trade_market(
                        close_symbol, 'MAIN', coin, 'SELL')

                def _close_future():
                    operator.trade_market(
                        close_symbol, 'FUTURE', coin, 'BUY')

                handel1 = multiprocessing.Process(
                    target=_close_main)
                handel2 = multiprocessing.Process(
                    target=_close_future)
                handel1.start()
                handel2.start()
                handel1.join()
                handel2.join()

            # TODO 加入自动加仓机制
            # # 期货钱太多要加仓的情况
            # elif future + main > open_limit:
            #     self.log('高于加仓线，当前余额 现货期货', main, future)
            #     # 计算需要加仓多少      持有USDT - 中位数 = 多出来的钱
            #     need_open = (future + main) - \
            #         (open_limit + close_limit) / 2
            #     self.log('需要加仓', need_open, 'USDT')

            #     # 判断需要转多少钱到现货，默认多转5%
            #     need_transfer = need_open * 1.05 - main
            #     self.log('现货缺', need_transfer, 'USDT')
            #     # 如果是正数就转
            #     if need_transfer > 0:
            #         self.log('划转', need_transfer, '到现货')
            #         operator.transfer_asset(
            #             'UMFUTURE_MAIN', 'USDT', need_transfer)

            #     # 加仓钱>20则加仓
            #     if need_open > 20:
            #         # 把加仓的钱乘以90%换算成货币数（留余，以免钱不够开仓失败）
            #         need_open = (need_open * 0.9) / \
            #             operator.get_latest_price(close_symbol, 'MAIN')
            #         # 将货币数转为精度对应的str
            #         need_open = binance_api.float_to_str_floor(
            #             need_open, operator.get_symbol_precision(close_symbol))

            #         self.log('需要加仓', need_open, '货币')

            #         # 期货现货反向开仓

            #         def _open_main():
            #             operator.trade_market(
            #                 close_symbol, 'MAIN', need_open, 'BUY')

            #         def _open_future():
            #             operator.trade_market(
            #                 close_symbol, 'FUTURE', need_open, 'SELL')

            #         # 加仓货币不为0就加仓
            #         if float(need_open) != 0:
            #             self.log('启动加仓')
            #             handel1 = multiprocessing.Process(target=_open_main)
            #             handel2 = multiprocessing.Process(target=_open_future)
            #             handel1.start()
            #             handel2.start()
            #             handel1.join()
            #             handel2.join()

            time.sleep(refresh_timeout)
