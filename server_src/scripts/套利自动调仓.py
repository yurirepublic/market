import tools
import binance_api
import binance_api as bi
import time
import tools
import json
import math
import multiprocessing


class Script(tools.Script):
    def info(self):
        info = tools.ScriptInfo()
        info.title = "套利自动调仓"
        info.description = """初代版本，有待改进
        注意加仓限制和减仓限制，针对的都是期货账户的USDT余额
        每次调仓会让期货USDT余额尽可能逼近加仓和减仓之间
        所以加仓限制和减仓限制太过接近，将会频繁调仓导致亏损
        TODO 添加下单失败重下机制
        TODO 制定严谨的错误处理链，从可靠的自动处理，到无法自动处理的语音电话警报
        """
        info.inputs.append(tools.ScriptInput('调仓的交易对', 'close_symbol', ''))
        info.inputs.append(tools.ScriptInput('减仓限制', 'close_limit', 200))
        info.inputs.append(tools.ScriptInput('加仓限制', 'open_limit', 1500))
        return info

    def main(self):
        operator = binance_api.SmartOperator()     # 实例化一个币安api的操作者

        # 从用户输入获取
        close_symbol = 'ANKRUSDT'       # 期货账户保证金不足时用于平仓的货币对
        close_limit = 200           # 低于此金额，将会减杠杆
        open_limit = 1500           # 高于此金额，将会加杠杆

        refresh_timeout = 30            # 刷新账户金额的间隔(秒)，极快刷新可能导致服务器被封禁
        """
        注：每次调仓会将仓位调到close和open的中间
        """

        while True:
            # 获取余额
            usdt_main = operator.get_asset_amount('USDT', 'MAIN')
            usdt_future = operator.get_asset_amount('USDT', 'FUTURE')

            # 判断future账户余额是否低于减仓线
            if usdt_future < close_limit:
                # 计算期货账户缺多少钱  中位数 - 期货余额 = 缺多少钱
                need = (open_limit - close_limit) / 2 - usdt_future
                # 判断当前main余额是否足够使用
                if usdt_main > need:
                    # 足够的话，直接划转需要的钱到期货
                    operator.transfer_asset('MAIN_UMFUTURE', 'USDT', need)
                else:
                    # 不够的话，只要main余额不是0，就全划过去
                    if usdt_main != 0:
                        operator.transfer_asset(
                            'MAIN_UMFUTURE', 'USDT', usdt_main)

                    # 计算划转之后还需要平仓多少钱
                    need_close = need - usdt_main
                    # 需要平仓的钱必须大于15刀才生效
                    if need_close > 15:
                        # 计算需要平仓的货币数
                        need_close = need_close / \
                            operator.get_latest_price(close_symbol, 'MAIN')
                        # 将货币数转为精度对应的str
                        need_close = binance_api.float_to_str_floor(
                            need_close, operator.get_symbol_precision(close_symbol))
                        # 如果转了之后不为0，则启动两边减仓

                        def _close_main():
                            operator.trade_market(
                                close_symbol, 'MAIN', need_close, 'SELL')

                        def _close_future():
                            operator.trade_market(
                                close_symbol, 'FUTURE', need_close, 'BUY')

                        if float(need_close) != 0:
                            handel1 = multiprocessing.Process(
                                target=_close_main)
                            handel2 = multiprocessing.Process(
                                target=_close_future)
                            handel1.start()
                            handel2.start()
                            handel1.join()
                            handel2.join()

            # 判断future账户是否高于加仓线
            if usdt_future > open_limit:
                # 计算需要加仓多少      持有货币 - 中位数 = 多出来的钱
                need_open = usdt_future - (open_limit - close_limit) / 2
                # 把要加仓的钱丢到现货
                operator.transfer_asset('UMFUTURE_MAIN', 'USDT', need_open)
                # 把加仓的钱乘以90%换算成货币数（留余，以免钱不够开仓失败）
                need_open = (need_open * 0.9) / \
                    operator.get_latest_price(close_symbol, 'MAIN')
                # 期货现货反向开仓

                def _open_main():
                    operator.trade_market(
                        close_symbol, 'MAIN', need_open, 'BUY')

                def _open_future():
                    operator.trade_market(
                        close_symbol, 'FUTURE', need_open, 'SELL')

                handel1 = multiprocessing.Process(target=_open_main)
                handel2 = multiprocessing.Process(target=_open_future)
                handel1.start()
                handel2.start()
                handel1.join()
                handel2.join()

            time.sleep(refresh_timeout)
