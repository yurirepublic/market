import multiprocessing
import traceback
import time
import tools
import random


class Script(tools.Script):
    def info(self):
        info = tools.ScriptInfo()
        info.title = '用于运行的测试脚本'
        info.description = '如果不终止就会一直运行'
        info.inputs = []
        return info

    def main(self):
        self.log('脚本启动')
        while True:
            self.log(random.randint(0, 100))
            time.sleep(5)
