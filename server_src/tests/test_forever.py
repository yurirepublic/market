import multiprocessing
import traceback
import time
import script_manager
import random


class Script(script_manager.Script):
    def info(self):
        info = script_manager.ScriptInfo()
        info.title = '用于运行的测试脚本'
        info.description = '如果不终止就会一直运行，5秒输出一次随机数'
        info.inputs = []
        return info

    def main(self):
        self.log('脚本启动')
        while True:
            self.log(random.randint(0, 100))
            time.sleep(5)
