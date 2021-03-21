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
        self.log(random.randint(1, 100))
        self.log(random.randint(1, 100))
        self.log(random.randint(1, 100))
