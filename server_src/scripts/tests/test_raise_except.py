import multiprocessing
import traceback
import time
import tools
import random


class Script(tools.Script):
    def info(self):
        info = tools.ScriptInfo()
        info.title = '用于引发异常的测试脚本'
        info.description = '输出3个随机数之后，就会引发一个FileNotFoundError异常'
        info.inputs = []
        return info

    def main(self):
        self.log(random.randint(0, 100))
        self.log(random.randint(0, 100))
        self.log(random.randint(0, 100))
        raise FileNotFoundError
