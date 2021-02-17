import tools
import binance_api
import binance_api as bi
import time
import tools
import json
import math


class Script(tools.Script):
    def future_to_base(self, amount: str):
        """
        将期货账户USDT转账到现货账户
        """
        self.operator.request('api', '/sapi/v1/asset/transfer', 'POST', {
            'type': 'MAIN_UMFUTURE',
            'asset': 'USDT',
            'amount': amount,
            'timestamp': binance_api.get_timestamp()
        })

    def base_to_future(self, amount: str):
        """
        将现货账户USDT转账到期货账户
        """
        self.operator.request('api', '/sapi/v1/asset/transfer', 'POST', {
            'type': 'UMFUTURE_MAIN',
            'asset': 'USDT',
            'amount': amount,
            'timestamp': binance_api.get_timestamp()
        })

    def main(self):
        self.operator = binance_api.Operator()
        self.operator_future = binance_api.Operatorfuture()
        operator = self.operator
        operator_future = self.operator_future

        close_symbol = 'ANKRUSDT'       # 期货账户保证金不足时用于平仓的账户
        close_limit = 200           # 低于此金额，将会减杠杆
        open_limit = 1500           # 高于此金额，将会加杠杆

        refresh_timeout = 30            # 刷新账户金额的间隔(秒)，极快刷新可能导致服务器被封禁
        """
        注：每次调仓会将仓位调到close和open的中间
        """

        # 获取期货可用USDT保证金
        while True:
            usdt_free = json.loads(operator.request('api', '/api/v3/account', 'GET', {
                'timestamp': binance_api.get_timestamp()
            }))['balances']
            usdt_free = float(
                list(filter(lambda x: x['asset'] == 'USDT', usdt_free))[0]['free'])
            usdt_future_free = json.loads(operator_future.request('fapi', '/fapi/v2/balance', 'GET', {
                'timestamp': binance_api.get_timestamp()
            }))
            usdt_future_free = float(
                list(filter(lambda x: x['asset'] == 'USDT', usdt_future_free))[0]['availableBalance'])

            # 判断future账户余额是否低于减仓线
            if usdt_future_free < close_limit:
                # 计算需要让合约账户增长多少USDT 两个阈值的中间值减去余额
                need_usdt = (open_limit - close_limit) / 2 - usdt_free
                # 判断当前余额是否足够使用
                if usdt_free > need_usdt:
                    # 足够的话，直接划转需要的钱到期货
                    self.base_to_future(
                        binance_api.float_to_str_floor(need_usdt))
                else:
                    # 不够的话，只要余额不是0，就全划过去
                    if usdt_free != 0:
                        self.base_to_future(
                            binance_api.float_to_str_floor(usdt_free))

                    # 如果需要平仓的钱低于15USDT，直接不理（交易最低为10USDT，考虑冗余留到15USDT）
                    if need_usdt - usdt_free < 15:
                        pass
                    else:
                        # 使用市价单的成交额模式下单

                        pass
                # 判断future账户余额是否高于加仓线

                # TODO 把加仓部分也写上

                # if usdt_future_free > open_limit:
                #     pass

            time.sleep(refresh_timeout)
