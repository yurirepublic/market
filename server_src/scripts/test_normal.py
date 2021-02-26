import multiprocessing
import traceback
import time
import tools
import random
import binance_api
import json


class Script(tools.Script):
    def info(self):
        info = tools.ScriptInfo()
        info.title = '用于普通测试'
        info.description = '运行一下，输出几个东西就会结束'
        info.inputs = []
        return info

    def main(self):
        operator = binance_api.SmartOperator()
        operator.trade_market('BTCUSDT', 'MAIN', '10000',
                              'BUY', volume_mode=True)
