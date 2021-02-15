import multiprocessing
import traceback
import time
import tools
import random


class Script(tools.Script):
    def main(self):
        self.log('脚本启动')
        while True:
            self.log(random.randint(0, 100))
            time.sleep(5)
